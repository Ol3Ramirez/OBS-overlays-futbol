#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["websockets>=15"]
# requires-python = ">=3.11"
# ///
"""
WebSocket Relay -- original
Lee configuracion desde profile.json (SSOT).

Principios:
  SSOT        -- puerto, bind y configuracion desde profile.json
  Fail-fast   -- sale inmediatamente si profile.json no existe
  Atomico     -- state_store FIFO, sin crecer indefinidamente
  Idempotente -- estado se replica a cada cliente al conectar
"""
import asyncio
import base64
import hashlib
import json
import os
import pathlib
import shutil
import sys
import uuid
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
_WS_PORT  = _profile.get("wsPort",        8889)
_WS_BIND  = _profile.get("wsBindAddress", "127.0.0.1")
_NAME     = _profile.get("name",          "original")

_NO_STORE = frozenset({
    "clear", "clearSpeaker", "clearTopic", "hideBadge",
    "stopCountdown", "hide", "resetClock",
    "setScene", "triggerReplay",
})

_state_store: OrderedDict[str, str] = OrderedDict()
_MAX_STORE = 100
_outboxes: dict = {}

# ── OBS WebSocket para setScene + replay ──
_obs_ws            = None
_obs_authenticated = False

_replay_lock:          asyncio.Lock           = asyncio.Lock()
_replay_saved_future:  "asyncio.Future | None" = None
_replay_playing_future: "asyncio.Future | None" = None
_previous_scene:       "str | None"            = None
_scene_future:         "asyncio.Future | None" = None
_scene_future_rid:     "str | None"            = None

_FEATURES        = _profile.get("features", {})
_ENABLE_REPLAY   = _FEATURES.get("ENABLE_REPLAY", False)
_REPLAY_SLOWMO   = _profile.get("replaySlowmoFactor",  0.5)
_REPLAY_DURATION = int(_profile.get("replayDuration",  12))
_REPLAY_INPUT    = _profile.get("replayInputName",     "Replay-Video")


def _build_scene_map(profile: dict) -> dict:
    prefix = profile.get("scenePrefix", "")
    scenes = profile.get("scenes", {})
    scene_map = {name: f"{prefix}{name}" for name in scenes}
    for alias, target in profile.get("sceneAliases", {}).items():
        scene_map[alias] = f"{prefix}{target}"
    return scene_map


SCENE_MAP = _build_scene_map(_profile)


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


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


def _broadcast(message: str) -> None:
    for outbox in list(_outboxes.values()):
        outbox.put_nowait(message)


async def _writer(websocket, outbox: asyncio.Queue) -> None:
    try:
        while True:
            await websocket.send(await outbox.get())
    except Exception:
        pass


async def _enqueue_replay(outbox: asyncio.Queue) -> None:
    for msg in list(_state_store.values()):
        await outbox.put(msg)
        await asyncio.sleep(0.25)


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
    """Consulta la escena activa. Usa _scene_future resuelto por _obs_connect_loop."""
    global _scene_future, _scene_future_rid
    if not _obs_ws or not _obs_authenticated:
        return None
    rid = str(uuid.uuid4())
    prefix = _profile.get("scenePrefix", "")
    _scene_future     = asyncio.get_running_loop().create_future()
    _scene_future_rid = rid
    try:
        await _obs_ws.send(json.dumps({
            "op": 6,
            "d": {"requestType": "GetCurrentProgramScene", "requestId": rid, "requestData": {}},
        }))
        resp_data = await asyncio.wait_for(_scene_future, timeout=3.0)
        full = resp_data.get("currentProgramSceneName", "")
        short = full[len(prefix):] if prefix and full.startswith(prefix) else full
        return short or None
    except asyncio.TimeoutError:
        print(f"[{_ts()}] [!] _obs_get_current_scene: timeout")
        return None
    except Exception as e:
        print(f"[{_ts()}] [!] _obs_get_current_scene: {e}")
        return None
    finally:
        _scene_future     = None
        _scene_future_rid = None


