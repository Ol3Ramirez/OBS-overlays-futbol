#!/usr/bin/env python3
"""
WebSocket Relay — OBS Overlays Fútbol 5
API: websockets 15.x  |  ws://0.0.0.0:8889

State store: sends last known state to every newly connected client
so overlays recover automatically after a reload or reconnect.
"""
import asyncio
import json
from datetime import datetime
from websockets.asyncio.server import broadcast, serve

# These commands undo state and should NOT be restored on reconnect
_NO_STORE = frozenset({
    'clear', 'clearSpeaker', 'clearTopic', 'hideBadge',
    'stopCountdown', 'hide', 'resetClock',
})

_state_store: dict[str, str] = {}   # fn  → last JSON message


def _ts() -> str:
    return datetime.now().strftime('%H:%M:%S')


async def main() -> None:
    async def relay(websocket) -> None:
        addr = websocket.remote_address
        print(f"[{_ts()}] [+] {addr}  clientes={len(server.connections)}")

        # Replay current state to the newly connected client
        for msg in list(_state_store.values()):
            try:
                await websocket.send(msg)
            except Exception:
                pass

        try:
            async for message in websocket:
                # Parse + store
                try:
                    data = json.loads(message)
                    fn = data.get('fn', '')
                    if fn and fn not in _NO_STORE:
                        _state_store[fn] = message
                    print(f"[{_ts()}]    → {data}")
                except Exception:
                    pass
                # Broadcast to all (including sender — overlays ignore own echo)
                broadcast(server.connections, message)

        except Exception as e:
            print(f"[{_ts()}] [!] {addr} error: {e}")
        finally:
            print(f"[{_ts()}] [-] {addr} desconectado  "
                  f"clientes={max(0, len(server.connections) - 1)}")

    async with serve(relay, "0.0.0.0", 8889) as server:
        print(f"[{_ts()}] WS Relay escuchando en ws://localhost:8889  "
              f"(Ctrl+C para detener)")
        await server.serve_forever()


asyncio.run(main())
