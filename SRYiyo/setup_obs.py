#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["websockets>=15"]
# requires-python = ">=3.11"
# ///
"""
setup_obs.py -- Configura OBS para el perfil SRYiyo (Robles Futbol)
Protocolo: OBS WebSocket v5 (raw) -- compatible con OBS 28+
Uso: uv run setup_obs.py

PASSWORD: lee en orden — variable de entorno OBS_WS_PASSWORD
          → archivo .env en la misma carpeta
          → prompt interactivo (ofrece guardar en .env)
"""
import sys, io, os, asyncio, json, uuid, hashlib, base64, getpass
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from websockets.asyncio.client import connect

HOST            = "localhost"
PORT            = 4455
HTTP            = 8890
COLLECTION_NAME = "SRYiyo - Robles Futbol"

SCENES = [
    ("SRY - Inicio",       f"http://localhost:{HTTP}/intro.html",         1920, 1080),
    ("SRY - Partido",      f"http://localhost:{HTTP}/marcador.html",       1920, 1080),
    ("SRY - Evento",       f"http://localhost:{HTTP}/evento_jugador.html", 1920, 1080),
    ("SRY - Alineacion",   f"http://localhost:{HTTP}/alineacion.html",     1920, 1080),
    ("SRY - Medio Tiempo", f"http://localhost:{HTTP}/medio_tiempo.html",   1920, 1080),
    ("SRY - Entrevista",   f"http://localhost:{HTTP}/entrevista.html",     1920, 1080),
]

# ── Obtener password (env var → .env file → prompt interactivo) ──

def _load_env_file():
    """Lee OBS_WS_PASSWORD de un archivo .env en la misma carpeta que este script."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return None
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("OBS_WS_PASSWORD="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                return value or None
    return None

def _save_env_file(password):
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f"OBS_WS_PASSWORD={password}\n")
    print("  OK Guardado en .env (no se sube a GitHub)")

def get_password():
    # 1. Variable de entorno
    pwd = os.environ.get("OBS_WS_PASSWORD", "").strip()
    if pwd:
        return pwd

    # 2. Archivo .env local
    pwd = _load_env_file()
    if pwd:
        return pwd

    # 3. Prompt interactivo
    print()
    print("  Password de OBS WebSocket no configurado.")
    print("  Alternativas para no tener que escribirlo cada vez:")
    print("    A) Crea SRYiyo/.env con: OBS_WS_PASSWORD=tu_password")
    print("    B) Exporta la variable: export OBS_WS_PASSWORD=tu_password")
    print()
    pwd = getpass.getpass("  Ingresa el password de OBS WebSocket (4455): ").strip()
    if not pwd:
        print("  ERROR: password requerido.")
        sys.exit(1)

    save = input("  Guardar en .env para no pedirlo la proxima vez? [s/N]: ").strip().lower()
    if save in ("s", "si", "y", "yes"):
        _save_env_file(pwd)

    return pwd

# ── Auth OBS WebSocket v5 ──

def make_auth(password, salt, challenge):
    secret = base64.b64encode(hashlib.sha256((password + salt).encode()).digest()).decode()
    return base64.b64encode(hashlib.sha256((secret + challenge).encode()).digest()).decode()

async def main():
    print()
    print("=" * 51)
    print("  SRYiyo -- Setup OBS  |  Robles Futbol")
    print("  PROVEEDORA ROBLES vs HERMANOS OSORIO")
    print("=" * 51)
    print()

    password = get_password()

    print(f"  Conectando a ws://{HOST}:{PORT}...")
    try:
        ws = await connect(f"ws://{HOST}:{PORT}")
    except Exception as e:
        print(f"\n  ERROR: No se pudo conectar: {e}")
        print("  -> OBS debe estar abierto con WebSocket habilitado en puerto 4455")
        sys.exit(1)

    # Hello (op=0)
    hello = json.loads(await ws.recv())
    if hello.get("op") != 0:
        print(f"  ERROR: Respuesta inesperada: {hello}")
        sys.exit(1)

    auth_data   = hello["d"].get("authentication")
    rpc_version = hello["d"]["rpcVersion"]

    # Identify (op=1)
    identify_d = {"rpcVersion": rpc_version, "eventSubscriptions": 0}
    if auth_data:
        identify_d["authentication"] = make_auth(password, auth_data["salt"], auth_data["challenge"])

    await ws.send(json.dumps({"op": 1, "d": identify_d}))

    # Identified (op=2)
    identified = json.loads(await ws.recv())
    if identified.get("op") != 2:
        print(f"  ERROR de autenticacion.")
        print(f"  Verifica el password en OBS -> Herramientas -> WebSocket.")
        await ws.close()
        sys.exit(1)

    print("  OK Conectado y autenticado")

    async def req(request_type, data={}):
        rid = str(uuid.uuid4())
        await ws.send(json.dumps({"op": 6, "d": {
            "requestType": request_type,
            "requestId": rid,
            "requestData": data
        }}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("op") == 7 and msg["d"].get("requestId") == rid:
                return msg["d"]

    # Version
    ver = await req("GetVersion")
    rd  = ver["responseData"]
    print(f"  OBS {rd.get('obsVersion','?')}  |  WS {rd.get('obsWebSocketVersion','?')}")
    print()

    # Scene Collection
    print(f"  Scene Collection: '{COLLECTION_NAME}'")
    r = await req("CreateSceneCollection", {"sceneCollectionName": COLLECTION_NAME})
    if r["requestStatus"]["result"]:
        print("  OK Creada")
        await asyncio.sleep(1.2)
    else:
        print("  (ya existe) -> activando")
        await req("SetCurrentSceneCollection", {"sceneCollectionName": COLLECTION_NAME})
        await asyncio.sleep(0.5)

    # Escenas + Browser Sources
    print()
    for scene_name, url, w, h in SCENES:
        print(f"  [{scene_name}]")

        r = await req("CreateScene", {"sceneName": scene_name})
        if not r["requestStatus"]["result"]:
            code = r["requestStatus"].get("code")
            print(f"    (ya existe)" if code == 601 else f"    aviso: code {code}")

        src = f"Browser-{scene_name.replace('SRY - ', '')}"
        r2  = await req("CreateInput", {
            "sceneName":    scene_name,
            "inputName":    src,
            "inputKind":    "browser_source",
            "inputSettings": {
                "url": url, "width": w, "height": h, "fps": 30,
                "reroute_audio": False, "restart_when_active": False,
                "css": "body{background:transparent;margin:0;overflow:hidden;}"
            },
            "sceneItemEnabled": True
        })
        if r2["requestStatus"]["result"]:
            print(f"    OK -> {url}")
        else:
            code2 = r2["requestStatus"].get("code")
            print(f"    (ya existe)" if code2 == 601 else
                  f"    Error {code2}: {r2['requestStatus'].get('comment','')}")

        await asyncio.sleep(0.35)

    # Escena inicial
    print()
    r = await req("SetCurrentProgramScene", {"sceneName": "SRY - Inicio"})
    print("  OK Escena inicial activada" if r["requestStatus"]["result"] else
          f"  Aviso: {r['requestStatus']}")

    await ws.close()

    print()
    print("=" * 51)
    print("  OK OBS configurado para SRYiyo!")
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
