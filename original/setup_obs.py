#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["websockets>=15"]
# requires-python = ">=3.11"
# ///
"""
setup_obs.py -- Configura OBS para el perfil SRYiyo
Lee TODA la configuracion desde profile.json (SSOT).

Principios aplicados:
  SSOT       -- profile.json es la unica fuente de verdad (host, port, collection, scenes)
  Idempotente -- re-ejecutar no rompe estado: escenas ya existentes se detectan (code 601)
  Atomico    -- .env se escribe via tmp+rename, nunca queda corrupto a mitad
  Fail-fast  -- exit 1 inmediato en error de conexion, auth o config invalida
  Defensivo  -- verifica version OBS antes de crear recursos
"""
import sys
import io
import os
import json
import asyncio
import uuid
import hashlib
import base64
import getpass
import tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from websockets.asyncio.client import connect

# ── Cargar profile.json (SSOT) ──────────────────────────────────────────────

def _load_profile() -> dict:
    profile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile.json")
    if not os.path.exists(profile_path):
        print(f"  [FATAL] profile.json no encontrado en {profile_path}")
        sys.exit(1)
    try:
        with open(profile_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"  [FATAL] profile.json invalido: {e}")
        sys.exit(1)

_P = _load_profile()

HOST            = _P.get("obsHost",       "localhost")
PORT            = _P.get("obsPort",       4455)
HTTP            = _P.get("httpPort",      8890)
COLLECTION_NAME = _P.get("obsCollection", "SRYiyo - Robles Futbol")
PROFILE_NAME    = _P.get("name",          "SRYiyo")

# Escenas derivadas de profile.json (SSOT): scenePrefix + nombre -> overlay html.
SCENE_PREFIX = _P.get("scenePrefix", "")
SCENES = [
    (f"{SCENE_PREFIX}{name}", f"http://localhost:{HTTP}/{html}", 1920, 1080)
    for name, html in _P.get("scenes", {}).items()
]

# Escenas que se ven en vivo sobre la camara (Inicio y Medio Tiempo son
# pantallas graficas sin camara -- ver original/CONFIG_IRL_PRO.md)
SCENES_WITH_CAMERA = {"Partido", "Evento", "Alineacion", "Entrevista"}

CAMERA_NAME = "Camara SRT"
SRT_PORT    = _P.get("srtPort", 5000)
SRT_LATENCY_MS = _P.get("srtLatencyMs", 4000)
CAMERA_URL  = f"srt://0.0.0.0:{SRT_PORT}?mode=listener&latency={SRT_LATENCY_MS * 1000}"

# ── Password: env var → .env file → getpass interactivo ─────────────────────

def _env_path() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

