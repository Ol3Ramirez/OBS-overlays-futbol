#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["websockets>=15"]
# requires-python = ">=3.11"
# ///
"""
setup_obs.py -- Configura OBS para el perfil SRYiyo (Robles Futbol)
Protocolo: OBS WebSocket v5 (raw) -- compatible con OBS 28+
Uso: uv run setup_obs.py
"""
import sys, io, asyncio, json, uuid, hashlib, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from websockets.asyncio.client import connect

PASSWORD        = "xxeE65696N6ufKhc"
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
        identify_d["authentication"] = make_auth(PASSWORD, auth_data["salt"], auth_data["challenge"])

    await ws.send(json.dumps({"op": 1, "d": identify_d}))

    # Identified (op=2)
    identified = json.loads(await ws.recv())
    if identified.get("op") != 2:
        print(f"  ERROR de autenticacion (verifica la contrasena).")
        print(f"  Respuesta recibida: {identified}")
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
    rd = ver["responseData"]
    print(f"  OBS {rd.get('obsVersion','?')}  |  WS {rd.get('obsWebSocketVersion','?')}")
    print()

    # Crear / activar Scene Collection
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
            print(f"    escena ya existe (code {code})" if code == 601 else f"    aviso: {r['requestStatus']}")

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
            if code2 == 601:
                print(f"    (source ya existe) -> {url}")
            else:
                print(f"    Error {code2}: {r2['requestStatus'].get('comment','')}")

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
    print("  1. Corre: .\\iniciar_stream.ps1")
    print("  2. Abre el panel en Chrome")
    print("  3. OBS: clic derecho cada source -> Refresh")
    print("=" * 51)
    print()

asyncio.run(main())
