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
import os
import pathlib
import shutil
import sys
import tempfile
import uuid
from collections import OrderedDict
from datetime import datetime

from websockets.asyncio.server import serve


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
    "triggerReplay",
})

_state_store: OrderedDict[str, str] = OrderedDict()
_MAX_STORE  = 100
_auth_ok: set = set()  # websockets autenticados (para control remoto)
_outboxes: dict = {}   # websocket -> asyncio.Queue de salida (ver main())

# ── OBS WebSocket para setScene + replay ──
_obs_ws            = None
_obs_authenticated = False

_replay_lock:         asyncio.Lock           = asyncio.Lock()
_replay_saved_future: "asyncio.Future | None" = None
_previous_scene:      "str | None"            = None

_FEATURES        = _profile.get("features", {})
_ENABLE_REPLAY   = _FEATURES.get("ENABLE_REPLAY", False)
_REPLAY_SLOWMO   = _profile.get("replaySlowmoFactor",  0.5)
_REPLAY_DURATION = int(_profile.get("replayDuration",  12))
_REPLAY_INPUT    = _profile.get("replayInputName",     "Replay-Video")

def _build_scene_map(profile: dict) -> dict:
    """Mapa nombre-corto -> nombre de escena en OBS, derivado de profile.json.

    Cada escena de `scenes` mapea a `scenePrefix` + su nombre. `sceneAliases`
    agrega nombres alternativos (ej. "Intro" -> "Inicio") que apuntan a la misma
    escena prefijada. Asi el SCENE_MAP es SSOT: vive solo en profile.json.
    """
    prefix = profile.get("scenePrefix", "")
    scenes = profile.get("scenes", {})
    scene_map = {name: f"{prefix}{name}" for name in scenes}
    for alias, target in profile.get("sceneAliases", {}).items():
        scene_map[alias] = f"{prefix}{target}"
    return scene_map


SCENE_MAP = _build_scene_map(_profile)


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


async def _obs_send(request_type: str, request_data: dict = {}) -> None:
    """Envía un request a OBS WS (fire-and-forget, no espera respuesta)."""
    if not _obs_ws or not _obs_authenticated:
        return
    rid = str(uuid.uuid4())
    try:
        await _obs_ws.send(json.dumps({
            "op": 6,
            "d": {"requestType": request_type, "requestId": rid, "requestData": request_data},
        }))
    except Exception as e:
        print(f"[{_ts()}] [!] _obs_send {request_type}: {e}")


async def _obs_get_current_scene() -> "str | None":
    """Consulta la escena activa en OBS y devuelve su nombre corto (sin prefijo)."""
    if not _obs_ws or not _obs_authenticated:
        return None
    rid = str(uuid.uuid4())
    prefix = _profile.get("scenePrefix", "")
    try:
        await _obs_ws.send(json.dumps({
            "op": 6,
            "d": {"requestType": "GetCurrentProgramScene", "requestId": rid, "requestData": {}},
        }))
        async with asyncio.timeout(3.0):
            async for raw in _obs_ws:
                msg = json.loads(raw)
                if msg.get("op") == 7 and msg["d"].get("requestId") == rid:
                    full = msg["d"].get("responseData", {}).get("currentProgramSceneName", "")
                    short = full[len(prefix):] if prefix and full.startswith(prefix) else full
                    return short or None
    except Exception as e:
        print(f"[{_ts()}] [!] _obs_get_current_scene: {e}")
    return None


