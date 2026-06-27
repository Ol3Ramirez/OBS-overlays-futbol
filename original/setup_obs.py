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

# Logica de ajustes OBS compartida entre perfiles (video canvas + salida/grabacion/audio).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shared"))
import obs_settings  # noqa: E402  (import tras ajustar sys.path)

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
# Perfil de OBS real (puede ser compartido entre varias carpetas, ej. la
# misma resolucion 1920x1080 -- ver shared/obs_settings.py). Si no se declara
# explicitamente, cae al nombre del perfil de repo (comportamiento previo).
OBS_PROFILE     = _P.get("obsProfile",    PROFILE_NAME)

# Escenas derivadas de profile.json (SSOT): scenePrefix + nombre -> overlay html.
# El tamano de cada Browser Source sigue el canvas del perfil (1080x1920 en
# tiktok-vertical, no 1920x1080 fijo) -- evita overlays mal proporcionados.
SCENE_PREFIX = _P.get("scenePrefix", "")
_VIDEO       = _P.get("video", {})
_SCENE_W     = _VIDEO.get("outputWidth", 1920)
_SCENE_H     = _VIDEO.get("outputHeight", 1080)
SCENES = [
    (f"{SCENE_PREFIX}{name}", f"http://localhost:{HTTP}/{html}", _SCENE_W, _SCENE_H)
    for name, html in _P.get("scenes", {}).items()
]

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

    # Perfil OBS (idempotente: crea si no existe, activa siempre). Puede ser
    # compartido entre carpetas (obsProfile en profile.json) -- no siempre es
    # el mismo nombre que el perfil de repo.
    print(f"  Perfil OBS: '{OBS_PROFILE}'" + (f"  (compartido, repo={PROFILE_NAME})" if OBS_PROFILE != PROFILE_NAME else ""))
    pl = await req("GetProfileList")
    existentes = pl["responseData"].get("profiles", [])
    if OBS_PROFILE not in existentes:
        await req("CreateProfile", {"profileName": OBS_PROFILE})
        print("  OK Perfil creado")
        await asyncio.sleep(1.0)
    else:
        print("  (ya existe)")
    await req("SetCurrentProfile", {"profileName": OBS_PROFILE})
    # Canvas de video + ajustes generales (salida/grabacion/audio) desde profile.json.
    # Logica compartida (shared/obs_settings.py): misma config en todos los perfiles,
    # cross-platform (encoder/ruta por SO) e idempotente.
    await obs_settings.apply_video_and_output(req, _P)
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

    # Escenas + Browser Sources (idempotente: code 601 = ya existe, continua)
    print()
    for scene_name, url, w, h in SCENES:
        print(f"  [{scene_name}]")

        r = await req("CreateScene", {"sceneName": scene_name})
        if not r["requestStatus"]["result"]:
            code = r["requestStatus"].get("code")
            if code != 601:
                print(f"    aviso CreateScene: code {code}")

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

    # Camara SRT en las escenas que la necesitan (logica compartida -- ver shared/obs_settings.py)
    print()
    await obs_settings.ensure_camera_in_scenes(req, _P, SCENE_PREFIX)

    # ── Fuente de video Replay (ffmpeg_source, idempotente) ────────────────────
    REPLAY_SCENE = f"{SCENE_PREFIX}Replay"
    REPLAY_INPUT = _P.get("replayInputName", "Replay-Video")
    if _P.get("features", {}).get("ENABLE_REPLAY"):
        print(f"\n  [Replay-Video] -> {REPLAY_SCENE}")
        r_rp = await req("CreateInput", {
            "sceneName":     REPLAY_SCENE,
            "inputName":     REPLAY_INPUT,
            "inputKind":     "ffmpeg_source",
            "inputSettings": {
                "local_file":          "",
                "is_local_file":       True,
                "looping":             False,
                "restart_on_activate": False,
            },
            "sceneItemEnabled": True,
        })
        ok_rp   = r_rp["requestStatus"]["result"]
        code_rp = r_rp["requestStatus"].get("code")
        if ok_rp:
            print(f"    OK creado (esperando primera jugada)")
        elif code_rp == 601:
            print(f"    OK (ya existe)")
        else:
            print(f"    Error {code_rp}: {r_rp['requestStatus'].get('comment','')}")
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
