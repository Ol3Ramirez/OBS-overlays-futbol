"""Ajustes de OBS compartidos entre perfiles (video canvas + salida/grabacion/audio
+ camara SRT). Fuente unica: los bloques `video`/`output` y los campos
`srtPort`/`srtLatencyMs`/`scenePrefix` de cada profile.json. La logica vive aqui
(no duplicada por perfil) para que cualquier subcarpeta nueva la herede al
importar este modulo. Cross-platform: encoder, ruta de grabacion y carpeta de
config de OBS se resuelven por SO. Idempotente: aplicar N veces deja el mismo
estado.

Uso desde <perfil>/setup_obs.py:

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shared"))
    import obs_settings
    ...
    await obs_settings.apply_video_and_output(req, _P)            # canvas + salida
    await obs_settings.ensure_camera_in_scenes(req, _P, SCENE_PREFIX)  # camara SRT
"""

import asyncio
import json
import os
import sys
import tempfile


def _resolve_encoder(output: dict) -> str:
    """Encoder segun SO. Acepta string ("x264") o mapa {"darwin","win32","default"}.

    Default seguro multiplataforma: x264 (siempre disponible). En Mac Apple Silicon
    conviene apple_h264 (VideoToolbox, hardware); en Windows depende de la GPU.
    """
    enc = output.get("encoder", "x264")
    if isinstance(enc, dict):
        return enc.get(sys.platform) or enc.get("default") or "x264"
    return enc or "x264"


# Mapa de id "simple" (el que usa SimpleOutput.StreamEncoder) -> id real del
# encoder en modo Advanced (el que espera AdvOut.Encoder). obs_x264 es universal
# (compilado en libobs); el id de Apple VideoToolbox se confirmo leyendo en disco
# el basic.ini de un perfil real en macOS (Settings -> Output -> Advanced).
_ADVANCED_ENCODER_MAP = {
    "x264":       "obs_x264",
    "apple_h264": "com.apple.videotoolbox.videoencoder.ave.avc",
}


def _resolve_rec_dir(output: dict, profile_name: str) -> str:
    """Ruta de grabacion por SO si no se especifica una absoluta en profile.json."""
    rec = output.get("recPath")
    if rec:
        return os.path.expanduser(rec)
    home = os.path.expanduser("~")
    base = os.path.join(home, "Movies" if sys.platform == "darwin" else "Videos")
    return os.path.join(base, f"OBS-{profile_name}")


def _obs_config_dir() -> str | None:
    """Carpeta de datos de OBS Studio por SO. None si el SO no es soportado --
    no rompe el flujo, solo se omite el sidecar de bitrate de modo Advanced."""
    home = os.path.expanduser("~")
    if sys.platform == "darwin":
        return os.path.join(home, "Library", "Application Support", "obs-studio")
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        return os.path.join(appdata, "obs-studio") if appdata else None
    return None


