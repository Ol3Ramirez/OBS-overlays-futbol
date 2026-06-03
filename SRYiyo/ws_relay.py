#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["websockets>=15"]
# requires-python = ">=3.11"
# ///
"""
WebSocket Relay — SRYiyo Robles Fútbol
Puerto: ws://0.0.0.0:8891  (independiente del perfil original en 8889)
"""
import asyncio
import json
from datetime import datetime
from websockets.asyncio.server import broadcast, serve

_NO_STORE = frozenset({
    'clear', 'clearSpeaker', 'clearTopic', 'hideBadge',
    'stopCountdown', 'hide', 'resetClock',
})

_state_store: dict[str, str] = {}


def _ts() -> str:
    return datetime.now().strftime('%H:%M:%S')


async def main() -> None:
    async def relay(websocket) -> None:
        addr = websocket.remote_address
        print(f"[{_ts()}] [+] {addr}  clientes={len(server.connections)}")

        for msg in list(_state_store.values()):
            try:
                await websocket.send(msg)
            except Exception:
                pass

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    fn = data.get('fn', '')
                    if fn and fn not in _NO_STORE:
                        _state_store[fn] = message
                    print(f"[{_ts()}]    → {data}")
                except Exception:
                    pass
                broadcast(server.connections, message)

        except Exception as e:
            print(f"[{_ts()}] [!] {addr} error: {e}")
        finally:
            print(f"[{_ts()}] [-] {addr} desconectado  "
                  f"clientes={max(0, len(server.connections) - 1)}")

    async with serve(relay, "0.0.0.0", 8891) as server:
        print(f"[{_ts()}] SRYiyo WS Relay escuchando en ws://localhost:8891")
        print(f"[{_ts()}] (Ctrl+C para detener)")
        await server.serve_forever()


asyncio.run(main())