async def _obs_ffmpeg_slowmo(src_path: str) -> "str | None":
    """Crea versión a cámara lenta del clip guardado por OBS. Cross-platform.

    Toma los últimos `in_duration` segundos del buffer (no los primeros) usando
    -sseof, para que el replay muestre la jugada más reciente.
    """
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print(f"[{_ts()}] [!] ffmpeg no encontrado — sin cámara lenta (instala ffmpeg)")
        return None
    src = pathlib.Path(src_path)
    # timestamp único por replay: OBS ve un path distinto y abre el archivo de cero
    # (si el path es el mismo, OBS puede reutilizar el handle del replay anterior)
    ts  = int(datetime.now().timestamp())
    out = src.parent / f"replay_slowmo_{ts}.mp4"
    pts_factor  = round(1.0 / _REPLAY_SLOWMO, 4)          # 0.5 → 2.0
    in_duration = round(_REPLAY_DURATION * _REPLAY_SLOWMO, 2)  # segundos de input necesarios (ej. 6)
    fps_out     = _profile.get("video", {}).get("fps", 30)
    try:
        proc = await asyncio.create_subprocess_exec(
            ffmpeg, "-y",
            "-sseof", f"-{in_duration}",   # buscar desde el FINAL del archivo (jugada más reciente)
            "-i", str(src),
            # PTS-STARTPTS resetea timestamps al punto de inicio del seek;
            # luego pts_factor*PTS aplica el slowmo; fps duplica frames para mantener 30fps suave
            "-vf", f"setpts=PTS-STARTPTS,setpts={pts_factor}*PTS,fps={fps_out}",
            "-an",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-t", str(_REPLAY_DURATION),
            str(out),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode == 0 and out.exists():
            size_kb = out.stat().st_size // 1024
            print(f"[{_ts()}] ffmpeg OK: {out} ({size_kb} KB | últimos {in_duration}s → {_REPLAY_DURATION}s slowmo)")
            return str(out)
        lines = stderr.decode(errors="replace").strip().splitlines()
        tail  = " | ".join(lines[-3:]) if lines else "(sin stderr)"
        print(f"[{_ts()}] [!] ffmpeg retornó {proc.returncode}: {tail}")
        return None
    except Exception as e:
        print(f"[{_ts()}] [!] ffmpeg error: {e}")
        return None


def _cleanup_slowmo_files(directory: pathlib.Path) -> None:
    """Elimina archivos replay_slowmo_*.mp4 excepto los 2 más recientes."""
    files = sorted(directory.glob("replay_slowmo_*.mp4"), key=lambda f: f.stat().st_mtime)
    for old in files[:-2]:
        try:
            old.unlink()
        except Exception:
            pass


async def _obs_replay() -> None:
    """Flujo completo: guardar buffer → slow-mo → escena Replay → restaurar escena.

    Usa MediaInputPlaybackStarted para saber exactamente cuándo OBS terminó de
    cargar el archivo, eliminando la race condition de SetInputSettings asíncrono.
    """
    global _replay_saved_future, _replay_playing_future, _previous_scene
    if not _ENABLE_REPLAY:
        return
    if not _obs_ws or not _obs_authenticated:
        print(f"[{_ts()}] [!] triggerReplay: OBS no conectado")
        return

    async with _replay_lock:
        loop = asyncio.get_running_loop()

        # ── 1. Guardar buffer ──────────────────────────────────────────────────
        _replay_saved_future = loop.create_future()
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

        # ── 2. Generar slow-mo ────────────────────────────────────────────────
        print(f"[{_ts()}] Replay guardado: {saved_path}")
        slowmo = await _obs_ffmpeg_slowmo(saved_path)
        video  = slowmo if slowmo else saved_path
        print(f"[{_ts()}] Cargando en {_REPLAY_INPUT}: {video}")

        prev = _previous_scene or await _obs_get_current_scene()

        # ── 3. Detener reproducción anterior y cargar nuevo archivo ───────────
        await _obs_send("TriggerMediaInputAction", {
            "inputName":   _REPLAY_INPUT,
            "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_STOP",
        })
        await asyncio.sleep(0.2)

        await _obs_send("SetInputSettings", {
            "inputName":     _REPLAY_INPUT,
            "inputSettings": {
                "local_file":          video,
                "is_local_file":       True,
                "looping":             False,
                "restart_on_activate": False,
            },
            "overlay": True,  # merge: solo cambia los campos enviados, no resetea el resto
        })

        # ── 4. Esperar a que OBS confirme que el video está reproduciéndose ───
        # MediaInputPlaybackStarted = OBS abrió el archivo y el decoder está activo.
        # Resuelto por _obs_connect_loop cuando llega el evento de OBS.
        _replay_playing_future = loop.create_future()
        await asyncio.sleep(0.3)  # margen mínimo para que SetInputSettings sea procesado

        await _obs_send("TriggerMediaInputAction", {
            "inputName":   _REPLAY_INPUT,
            "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART",
        })

        confirmed = False
        try:
            await asyncio.wait_for(asyncio.shield(_replay_playing_future), timeout=5.0)
            confirmed = True
            print(f"[{_ts()}] MediaInputPlaybackStarted confirmado — video listo")
        except asyncio.TimeoutError:
            print(f"[{_ts()}] [!] Timeout MediaInputPlaybackStarted — delay de seguridad 1s")
            await asyncio.sleep(1.0)
        finally:
            _replay_playing_future = None

        # ── 5. Reiniciar desde frame 0 y mostrar escena ───────────────────────
        # Un segundo RESTART asegura que el usuario vea desde el principio,
        # no desde los ~200ms que el video lleva reproduciéndose en background.
        await _obs_send("TriggerMediaInputAction", {
            "inputName":   _REPLAY_INPUT,
            "mediaAction": "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART",
        })
        await _obs_set_scene("Replay")
        print(f"[{_ts()}] Reproduciendo {_REPLAY_DURATION}s — anterior: {prev}")

        await asyncio.sleep(_REPLAY_DURATION + 0.5)
        if prev and prev != "Replay":
            await _obs_set_scene(prev)

        # Limpiar archivos de replay antiguos: mantener solo los 2 más recientes
        # (el actual sigue siendo el más nuevo; el anterior como respaldo)
        if slowmo:
            _cleanup_slowmo_files(pathlib.Path(slowmo).parent)


async def _obs_connect_loop() -> None:
    """Mantiene conexion persistente con OBS WS para setScene y replay."""
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
                # 0x7FFFFFFF = todos los eventos (General|Config|Scenes|Inputs|Outputs|etc.)
                # 1024 (solo Ui) era incorrecto — ReplayBufferSaved es evento Outputs (64)
                identify_d  = {"rpcVersion": rpc_version, "eventSubscriptions": 0x7FFFFFFF}

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

                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue
                    op = msg.get("op")
                    if op == 7:
                        # Respuesta a request (GetCurrentProgramScene, StartReplayBuffer, etc.)
                        d = msg.get("d", {})
                        rid = d.get("requestId", "")
                        status = d.get("requestStatus", {})
                        if not status.get("result", True):
                            print(f"[{_ts()}] OBS op:7 error — {d.get('requestType')} "
                                  f"code={status.get('code')} {status.get('comment','')}")
                        if rid and rid == _scene_future_rid and _scene_future and not _scene_future.done():
                            _scene_future.set_result(d.get("responseData", {}))
                    elif op == 5:
                        event_type = msg["d"].get("eventType", "")
                        event_data = msg["d"].get("eventData", {})
                        if event_type == "ReplayBufferSaved":
                            path = event_data.get("savedReplayPath", "")
                            print(f"[{_ts()}] ReplayBufferSaved: {path}")
                            if _replay_saved_future and not _replay_saved_future.done():
                                _replay_saved_future.set_result(path)
                        elif event_type == "MediaInputPlaybackStarted":
                            inp = event_data.get("inputName", "")
                            print(f"[{_ts()}] MediaInputPlaybackStarted: {inp}")
                            if (inp == _REPLAY_INPUT
                                    and _replay_playing_future
                                    and not _replay_playing_future.done()):
                                _replay_playing_future.set_result(True)

        except Exception as e:
            _obs_ws            = None
            _obs_authenticated = False
            detail = ""
            if hasattr(e, "code") and hasattr(e, "reason"):
                detail = f" code={e.code} reason={e.reason!r}"
            print(f"[{_ts()}] OBS WS desconectado ({e.__class__.__name__}{detail}), reintentando en 5s...")
            await asyncio.sleep(5)


async def main() -> None:
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
                    if fn == "resetClock":
                        _state_store.pop("setMinute", None)
                        _state_store.pop("addedTime", None)
                    if fn and fn not in _NO_STORE:
                        _state_store[fn] = message
                        if len(_state_store) > _MAX_STORE:
                            _state_store.popitem(last=False)
                    print(f"[{_ts()}]    -> {data}")
                except json.JSONDecodeError:
                    print(f"[{_ts()}] [!] JSON invalido ignorado: {message[:80]}")
                    continue
                except Exception as e:
                    print(f"[{_ts()}] [!] Error procesando: {e}")
                    continue

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
            print(f"[{_ts()}] [-] {addr} desconectado  "
                  f"clientes={max(0, len(server.connections) - 1)}")

    async with serve(relay, _WS_BIND, _WS_PORT, ping_interval=30, ping_timeout=15) as server:
        asyncio.create_task(_obs_connect_loop())
        print(f"[{_ts()}] {_NAME} WS Relay en ws://{_WS_BIND}:{_WS_PORT}")
        print(f"[{_ts()}] (Ctrl+C para detener)")
        await server.serve_forever()


asyncio.run(main())