def _write_encoder_bitrate_sidecar(profile_name: str, filename: str, bitrate_kbps: int) -> None:
    """Escribe el bitrate del encoder Advanced directamente en su sidecar JSON.

    obs-websocket NO expone un request para configurar el bitrate del encoder en
    modo Advanced: SetProfileParameter solo escribe basic.ini, y el bitrate de
    Advanced vive en <perfil>/streamEncoder.json (confirmado leyendo el archivo
    real -- ej. {"bitrate":5000} -- y la doc oficial del protocolo, que no lista
    ningun request para esto). Escribir el JSON es el unico camino programatico.
    Atomico via tmp+replace, igual que el resto de escrituras de este repo.
    """
    base = _obs_config_dir()
    if not base:
        print(f"    [AVISO] SO no reconocido para sidecar de encoder -- "
              f"ajusta el bitrate manualmente en OBS (Salida -> {filename}).")
        return
    out_dir = os.path.join(base, "basic", "profiles", profile_name)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    fd, tmp_path = tempfile.mkstemp(dir=out_dir, prefix=f".{filename}.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"bitrate": bitrate_kbps}, f)
        os.replace(tmp_path, path)
    except Exception as e:
        os.unlink(tmp_path)
        print(f"    [AVISO] No se pudo escribir {filename}: {e}")


async def _apply_advanced_bitrate(req, profile_name: str, stream_kbps: int, write_record: bool) -> None:
    """Escribe el bitrate Advanced y fuerza que OBS lo relea desde disco.

    OBS guarda el bitrate en memoria mientras el perfil esta activo y puede
    re-escribir el sidecar con ese valor al desactivarlo. Para que nuestro
    archivo no quede pisado, se escribe MIENTRAS el perfil esta inactivo
    (justo tras salir de el via otro perfil) y se reactiva despues -- asi la
    unica fuente que OBS lee al reactivar es el archivo que acabamos de escribir.
    """
    pl = await req("GetProfileList")
    others = [p for p in pl["responseData"].get("profiles", []) if p != profile_name]
    if not others:
        print("    [AVISO] No hay otro perfil para forzar el reload del bitrate "
              "Advanced -- se escribe igual, pero solo se vera tras cambiar de "
              "perfil manualmente una vez en OBS.")
        _write_encoder_bitrate_sidecar(profile_name, "streamEncoder.json", stream_kbps)
        if write_record:
            _write_encoder_bitrate_sidecar(profile_name, "recordEncoder.json", stream_kbps)
        return

    await req("SetCurrentProfile", {"profileName": others[0]})
    await asyncio.sleep(0.6)

    _write_encoder_bitrate_sidecar(profile_name, "streamEncoder.json", stream_kbps)
    if write_record:
        _write_encoder_bitrate_sidecar(profile_name, "recordEncoder.json", stream_kbps)

    await req("SetCurrentProfile", {"profileName": profile_name})
    await asyncio.sleep(0.6)


async def _set_param(req, category: str, name: str, value) -> None:
    r = await req("SetProfileParameter", {
        "parameterCategory": category,
        "parameterName": name,
        "parameterValue": str(value),
    })
    if not r["requestStatus"]["result"]:
        print(f"    Aviso {category}.{name}: {r['requestStatus'].get('comment', '')}")


async def _apply_simple_output(req, out: dict, encoder: str, rec_dir: str) -> None:
    await _set_param(req, "SimpleOutput", "VBitrate",      out.get("streamBitrateKbps", 6000))
    await _set_param(req, "SimpleOutput", "ABitrate",      out.get("audioBitrateKbps", 160))
    await _set_param(req, "SimpleOutput", "StreamEncoder", encoder)
    await _set_param(req, "SimpleOutput", "RecEncoder",    encoder)
    await _set_param(req, "SimpleOutput", "RecFormat2",    out.get("recFormat", "hybrid_mp4"))
    await _set_param(req, "SimpleOutput", "RecQuality",    out.get("recQuality", "Stream"))
    await _set_param(req, "SimpleOutput", "FilePath",      rec_dir)

    r_rec = await req("SetRecordDirectory", {"recordDirectory": rec_dir})
    if not r_rec["requestStatus"]["result"]:
        print(f"    Aviso SetRecordDirectory: {r_rec['requestStatus'].get('comment', '')}")

    print(f"  OK Ajustes generales aplicados (modo=Simple, encoder={encoder}, rec={rec_dir})")


async def _apply_advanced_output(req, out: dict, encoder: str, rec_dir: str, profile_name: str) -> None:
    adv_encoder = _ADVANCED_ENCODER_MAP.get(encoder, encoder)
    usa_stream_para_rec = out.get("recQuality", "Stream") == "Stream"
    rec_encoder = "none" if usa_stream_para_rec else adv_encoder
    stream_kbps = out.get("streamBitrateKbps", 6000)

    await _set_param(req, "AdvOut", "TrackIndex",    1)
    await _set_param(req, "AdvOut", "Encoder",       adv_encoder)
    await _set_param(req, "AdvOut", "RecType",       "Standard")
    await _set_param(req, "AdvOut", "RecFilePath",   rec_dir)
    await _set_param(req, "AdvOut", "RecFormat2",    out.get("recFormat", "hybrid_mp4"))
    await _set_param(req, "AdvOut", "RecTracks",     1)
    await _set_param(req, "AdvOut", "RecEncoder",    rec_encoder)
    await _set_param(req, "AdvOut", "Track1Bitrate", out.get("audioBitrateKbps", 160))

    await _apply_advanced_bitrate(req, profile_name, stream_kbps, write_record=not usa_stream_para_rec)

    r_rec = await req("SetRecordDirectory", {"recordDirectory": rec_dir})
    if not r_rec["requestStatus"]["result"]:
        print(f"    Aviso SetRecordDirectory: {r_rec['requestStatus'].get('comment', '')}")

    print(f"  OK Ajustes generales aplicados (modo=Advanced, encoder={adv_encoder}, "
          f"bitrate={stream_kbps}kbps, rec={rec_dir})")


async def apply_video_and_output(req, profile: dict) -> None:
    """Aplica canvas de video + ajustes generales del perfil via obs-websocket.

    `req(request_type, data)` es la corutina de setup_obs que envia una peticion
    obs-websocket y devuelve la respuesta cruda. Debe llamarse despues de
    SetCurrentProfile para que SetProfileParameter afecte al perfil correcto.
    """
    # ── Canvas de video (solo afecta el canvas Main) ──
    v = profile.get("video", {})
    r_vid = await req("SetVideoSettings", {
        "baseWidth":      v.get("baseWidth",   1920),
        "baseHeight":     v.get("baseHeight",  1080),
        "outputWidth":    v.get("outputWidth", 1920),
        "outputHeight":   v.get("outputHeight",1080),
        "fpsNumerator":   v.get("fps",         30),
        "fpsDenominator": 1,
    })
    if not r_vid["requestStatus"]["result"]:
        print(f"    Aviso SetVideoSettings: {r_vid['requestStatus'].get('comment', '')}")

    # ── Ajustes generales (salida/grabacion/audio) ──
    out = profile.get("output")
    if not out:
        return

    encoder = _resolve_encoder(out)
    mode    = out.get("mode", "Simple")
    await _set_param(req, "Output", "Mode", mode)

    # La carpeta de grabacion sigue el nombre del perfil de REPO (un folder por
    # partido/carpeta, aunque varias carpetas compartan un mismo Perfil de OBS).
    # El sidecar/bounce de bitrate Advanced en cambio debe apuntar al Perfil de
    # OBS real en disco (obsProfile) -- puede ser compartido entre carpetas.
    rec_dir          = _resolve_rec_dir(out, profile.get("name", "perfil"))
    obs_profile_name = profile.get("obsProfile") or profile.get("name", "perfil")
    os.makedirs(rec_dir, exist_ok=True)

    if mode == "Advanced":
        await _apply_advanced_output(req, out, encoder, rec_dir, obs_profile_name)
    else:
        await _apply_simple_output(req, out, encoder, rec_dir)

    await _set_param(req, "Audio", "SampleRate",   out.get("audioSampleRate", 48000))
    await _set_param(req, "Audio", "ChannelSetup", out.get("audioChannels", "Stereo"))

    await report_canvases(req)


# ── Camara SRT ───────────────────────────────────────────────────────────────

# Escenas que se ven en vivo sobre la camara (Inicio y Medio Tiempo son
# pantallas graficas sin camara -- ver original/CONFIG_IRL_PRO.md). Nombres
# SIN scenePrefix -- el prefijo se aplica al armar el nombre real de la escena.
SCENES_WITH_CAMERA = frozenset({"Partido", "Evento", "Alineacion", "Entrevista"})

CAMERA_NAME = "Camara SRT"


async def ensure_camera_in_scenes(req, profile: dict, scene_prefix: str) -> None:
    """Ancla "Camara SRT" detras del overlay en cada escena que la necesita.
    Idempotente: no duplica si ya esta anidada en esa escena. Llamar DESPUES de
    crear las escenas (CreateScene) -- aqui solo se nidan sources existentes.

    Bug corregido: antes se comparaba el nombre de escena YA prefijado contra
    SCENES_WITH_CAMERA (sin prefijo) -- nunca coincidia en perfiles con
    scenePrefix no vacio (SRYiyo, plantilla, tiktok-vertical), solo funcionaba
    en original (prefijo ""). Aqui el prefijo se aplica al armar el nombre, no
    al comparar.
    """
    srt_port       = profile.get("srtPort", 5000)
    srt_latency_ms = profile.get("srtLatencyMs", 4000)
    camera_url     = f"srt://0.0.0.0:{srt_port}?mode=listener&latency={srt_latency_ms * 1000}"
    v              = profile.get("video", {})
    bounds_w       = v.get("baseWidth", 1920)
    bounds_h       = v.get("baseHeight", 1080)

    async def ensure_in(scene_name: str) -> None:
        items = await req("GetSceneItemList", {"sceneName": scene_name})
        if not items["requestStatus"]["result"]:
            print(f"    Error leyendo items de {scene_name}: {items['requestStatus'].get('comment','')}")
            return
        nombres = {it["sourceName"] for it in items["responseData"]["sceneItems"]}
        if CAMERA_NAME in nombres:
            print(f"    (camara ya en {scene_name})")
            return

        inputs = await req("GetInputList")
        existe_global = any(i["inputName"] == CAMERA_NAME for i in inputs["responseData"]["inputs"])

        if not existe_global:
            rc = await req("CreateInput", {
                "sceneName":     scene_name,
                "inputName":     CAMERA_NAME,
                "inputKind":     "ffmpeg_source",
                "inputSettings": {
                    "is_local_file":       False,
                    "input":               camera_url,
                    "hw_decode":           True,
                    "reconnect_delay_sec": 2,
                    "buffering_mb":        2,
                },
                "sceneItemEnabled": True,
            })
            if not rc["requestStatus"]["result"]:
                print(f"    Error creando camara: {rc['requestStatus'].get('comment','')}")
                return
            print(f"    OK camara creada en {scene_name} -> {camera_url}")
        else:
            rc = await req("CreateSceneItem", {"sceneName": scene_name, "sourceName": CAMERA_NAME})
            if not rc["requestStatus"]["result"]:
                print(f"    Error anidando camara en {scene_name}: {rc['requestStatus'].get('comment','')}")
                return
            print(f"    OK camara anidada en {scene_name}")

        id_resp = await req("GetSceneItemId", {"sceneName": scene_name, "sourceName": CAMERA_NAME})
        item_id = id_resp["responseData"]["sceneItemId"]
        await req("SetSceneItemTransform", {
            "sceneName":     scene_name,
            "sceneItemId":   item_id,
            "sceneItemTransform": {
                "boundsType":      "OBS_BOUNDS_STRETCH",
                "boundsWidth":     bounds_w,
                "boundsHeight":    bounds_h,
                "boundsAlignment": 0,
            },
        })

    for short_name in SCENES_WITH_CAMERA:
        await ensure_in(f"{scene_prefix}{short_name}")
        await asyncio.sleep(0.2)


async def report_canvases(req) -> None:
    """Lista los canvases de OBS y guia sobre el vertical de TikTok.

    obs-websocket (5.7+) puede LISTAR canvases pero NO crearlos/configurarlos: el
    canvas vertical para TikTok lo gestiona el plugin de StreamElements por su API
    propia (CEF), no por obs-websocket. Aqui solo detectamos y avisamos. Resiliente:
    si la version de obs-websocket no soporta GetCanvasList, se omite en silencio.
    """
    try:
        r = await req("GetCanvasList")
    except Exception:
        return
    if not r.get("requestStatus", {}).get("result"):
        return
    for c in r["responseData"].get("canvases", []):
        vs = c.get("canvasVideoSettings") or {}
        dims = f"{vs.get('baseWidth')}x{vs.get('baseHeight')}" if vs.get("baseWidth") else "sin asignar"
        name = c.get("canvasName", "?")
        print(f"  Canvas: {name} ({dims})")
        low = name.lower()
        if ("se.live" in low or "managed" in low) and not vs.get("baseWidth"):
            print("    -> Canvas vertical de StreamElements detectado SIN asignar.")
            print("       Asignalo/configuralo en el panel SE.Live (Vertical / TikTok).")
            print("       No es automatizable por obs-websocket; ver TIKTOK.md.")
