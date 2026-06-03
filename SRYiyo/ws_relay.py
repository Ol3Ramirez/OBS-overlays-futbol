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
import json
import sys
import os
from collections import OrderedDict
from datetime import datetime
from websockets.asyncio.server import broadcast, serve


def _load_profile() -> dict:
    profile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile.json")
    if not os.path.exists(profile_path):
        print(f"[FATAL] profile.json no encontrado en {profile_path}")
        sys.exit(1)
    try:
        with open(profile_path, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"[FATAL] profile.json invalido: {e}")
        sys.exit(1)


_profile  = _load_profile()
_WS_PORT  = _profile.get("wsPort",        8891)
_WS_BIND  = _profile.get("wsBindAddress", "127.0.0.1")
_NAME     = _profile.get("name",          "SRYiyo")
_TOKEN    = _profile.get("wsToken",       None)  # None = sin autenticacion

_LOCAL_ADDRS = {"127.0.0.1", "::1", "localhost"}

_NO_STORE = frozenset({
    "clear", "clearSpeaker", "clearTopic", "hideBadge",
    "stopCountdown", "hide", "resetClock",
})

_state_store: OrderedDict[str, str] = OrderedDict()
_MAX_STORE  = 100
_auth_ok: set = set()  # websockets autenticados (para control remoto)


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _is_local(addr) -> bool:
    """Conexiones locales (OBS Browser Sources) no necesitan token."""
    if not addr:
        return True
    host = addr[0] if isinstance(addr, (tuple, list)) else str(addr)
    return host in _LOCAL_ADDRS


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
                    if data["auth"] == _TOKEN:
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
                if fn and fn not in _NO_STORE:
                    _state_store[fn] = message
                    if len(_state_store) > _MAX_STORE:
                        _state_store.popitem(last=False)

                print(f"[{_ts()}]    -> {data}")

                # Broadcast a todas las conexiones activas
                broadcast(list(server.connections), message)

        except Exception as e:
            print(f"[{_ts()}] [!] {addr} error: {e}")
        finally:
            _auth_ok.discard(websocket)
            print(f"[{_ts()}] [-] {addr} desconectado  "
                  f"clientes={max(0, len(server.connections) - 1)}")

    token_info = f"token={'SI' if _TOKEN else 'NO'}"
    async with serve(relay, _WS_BIND, _WS_PORT) as server:
        print(f"[{_ts()}] {_NAME} WS Relay en ws://{_WS_BIND}:{_WS_PORT}  ({token_info})")
        if _TOKEN:
            print(f"[{_ts()}] Locales auto-autenticados | Remotos necesitan {{\"auth\":\"{_TOKEN}\"}}")
        print(f"[{_ts()}] (Ctrl+C para detener)")
        await server.serve_forever()


asyncio.run(main())
