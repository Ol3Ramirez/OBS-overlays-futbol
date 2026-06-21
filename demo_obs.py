#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["websockets>=15"]
# requires-python = ">=3.11"
# ///
"""
demo_obs.py -- Recorre escenas de AMBOS perfiles con funciones tipo demo.
Controla OBS via WebSocket (4455) y los relays (8889 / 8891).

Uso:
    uv run demo_obs.py             # demo completo (original -> SRYiyo)
    uv run demo_obs.py original    # solo perfil original
    uv run demo_obs.py sryi        # solo perfil SRYiyo
"""
import sys, io, os, json, asyncio, uuid, hashlib, base64

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
from websockets.asyncio.client import connect

# ── Config ────────────────────────────────────────────────────────────────────
OBS_URL = "ws://localhost:4455"
ROOT    = os.path.dirname(os.path.abspath(__file__))

SCENE_ORDER_ORIGINAL = ["Inicio", "Partido", "Evento", "Alineacion", "Medio Tiempo", "Entrevista"]
SCENE_ORDER_SRYIYO   = ["SRY - Inicio", "SRY - Partido", "SRY - Evento", "SRY - Alineacion", "SRY - Medio Tiempo", "SRY - Entrevista"]

PROFILES = {
    "original": {
        "label":      "original -- Avila Fisioterapia",
        "collection": "original - Avila Fisioterapia",
        "relay":      "ws://localhost:8889",
        "env":        os.path.join(ROOT, "original", ".env"),
        "scenes":     SCENE_ORDER_ORIGINAL,
    },
    "sryiyo": {
        "label":      "SRYiyo -- Robles Futbol",
        "collection": "SRYiyo - Robles Futbol",
        "relay":      "ws://localhost:8891",
        "env":        os.path.join(ROOT, "SRYiyo", ".env"),
        "scenes":     SCENE_ORDER_SRYIYO,
    },
}

AUTO_MODE         = "--auto" in sys.argv
INTER_SCENE_DELAY = 5   # segundos entre escenas en modo --auto

# ── Auth helpers ──────────────────────────────────────────────────────────────
def _read_env(path: str) -> str | None:
    if not os.path.exists(path):
        return None
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("OBS_WS_PASSWORD="):
            v = line.split("=", 1)[1].strip().strip('"').strip("'")
            return v or None
    return None

def _make_auth(password: str, salt: str, challenge: str) -> str:
    secret = base64.b64encode(hashlib.sha256((password + salt).encode()).digest()).decode()
    return base64.b64encode(hashlib.sha256((secret + challenge).encode()).digest()).decode()

def get_password() -> str:
    pwd = os.environ.get("OBS_WS_PASSWORD", "").strip()
    if pwd:
        return pwd
    for key in ("original", "sryiyo"):
        pwd = _read_env(PROFILES[key]["env"])
        if pwd:
            return pwd
    import getpass
    return getpass.getpass("Password OBS WebSocket (4455): ").strip()

# ── OBS WS v5 ─────────────────────────────────────────────────────────────────
async def obs_connect(password: str):
    ws = await connect(OBS_URL)
    hello = json.loads(await ws.recv())
    auth  = hello["d"].get("authentication")
    rpc   = hello["d"]["rpcVersion"]
    ident: dict = {"rpcVersion": rpc, "eventSubscriptions": 0}
    if auth:
        ident["authentication"] = _make_auth(password, auth["salt"], auth["challenge"])
    await ws.send(json.dumps({"op": 1, "d": ident}))
    resp = json.loads(await ws.recv())
    if resp.get("op") != 2:
        print("  ERROR: password OBS incorrecto")
        sys.exit(1)
    return ws

async def obs_req(ws, rtype: str, data: dict = {}) -> dict:
    rid = str(uuid.uuid4())
    await ws.send(json.dumps({"op": 6, "d": {"requestType": rtype, "requestId": rid, "requestData": data}}))
    while True:
        msg = json.loads(await ws.recv())
        if msg.get("op") == 7 and msg["d"].get("requestId") == rid:
            return msg["d"]

# ── Relay helpers ─────────────────────────────────────────────────────────────
async def cmd(relay_ws, fn: str, *args):
    await relay_ws.send(json.dumps({"fn": fn, "args": list(args)}))

async def wait(secs: float, note: str = ""):
    if note:
        print(f"       {note}")
    await asyncio.sleep(secs)

