#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["websockets>=15"]
# requires-python = ">=3.11"
# ///
"""
WebSocket Relay -- SRYiyo Robles Futbol
Puerto: ws://127.0.0.1:8891  (independiente del perfil original en 8889)

Escucha en 127.0.0.1 (solo local). Si necesitas control desde otro
dispositivo en la misma red (celular, tablet), cambia a "0.0.0.0".
"""
import asyncio
import json
from collections import OrderedDict
from datetime import datetime
from websockets.asyncio.server import broadcast, serve

_NO_STORE = frozenset({
    'clear', 'clearSpeaker', 'clearTopic', 'hideBadge',
    'stopCountdown', 'hide', 'resetClock',
})

_state_store: OrderedDict[str, str] = OrderedDict()
_MAX_STORE = 100


def _ts() -> str:
    return datetime.now().strftime('%H:%M:%S')


async def main() -> None:
    async def relay(websocket) -> None:
        addr = websocket.remote_address
        print(f"[{_ts()}] [+] {addr}  clientes={len(server.connections)}")

        # Replay estado actual al cliente recién conectado
        for msg in list(_state_store.values()):
            try:
                await websocket.send(msg)
            except Exception:
                pass

        try:
            async for message in websocket:
                # Parsear y guardar en state store
                try:
                    data = json.loads(message)
                    fn = data.get('fn', '')
                    if fn and fn not in _NO_STORE:
                        _state_store[fn] = message
                        if len(_state_store) > _MAX_STORE:
                            _state_store.popitem(last=False)
                    print(f"[{_ts()}]    -> {data}")
                except json.JSONDecodeError:
                    print(f"[{_ts()}] [!] JSON invalido ignorado: {message[:80]}")
                    continue  # No broadcast de mensajes malformados
                except Exception as e:
                    print(f"[{_ts()}] [!] Error procesando mensaje: {e}")

                # Broadcast a todas las conexiones activas (copia para evitar race condition)
                broadcast(list(server.connections), message)

        except Exception as e:
            print(f"[{_ts()}] [!] {addr} error: {e}")
        finally:
            print(f"[{_ts()}] [-] {addr} desconectado  "
                  f"clientes={max(0, len(server.connections) - 1)}")

    async with serve(relay, "127.0.0.1", 8891) as server:
        print(f"[{_ts()}] SRYiyo WS Relay en ws://127.0.0.1:8891")
        print(f"[{_ts()}] (Ctrl+C para detener)")
        await server.serve_forever()


asyncio.run(main())
