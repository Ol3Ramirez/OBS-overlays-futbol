#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["websockets>=15"]
# requires-python = ">=3.11"
# ///
"""
WebSocket Relay -- SRYiyo
Lee configuracion desde profile.json (SSOT).

Principios:
  SSOT        -- puerto, bind y token desde profile.json
  Fail-fast   -- sale inmediatamente si profile.json no existe
  Atomico     -- state_store FIFO, sin crecer indefinidamente
  Seguridad   -- token opcional; conexiones locales (127.0.0.1) auto-autenticadas
  Idempotente -- estado se replica a cada cliente al conectar
"""
import asyncio
import base64
import hashlib
import hmac
import json
import sys
import os
import uuid
from collections import OrderedDict
from datetime import datetime
from websockets.asyncio.server import broadcast, serve


def _load_profile() -> dict:
    """Carga profile.json (SSOT, commiteado) y superpone profile.local.json
    (gitignoreado) si existe -- ahi vive el wsToken real, nunca en profile.json."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    profile_path = os.path.join(base_dir, "profile.json")
    if not os.path.exists(profile_path):
        print(f"[FATAL] profile.json no encontrado en {profile_path}")
        sys.exit(1)
    try:
        with open(profile_path, encoding="utf-8") as f:
            profile = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[FATAL] profile.json invalido: {e}")
        sys.exit(1)

    local_path = os.path.join(base_dir, "profile.local.json")
    if os.path.exists(local_path):
        try:
            with open(local_path, encoding="utf-8") as f:
                profile.update(json.load(f))
        except json.JSONDecodeError as e:
            print(f"[FATAL] profile.local.json invalido: {e}")
            sys.exit(1)

    return profile


_profile  = _load_profile()
_WS_PORT  = _profile.get("wsPort",        8891)
_WS_BIND  = _profile.get("wsBindAddress", "127.0.0.1")
_NAME     = _profile.get("name",          "SRYiyo")
_TOKEN    = _profile.get("wsToken",       None)  # None = sin autenticacion

_LOCAL_ADDRS = {"127.0.0.1", "::1", "localhost"}

_NO_STORE = frozenset({
    "clear", "clearSpeaker", "clearTopic", "hideBadge",
    "stopCountdown", "hide", "resetClock",
    "setScene", "playKickoffMusic", "stopKickoffMusic",
})

_state_store: OrderedDict[str, str] = OrderedDict()
_MAX_STORE  = 100
_auth_ok: set = set()  # websockets autenticados (para control remoto)

# ── OBS WebSocket para setScene ──
_obs_ws            = None
_obs_authenticated = False

SCENE_MAP = {
    "Partido":       "SRY - Partido",
    "Intro":         "SRY - Inicio",
    "Medio Tiempo":  "SRY - Medio Tiempo",
    "Alineación":    "SRY - Alineacion",
    "Alineacion":    "SRY - Alineacion",
    "Entrevista":    "SRY - Entrevista",
    "Sin Fuente":    "SRY - Inicio",
}


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _is_local(addr) -> bool:
    """Conexiones locales (OBS Browser Sources) no necesitan token."""
    if not addr:
        return True
    host = addr[0] if isinstance(addr, (tuple, list)) else str(addr)
    return host in _LOCAL_ADDRS


def _load_obs_password() -> str:
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("OBS_WS_PASSWORD="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("OBS_WS_PASSWORD", "")


def _make_obs_auth(password: str, salt: str, challenge: str) -> str:
    secret = base64.b64encode(hashlib.sha256((password + salt).encode()).digest()).decode()
    return base64.b64encode(hashlib.sha256((secret + challenge).encode()).digest()).decode()


async def _obs_set_scene(scene_short: str) -> None:
    global _obs_ws, _obs_authenticated
    if not _obs_ws or not _obs_authenticated:
        print(f"[{_ts()}] [!] setScene: OBS WS no conectado ('{scene_short}' ignorado)")
        return
    scene_name = SCENE_MAP.get(scene_short)
    if not scene_name:
        print(f"[{_ts()}] [!] setScene: escena desconocida '{scene_short}'")
        return
    try:
        rid = str(uuid.uuid4())
        await _obs_ws.send(json.dumps({
            "op": 6,
            "d": {
                "requestType": "SetCurrentProgramScene",
                "requestId":   rid,
                "requestData": {"sceneName": scene_name},
            },
        }))
        print(f"[{_ts()}]    OBS -> SetCurrentProgramScene: {scene_name}")
    except Exception as e:
        print(f"[{_ts()}] [!] setScene error: {e}")


async def _obs_connect_loop() -> None:
    """Mantiene conexion persistente con OBS WS para setScene."""
    global _obs_ws, _obs_authenticated
    from websockets.asyncio.client import connect as ws_connect

    obs_host = _profile.get("obsHost", "localhost")
    obs_port = _profile.get("obsPort", 4455)
    password = _load_obs_password()

    while True:
        try:
            async with ws_connect(f"ws://{obs_host}:{obs_port}") as ws:
                _obs_ws            = ws
                _obs_authenticated = False

                hello = json.loads(await ws.recv())
                if hello.get("op") != 0:
                    raise ValueError(f"op inesperado: {hello.get('op')}")

                rpc_version = hello["d"]["rpcVersion"]
                auth_data   = hello["d"].get("authentication")
                identify_d  = {"rpcVersion": rpc_version, "eventSubscriptions": 0}

                if auth_data and password:
                    identify_d["authentication"] = _make_obs_auth(
                        password, auth_data["salt"], auth_data["challenge"]
                    )

                await ws.send(json.dumps({"op": 1, "d": identify_d}))
                identified = json.loads(await ws.recv())

                if identified.get("op") == 2:
                    _obs_authenticated = True
                    print(f"[{_ts()}] OBS WS conectado en {obs_host}:{obs_port}")
                else:
                    print(f"[{_ts()}] [!] OBS WS auth fallida")
                    _obs_ws = None
                    await asyncio.sleep(5)
                    continue

                # Drena mensajes entrantes (eventos OBS que no necesitamos)
                async for _ in ws:
                    pass

        except Exception as e:
            _obs_ws            = None
            _obs_authenticated = False
            print(f"[{_ts()}] OBS WS desconectado ({e.__class__.__name__}), reintentando en 5s...")
            await asyncio.sleep(5)


async def main() -> None:
    async def relay(websocket) -> None:
        addr  = websocket.remote_address
        local = _is_local(addr)

        print(f"[{_ts()}] [+] {addr}  local={local}  clientes={len(server.connections)}")

        # Replay estado actual al cliente recien conectado (idempotente)
        for msg in list(_state_store.values()):
            try:
                await websocket.send(msg)
            except Exception:
                pass

        # Conexiones locales (overlays OBS) no necesitan token
        if not _TOKEN or local:
            _auth_ok.add(websocket)
            if _TOKEN and local:
                print(f"[{_ts()}]    auto-auth local: {addr}")

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    print(f"[{_ts()}] [!] JSON invalido ignorado: {message[:80]}")
                    continue

                fn = data.get("fn", "")

                # ── Mensaje de autenticacion ──
                if "auth" in data:
                    # hmac.compare_digest evita timing attacks en la comparacion del token
                    if hmac.compare_digest(str(data.get("auth", "")), str(_TOKEN or "")):
                        _auth_ok.add(websocket)
                        await websocket.send(json.dumps({"fn": "_authOK"}))
                        print(f"[{_ts()}] [OK] {addr} autenticado")
                    else:
                        await websocket.send(json.dumps({"fn": "_authFailed"}))
                        print(f"[{_ts()}] [!] {addr} token invalido")
                    continue  # No broadcast del mensaje de auth

                # ── Verificar autorizacion ──
                if websocket not in _auth_ok:
                    print(f"[{_ts()}] [!] {addr} no autenticado — enviar {{\"auth\":\"token\"}}")
                    await websocket.send(json.dumps({"fn": "_authRequired"}))
                    continue

                # ── Guardar en state store ──
                if fn == "resetClock":
                    _state_store.pop("setMinute", None)
                    _state_store.pop("addedTime", None)
                if fn and fn not in _NO_STORE:
                    _state_store[fn] = message
                    if len(_state_store) > _MAX_STORE:
                        _state_store.popitem(last=False)

                print(f"[{_ts()}]    -> {data}")

                # ── setScene -> OBS WS directamente ──
                if fn == "setScene":
                    args = data.get("args", [])
                    if args:
                        asyncio.create_task(_obs_set_scene(args[0]))

                targets = list(server.connections)
                if targets:
                    try:
                        await asyncio.wait_for(
                            asyncio.gather(*[ws.send(message) for ws in targets], return_exceptions=True),
                            timeout=2.0
                        )
                    except asyncio.TimeoutError:
                        print(f"[{_ts()}] [!] broadcast timeout — cliente lento detectado")

        except Exception as e:
            print(f"[{_ts()}] [!] {addr} error: {e}")
        finally:
            _auth_ok.discard(websocket)
            print(f"[{_ts()}] [-] {addr} desconectado  "
                  f"clientes={max(0, len(server.connections) - 1)}")

    token_info = f"token={'SI' if _TOKEN else 'NO'}"
    async with serve(relay, _WS_BIND, _WS_PORT, ping_interval=30, ping_timeout=15) as server:
        asyncio.create_task(_obs_connect_loop())
        print(f"[{_ts()}] {_NAME} WS Relay en ws://{_WS_BIND}:{_WS_PORT}  ({token_info})")
        if _TOKEN:
            print(f"[{_ts()}] Locales auto-autenticados | Remotos necesitan {{\"auth\":\"{_TOKEN}\"}}")
        print(f"[{_ts()}] (Ctrl+C para detener)")
        await server.serve_forever()


asyncio.run(main())