def _load_env_file() -> str | None:
    path = _env_path()
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("OBS_WS_PASSWORD="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                return value or None
    return None

def _save_env_file_atomic(password: str) -> None:
    """Escribe .env via archivo temporal + rename — atomico, nunca queda corrupto."""
    path = _env_path()
    dir_ = os.path.dirname(path)
    fd, tmp_path = tempfile.mkstemp(dir=dir_, prefix=".env.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(f"OBS_WS_PASSWORD={password}\n")
        os.replace(tmp_path, path)  # atomico en POSIX y Windows (Python 3.3+)
        print("  OK Guardado en .env (gitignoreado, no va al repo)")
    except Exception as e:
        os.unlink(tmp_path)
        print(f"  [AVISO] No se pudo guardar .env: {e}")

def get_password() -> str:
    pwd = os.environ.get("OBS_WS_PASSWORD", "").strip()
    if pwd:
        return pwd
    pwd = _load_env_file()
    if pwd:
        return pwd
    print()
    print("  Password de OBS WebSocket no configurado.")
    print("  Opciones para evitar escribirlo cada vez:")
    print(f"    A) Crear {_env_path()} con: OBS_WS_PASSWORD=tu_password")
    print("    B) export OBS_WS_PASSWORD=tu_password  (Mac/Linux)")
    print("    C) $env:OBS_WS_PASSWORD='tu_password'  (Windows PowerShell)")
    print()
    pwd = getpass.getpass("  Password OBS WebSocket (puerto 4455): ").strip()
    if not pwd:
        print("  ERROR: password requerido.")
        sys.exit(1)
    save = input("  Guardar en .env para proximas ejecuciones? [s/N]: ").strip().lower()
    if save in ("s", "si", "y", "yes"):
        _save_env_file_atomic(pwd)
    return pwd

# ── Auth OBS WebSocket v5 ────────────────────────────────────────────────────

def make_auth(password: str, salt: str, challenge: str) -> str:
    secret = base64.b64encode(
        hashlib.sha256((password + salt).encode()).digest()
    ).decode()
    return base64.b64encode(
        hashlib.sha256((secret + challenge).encode()).digest()
    ).decode()

# ── Main ─────────────────────────────────────────────────────────────────────

async def main() -> None:
    print()
    print("=" * 51)
    print(f"  {PROFILE_NAME} -- Setup OBS")
    print(f"  {_P.get('home','?')} vs {_P.get('away','?')}")
    print(f"  {_P.get('matchLabel','')}")
    print("=" * 51)
    print()

    password = get_password()

    print(f"  Conectando a ws://{HOST}:{PORT}...")
    try:
        ws = await connect(f"ws://{HOST}:{PORT}")
    except Exception as e:
        print(f"\n  ERROR: No se pudo conectar: {e}")
        print(f"  -> OBS debe estar abierto con WebSocket en puerto {PORT}")
        sys.exit(1)

    # Handshake OBS WS v5: Hello(op=0) → Identify(op=1) → Identified(op=2)
    hello = json.loads(await ws.recv())
    if hello.get("op") != 0:
        print(f"  ERROR: Hello inesperado: {hello}")
        await ws.close()
        sys.exit(1)

    auth_data   = hello["d"].get("authentication")
    rpc_version = hello["d"]["rpcVersion"]

    identify_d: dict = {"rpcVersion": rpc_version, "eventSubscriptions": 0}
    if auth_data:
        identify_d["authentication"] = make_auth(
            password, auth_data["salt"], auth_data["challenge"]
        )

    await ws.send(json.dumps({"op": 1, "d": identify_d}))

    identified = json.loads(await ws.recv())
    if identified.get("op") != 2:
        print()
        print("  ERROR: la contrasena de OBS WebSocket NO funciono (puerto 4455).")
        print(f"  -> OBS: Herramientas -> Servidor WebSocket -> Mostrar info de conexion")
        print(f"  -> Corrige {_env_path()} (o $env:OBS_WS_PASSWORD) y reintenta.")
        await ws.close()
        sys.exit(1)

    print("  OK Conectado y autenticado")

    async def req(request_type: str, data: dict = {}) -> dict:
        rid = str(uuid.uuid4())
        await ws.send(json.dumps({
            "op": 6,
            "d": {"requestType": request_type, "requestId": rid, "requestData": data}
        }))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("op") == 7 and msg["d"].get("requestId") == rid:
                return msg["d"]

    # Version check (fail-fast si OBS es demasiado viejo)
    ver = await req("GetVersion")
    rd  = ver["responseData"]
    obs_ver = rd.get("obsVersion", "?")
    ws_ver  = rd.get("obsWebSocketVersion", "?")
    print(f"  OBS {obs_ver}  |  WS {ws_ver}")

    major = int(obs_ver.split(".")[0]) if obs_ver != "?" else 99
    if major < 28:
        print(f"  ERROR: OBS {obs_ver} no soporta WS v5. Necesitas OBS 28+.")
        await ws.close()
        sys.exit(1)
    print()

    # Perfil OBS (idempotente: crea si no existe, activa siempre)
    print(f"  Perfil OBS: '{PROFILE_NAME}'")
    pl = await req("GetProfileList")
    existentes = pl["responseData"].get("profiles", [])
    if PROFILE_NAME not in existentes:
        await req("CreateProfile", {"profileName": PROFILE_NAME})
        print("  OK Perfil creado")
        await asyncio.sleep(1.0)
    else:
        print("  (ya existe)")
    await req("SetCurrentProfile", {"profileName": PROFILE_NAME})
    # Canvas de video desde profile.json (SSOT): base/output/fps. Buenas practicas:
    # base = output (sin reescalado) a 1920x1080, 30 fps por defecto.
    _v = _P.get("video", {})
    r_vid = await req("SetVideoSettings", {
        "baseWidth":     _v.get("baseWidth",   1920),
        "baseHeight":    _v.get("baseHeight",  1080),
        "outputWidth":   _v.get("outputWidth", 1920),
        "outputHeight":  _v.get("outputHeight",1080),
        "fpsNumerator":  _v.get("fps",         30),
        "fpsDenominator": 1,
    })
    if not r_vid["requestStatus"]["result"]:
        print(f"    Aviso SetVideoSettings: {r_vid['requestStatus'].get('comment', 'error desconocido')}")
    await asyncio.sleep(0.5)
    print()

    # Scene Collection (idempotente: crea si no existe, activa si ya existe)
    print(f"  Scene Collection: '{COLLECTION_NAME}'")
    r = await req("CreateSceneCollection", {"sceneCollectionName": COLLECTION_NAME})
    if r["requestStatus"]["result"]:
        print("  OK Creada")
        await asyncio.sleep(1.2)
    else:
        print("  (ya existe) -> activando")
        await req("SetCurrentSceneCollection", {"sceneCollectionName": COLLECTION_NAME})
        await asyncio.sleep(0.5)

    # Camara SRT (idempotente): ancla "Camara SRT" detras del overlay en cada
    # escena que la necesita. No duplica si ya esta anidada en esa escena.
    async def ensure_camera_in_scene(scene_name: str) -> None:
        items = await req("GetSceneItemList", {"sceneName": scene_name})
        if not items["requestStatus"]["result"]:
            print(f"    Error leyendo items de {scene_name}: {items['requestStatus'].get('comment','')}")
            return
        nombres = {it["sourceName"] for it in items["responseData"]["sceneItems"]}
        if CAMERA_NAME in nombres:
            print(f"    (camara ya en {scene_name})")
            return

        inputs = await req("GetInputList")
        existe_global = any(i["inputName"] == CAMERA_NAME for i in inputs["responseData"]["inputs"])

        if not existe_global:
            rc = await req("CreateInput", {
                "sceneName":     scene_name,
                "inputName":     CAMERA_NAME,
                "inputKind":     "ffmpeg_source",
                "inputSettings": {
                    "is_local_file":       False,
                    "input":               CAMERA_URL,
                    "hw_decode":           True,
                    "reconnect_delay_sec": 2,
                    "buffering_mb":        2,
                },
                "sceneItemEnabled": True,
            })
            if not rc["requestStatus"]["result"]:
                print(f"    Error creando camara: {rc['requestStatus'].get('comment','')}")
                return
            print(f"    OK camara creada en {scene_name} -> {CAMERA_URL}")
        else:
            rc = await req("CreateSceneItem", {"sceneName": scene_name, "sourceName": CAMERA_NAME})
            if not rc["requestStatus"]["result"]:
                print(f"    Error anidando camara en {scene_name}: {rc['requestStatus'].get('comment','')}")
                return
            print(f"    OK camara anidada en {scene_name}")

        id_resp = await req("GetSceneItemId", {"sceneName": scene_name, "sourceName": CAMERA_NAME})
        item_id = id_resp["responseData"]["sceneItemId"]
        await req("SetSceneItemTransform", {
            "sceneName":     scene_name,
            "sceneItemId":   item_id,
            "sceneItemTransform": {
                "boundsType":      "OBS_BOUNDS_STRETCH",
                "boundsWidth":     1920,
                "boundsHeight":    1080,
                "boundsAlignment": 0,
            },
        })

    # Escenas + Browser Sources (idempotente: code 601 = ya existe, continua)
    print()
    for scene_name, url, w, h in SCENES:
        print(f"  [{scene_name}]")

        r = await req("CreateScene", {"sceneName": scene_name})
        if not r["requestStatus"]["result"]:
            code = r["requestStatus"].get("code")
            if code != 601:
                print(f"    aviso CreateScene: code {code}")

        if scene_name in SCENES_WITH_CAMERA:
            await ensure_camera_in_scene(scene_name)
            await asyncio.sleep(0.2)

        src = f"Browser-{scene_name}"
        r2  = await req("CreateInput", {
            "sceneName":     scene_name,
            "inputName":     src,
            "inputKind":     "browser_source",
            "inputSettings": {
                "url":  url, "width": w, "height": h, "fps": 30,
                "reroute_audio": False, "restart_when_active": False,
                "css":  "body{background:transparent;margin:0;overflow:hidden;}"
            },
            "sceneItemEnabled": True,
        })
        ok    = r2["requestStatus"]["result"]
        code2 = r2["requestStatus"].get("code")
        if ok:
            print(f"    OK creado -> {url}")
        elif code2 == 601:
            await req("SetInputSettings", {
                "inputName":     src,
                "inputSettings": {"url": url},
                "overlay":       True,
            })
            r_ref = await req("PressInputPropertiesButton", {
                "inputName":    src,
                "propertyName": "refreshnocache",
            })
            if r_ref["requestStatus"]["result"]:
                print(f"    OK refrescado -> {url}")
            else:
                print(f"    OK actualizado -> {url}")
        else:
            print(f"    Error {code2}: {r2['requestStatus'].get('comment','')}")

        await asyncio.sleep(0.35)

    # Eliminar escena vacía que OBS crea por defecto en colecciones nuevas
    default_scenes = ["Escena", "Scene"]
    for ds in default_scenes:
        rd = await req("RemoveScene", {"sceneName": ds})
        if rd["requestStatus"]["result"]:
            print(f"  OK Escena por defecto '{ds}' eliminada")

    # Activar escena inicial
    print()
    r = await req("SetCurrentProgramScene", {"sceneName": f"{SCENE_PREFIX}Inicio"})
    print("  OK Escena inicial activada" if r["requestStatus"]["result"]
          else f"  Aviso SetCurrentProgramScene: {r['requestStatus']}")

    await ws.close()

    print()
    print("=" * 51)
    print(f"  OK OBS configurado para {PROFILE_NAME}!")
    print()
    print(f"  Panel: http://localhost:{HTTP}/control_remoto.html")
    print()
    print("  Proximos pasos:")
    print("  1. Corre: .\\iniciar_stream.ps1  (Windows)")
    print("         o: bash iniciar_stream.sh  (Mac)")
    print("  2. Abre el panel en Chrome")
    print("  3. OBS: clic derecho cada source -> Refresh")
    print("=" * 51)
    print()


asyncio.run(main())