async def enter(prompt: str = ""):
    if AUTO_MODE:
        print(f"  (auto: esperando {INTER_SCENE_DELAY}s...)")
        await asyncio.sleep(INTER_SCENE_DELAY)
    else:
        msg = prompt or "  [ENTER] siguiente escena..."
        input(f"\n  {msg}\n")

# ── Demos por escena ──────────────────────────────────────────────────────────
async def demo_inicio(obs, relay, scene_name):
    await obs_req(obs, "SetCurrentProgramScene", {"sceneName": scene_name})
    await wait(1.5, "intro.html -> pantalla de countdown")

async def demo_partido(obs, relay, scene_name):
    await obs_req(obs, "SetCurrentProgramScene", {"sceneName": scene_name})
    await wait(0.8)
    print("       setTeams LOCAL / VISITANTE")
    await cmd(relay, "setTeams", "LOCAL", "VISITANTE")
    await wait(1.5)
    print("       toggleClock -> reloj arranca")
    await cmd(relay, "toggleClock")
    await wait(3, "reloj corriendo (3s)...")
    print("       goalHome Ramirez -> banner GOL")
    await cmd(relay, "goalHome", "Ramirez")
    await wait(5, "banner GOL local (5s)...")
    print("       goalAway Martinez -> banner GOL")
    await cmd(relay, "goalAway", "Martinez")
    await wait(5, "banner GOL visitante (5s)...")
    print("       toggleClock -> pausa")
    await cmd(relay, "toggleClock")
    await wait(0.8)

async def demo_evento(obs, relay, scene_name):
    await obs_req(obs, "SetCurrentProgramScene", {"sceneName": scene_name})
    await wait(0.8)
    print("       goal Ramirez 23' 1-0")
    await cmd(relay, "goal", "Ramirez", "LOCAL", 23, "1-0")
    await wait(4, "overlay GOL full-screen...")
    await cmd(relay, "clear")
    await wait(1.5)
    print("       tarjeta amarilla Lopez 31'")
    await cmd(relay, "yellow", "Lopez", "VISITANTE", 31)
    await wait(4, "tarjeta amarilla...")
    await cmd(relay, "clear")
    await wait(1.5)
    print("       tarjeta roja Gonzalez 44'")
    await cmd(relay, "red", "Gonzalez", "LOCAL", 44)
    await wait(4, "tarjeta roja...")
    await cmd(relay, "clear")
    await wait(1.5)
    print("       cambio Torres -> Mendez 52'")
    await cmd(relay, "sub", "Torres", "Mendez", "LOCAL", 52)
    await wait(4, "cambio overlay...")
    await cmd(relay, "clear")
    await wait(0.8)

async def demo_alineacion(obs, relay, scene_name):
    await obs_req(obs, "SetCurrentProgramScene", {"sceneName": scene_name})
    await wait(0.8)
    print("       setTeam 4-3-3 con 11 jugadores")
    await cmd(relay, "setTeam", {
        "name":      "LOCAL",
        "formation": "4-3-3",
        "coach":     "Prof. Rodriguez",
        "players": [
            {"num": 1,  "name": "Portero",   "pos": "GK", "x": 50, "y": 90},
            {"num": 2,  "name": "Def Der",   "pos": "RB", "x": 80, "y": 72},
            {"num": 5,  "name": "Def Cen",   "pos": "CB", "x": 62, "y": 72},
            {"num": 4,  "name": "Def Cen",   "pos": "CB", "x": 38, "y": 72},
            {"num": 3,  "name": "Def Izq",   "pos": "LB", "x": 20, "y": 72},
            {"num": 8,  "name": "Med Der",   "pos": "CM", "x": 72, "y": 52},
            {"num": 6,  "name": "Med Cen",   "pos": "CM", "x": 50, "y": 52},
            {"num": 10, "name": "Med Izq",   "pos": "CM", "x": 28, "y": 52},
            {"num": 11, "name": "Del Der",   "pos": "RW", "x": 78, "y": 28},
            {"num": 9,  "name": "Delantero", "pos": "ST", "x": 50, "y": 22},
            {"num": 7,  "name": "Del Izq",   "pos": "LW", "x": 22, "y": 28},
        ],
    })
    await wait(4, "formacion 4-3-3 visible en OBS...")

async def demo_medio_tiempo(obs, relay, scene_name):
    await obs_req(obs, "SetCurrentProgramScene", {"sceneName": scene_name})
    await wait(3, "pantalla medio tiempo activa...")