async def _obs_ffmpeg_slowmo(src_path: str) -> "str | None":
    """Crea versión a cámara lenta del clip guardado por OBS. Cross-platform."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print(f"[{_ts()}] [!] ffmpeg no encontrado — sin cámara lenta (instala ffmpeg)")
        return None
    src = pathlib.Path(src_path)
    out = src.parent / f"replay_slowmo{src.suffix}"
    pts_factor = round(1.0 / _REPLAY_SLOWMO, 4)  # 0.5 → 2.0
    try:
        proc = await asyncio.create_subprocess_exec(
            ffmpeg, "-y", "-i", str(src),
            "-vf", f"setpts={pts_factor}*PTS",
            "-an",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18",
            "-t", str(_REPLAY_DURATION),
            str(out),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        if proc.returncode == 0 and out.exists():
            print(f"[{_ts()}] ffmpeg OK: {out}")
            return str(out)
        print(f"[{_ts()}] [!] ffmpeg retornó {proc.returncode}")
        return None
    except Exception as e:
        print(f"[{_ts()}] [!] ffmpeg error: {e}")
        return None


async def _obs_replay() -> None:
    """Flujo completo: guardar buffer → slow-mo → escena Replay → restaurar escena."""
    global _replay_saved_future, _previous_scene
    if not _ENABLE_REPLAY:
        return
    if not _obs_ws or not _obs_authenticated:
        print(f"[{_ts()}] [!] triggerReplay: OBS no conectado")
        return

    async with _replay_lock:
        loop = asyncio.get_event_loop()
        _replay_saved_future = loop.create_future()

        await _obs_send("StartReplayBuffer")   # idempotente si ya corre
        await asyncio.sleep(0.1)
        await _obs_send("SaveReplayBuffer")

        try:
            saved_path = await asyncio.wait_for(
                asyncio.shield(_replay_saved_future), timeout=10.0
            )
        except asyncio.TimeoutError:
            print(f"[{_ts()}] [!] Timeout esperando ReplayBufferSaved (¿replay buffer activo en OBS?)")
            _replay_saved_future = None
            return
        finally:
            _replay_saved_future = None

        if not saved_path:
            print(f"[{_ts()}] [!] OBS no devolvió path del replay")
            return

        print(f"[{_ts()}] Replay guardado: {saved_path}")
        slowmo = await _obs_ffmpeg_slowmo(saved_path)
        video  = slowmo if slowmo else saved_path

        await _obs_send("SetInputSettings", {
            "inputName":     _REPLAY_INPUT,
            "inputSettings": {"local_file": video},
            "overlay":       True,
        })
        await asyncio.sleep(0.15)
        await _obs_send("TriggerMediaInputAction", {
            "inputName":   _REPLAY_INPUT,
            "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART",
        })

        # Usar escena actual de OBS como fallback si el panel no la actualizó
        prev = _previous_scene or await _obs_get_current_scene()
        await _obs_set_scene("Replay")
        await asyncio.sleep(_REPLAY_DURATION + 1.5)
        if prev and prev != "Replay":
            await _obs_set_scene(prev)


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
                identify_d  = {"rpcVersion": rpc_version, "eventSubscriptions": 1024}

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

                # Parsea eventos OBS (suscripción 1024 = Outputs)
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue
                    if msg.get("op") != 5:
                        continue
                    event_type = msg["d"].get("eventType", "")
                    event_data = msg["d"].get("eventData", {})
                    if event_type == "ReplayBufferSaved":
                        path = event_data.get("savedReplayPath", "")
                        print(f"[{_ts()}] ReplayBufferSaved: {path}")
                        if _replay_saved_future and not _replay_saved_future.done():
                            _replay_saved_future.set_result(path)

        except Exception as e:
            _obs_ws            = None
            _obs_authenticated = False
            print(f"[{_ts()}] OBS WS desconectado ({e.__class__.__name__}), reintentando en 5s...")
            await asyncio.sleep(5)


def _broadcast(message: str) -> None:
    for outbox in list(_outboxes.values()):
        outbox.put_nowait(message)


async def _writer(websocket, outbox: asyncio.Queue) -> None:
    """Unico lugar que escribe en el socket de esta conexion. Drena la cola en
    el orden en que se encolo (FIFO) -- replay y mensajes en vivo nunca se
    desordenan entre si, y el read-loop (pings/keepalive) jamas espera un send.
    """
    try:
        while True:
            await websocket.send(await outbox.get())
    except Exception:
        pass  # conexion cerrada -- el finally de relay() limpia


async def _enqueue_replay(outbox: asyncio.Queue) -> None:
    """Encola el estado guardado al cliente recien conectado, escalonado.

    El stagger evita que todas las transiciones CSS (lower-third, ticker, cambio
    de modo) disparen en la misma rafaga (parpadeo). Encolar -- no enviar
    directo -- preserva el orden FIFO frente a comandos en vivo que lleguen
    mientras el replay todavia se esta armando.
    """
    for msg in list(_state_store.values()):
        await outbox.put(msg)
        await asyncio.sleep(0.25)


async def main() -> None:
    async def relay(websocket) -> None:
        addr  = websocket.remote_address
        local = _is_local(addr)

        print(f"[{_ts()}] [+] {addr}  local={local}  clientes={len(server.connections)}")

        outbox: asyncio.Queue = asyncio.Queue()
        _outboxes[websocket] = outbox
        writer_task = asyncio.create_task(_writer(websocket, outbox))
        asyncio.create_task(_enqueue_replay(outbox))

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
                        outbox.put_nowait(json.dumps({"fn": "_authOK"}))
                        print(f"[{_ts()}] [OK] {addr} autenticado")
                    else:
                        outbox.put_nowait(json.dumps({"fn": "_authFailed"}))
                        print(f"[{_ts()}] [!] {addr} token invalido")
                    continue  # No broadcast del mensaje de auth

                # ── Verificar autorizacion ──
                if websocket not in _auth_ok:
                    print(f"[{_ts()}] [!] {addr} no autenticado — enviar {{\"auth\":\"token\"}}")
                    outbox.put_nowait(json.dumps({"fn": "_authRequired"}))
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

                # ── setScene → OBS WS directamente ──
                if fn == "setScene":
                    args = data.get("args", [])
                    if args:
                        global _previous_scene
                        _previous_scene = args[0]
                        asyncio.create_task(_obs_set_scene(args[0]))

                # ── triggerReplay → flujo completo de replay ──
                if fn == "triggerReplay":
                    asyncio.create_task(_obs_replay())

                _broadcast(message)

        except Exception as e:
            print(f"[{_ts()}] [!] {addr} error: {e}")
        finally:
            writer_task.cancel()
            _outboxes.pop(websocket, None)
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
