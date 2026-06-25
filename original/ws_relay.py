#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["websockets>=15"]
# requires-python = ">=3.11"
# ///
"""
WebSocket Relay -- SRYiyo
Lee configuracion desde profile.json (SSOT).

Principios:
  SSOT       -- puerto y bind address desde profile.json
  Fail-fast  -- sale inmediatamente si profile.json no existe o tiene error
  Atomicity  -- _state_store con limite FIFO, no crece indefinidamente
  DRY        -- logica de relay en una sola funcion
"""
import asyncio
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime

from websockets.asyncio.server import serve


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


_profile = _load_profile()
_WS_PORT  = _profile.get("wsPort",        8891)
_WS_BIND  = _profile.get("wsBindAddress", "127.0.0.1")
_NAME     = _profile.get("name",          "SRYiyo")

_NO_STORE = frozenset({
    "clear", "clearSpeaker", "clearTopic", "hideBadge",
    "stopCountdown", "hide", "resetClock",
})

_state_store: OrderedDict[str, str] = OrderedDict()
_MAX_STORE = 100


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


async def main() -> None:
    # Cola de salida por conexion + un "writer" dedicado que la drena en orden.
    # Tanto el replay de estado como el broadcast en vivo SOLO encolan mensajes
    # aqui (nunca escriben el socket directo) -- el writer los envia siempre en
    # el orden en que se encolaron (FIFO). Esto evita dos bugs a la vez:
    #   1. Si el replay (escalonado, con sleeps) escribiera el socket el mismo
    #      directamente, un comando en vivo recibido a mitad del replay podria
    #      "adelantarse" y luego ser pisado por un mensaje viejo del replay.
    #   2. El read-loop de la conexion (que responde los pings/keepalive) nunca
    #      espera a que un send termine -- jamas se bloquea.
    _outboxes: dict = {}

    def _broadcast(message: str) -> None:
        for outbox in list(_outboxes.values()):
            outbox.put_nowait(message)

    async def _writer(websocket, outbox: asyncio.Queue) -> None:
        try:
            while True:
                await websocket.send(await outbox.get())
        except Exception:
            pass  # conexion cerrada -- el finally de relay() limpia

    async def _enqueue_replay(outbox: asyncio.Queue) -> None:
        """Encola el estado guardado, escalonado (evita parpadeo CSS). Encolar
        -- no enviar directo -- preserva el orden FIFO frente a comandos en
        vivo que lleguen mientras el replay todavia se esta armando."""
        for msg in list(_state_store.values()):
            await outbox.put(msg)
            await asyncio.sleep(0.25)

    async def relay(websocket) -> None:
        addr = websocket.remote_address
        print(f"[{_ts()}] [+] {addr}  clientes={len(server.connections)}")

        outbox: asyncio.Queue = asyncio.Queue()
        _outboxes[websocket] = outbox
        writer_task = asyncio.create_task(_writer(websocket, outbox))
        asyncio.create_task(_enqueue_replay(outbox))

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    fn = data.get("fn", "")
                    if fn and fn not in _NO_STORE:
                        _state_store[fn] = message
                        if len(_state_store) > _MAX_STORE:
                            _state_store.popitem(last=False)  # FIFO eviction
                    print(f"[{_ts()}]    -> {data}")
                except json.JSONDecodeError:
                    print(f"[{_ts()}] [!] JSON invalido ignorado: {message[:80]}")
                    continue  # Fail-fast: no broadcast de mensajes malformados
                except Exception as e:
                    print(f"[{_ts()}] [!] Error procesando: {e}")
                    continue

                _broadcast(message)

        except Exception as e:
            print(f"[{_ts()}] [!] {addr} error: {e}")
        finally:
            writer_task.cancel()
            _outboxes.pop(websocket, None)
            print(f"[{_ts()}] [-] {addr} desconectado  "
                  f"clientes={max(0, len(server.connections) - 1)}")

    async with serve(relay, _WS_BIND, _WS_PORT) as server:
        print(f"[{_ts()}] {_NAME} WS Relay en ws://{_WS_BIND}:{_WS_PORT}")
        print(f"[{_ts()}] (Ctrl+C para detener)")
        await server.serve_forever()


asyncio.run(main())