async def demo_entrevista(obs, relay, scene_name):
    await obs_req(obs, "SetCurrentProgramScene", {"sceneName": scene_name})
    await wait(1.5, "browser source cargando...")
    print("       limpiando estado previo del relay")
    await cmd(relay, "clearSpeaker")
    await cmd(relay, "clearTopic")
    await wait(0.4)
    print("       modo standalone -> fondo oscuro")
    await cmd(relay, "setMode", "standalone")
    await wait(0.6)
    print("       badge ENTREVISTA EN VIVO")
    await cmd(relay, "showBadge", "ENTREVISTA EN VIVO")
    await wait(0.8)
    print("       social CTA")
    await cmd(relay, "setSocial", "Avila Fisioterapia")
    await wait(0.5)
    print("       lower-third speaker")
    await cmd(relay, "setSpeaker", "Juan Perez", "Director Tecnico", "left")
    await wait(4, "lower-third animado (600ms) + visible...")
    print("       setTopic -> ticker scrolling")
    await cmd(relay, "setTopic", "Avila Fisioterapia | Especialistas en recuperacion deportiva")
    await wait(4, "ticker en pantalla...")
    await cmd(relay, "clearSpeaker")
    await cmd(relay, "clearTopic")
    await cmd(relay, "hideBadge")
    await wait(0.8)

def _demo_key(scene_name: str) -> str:
    """Normaliza el nombre de escena a clave del demo (quita prefix 'SRY - ')."""
    return scene_name.replace("SRY - ", "").lower()

DEMOS = {
    "inicio":       demo_inicio,
    "partido":      demo_partido,
    "evento":       demo_evento,
    "alineacion":   demo_alineacion,
    "medio tiempo": demo_medio_tiempo,
    "entrevista":   demo_entrevista,
}

# ── Demo de un perfil completo ────────────────────────────────────────────────
async def run_profile_demo(obs, profile_key: str):
    p = PROFILES[profile_key]
    print(f"\n{'=' * 54}")
    print(f"  PERFIL: {p['label']}")
    print(f"  Relay:  {p['relay']}")
    print(f"{'=' * 54}\n")

    # Cambiar Scene Collection en OBS
    print(f"  Cambiando a Scene Collection '{p['collection']}'...")
    r = await obs_req(obs, "SetCurrentSceneCollection", {"sceneCollectionName": p["collection"]})
    if not r["requestStatus"]["result"]:
        print(f"  ERROR: coleccion '{p['collection']}' no encontrada en OBS")
        return
    await asyncio.sleep(1.5)  # OBS necesita un momento para cargar la coleccion
    print("  OK\n")

    # Conectar al relay de este perfil
    try:
        relay = await connect(p["relay"])
    except Exception as e:
        print(f"  ERROR relay {p['relay']}: {e}")
        print("  -> Asegurate de correr: .\\demo.ps1  antes de este script")
        return

    for scene_name in p["scenes"]:
        print(f"  [{scene_name}]")
        fn = DEMOS.get(_demo_key(scene_name))
        if fn:
            await fn(obs, relay, scene_name)
        print(f"  OK")
        await enter("[ENTER] siguiente escena ->")

    # Dejar OBS en Inicio al terminar
    await obs_req(obs, "SetCurrentProgramScene", {"sceneName": p["scenes"][0]})
    await relay.close()
    print(f"  Perfil '{p['label']}' completado. OBS en SRY - Inicio.\n")

# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    positional = [a for a in sys.argv[1:] if not a.startswith("--")]
    arg = positional[0].lower() if positional else "ambos"

    if arg in ("original", "ori"):
        perfil_keys = ["original"]
    elif arg in ("sryi", "sryiyo", "sry"):
        perfil_keys = ["sryiyo"]
    else:
        perfil_keys = ["original", "sryiyo"]

    print()
    print("=" * 54)
    print("  DEMO OBS -- Recorrido de escenas y overlays")
    print(f"  Perfiles: {', '.join(perfil_keys)}")
    print("=" * 54)
    print()
    print("  Conectando a OBS WebSocket (4455)...")

    password = get_password()
    try:
        obs = await obs_connect(password)
    except Exception as e:
        print(f"  ERROR: {e}")
        print("  -> OBS debe estar abierto con WebSocket activo")
        sys.exit(1)
    print("  OK OBS conectado\n")

    for key in perfil_keys:
        await run_profile_demo(obs, key)
        if len(perfil_keys) > 1 and key != perfil_keys[-1]:
            await enter("[ENTER] continuar con siguiente perfil ->")

    await obs.close()

    print("=" * 54)
    print("  DEMO COMPLETO")
    print("=" * 54)
    print()

asyncio.run(main())
