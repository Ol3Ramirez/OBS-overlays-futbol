"""Ajustes de OBS compartidos entre perfiles (video canvas + salida/grabacion/audio).

Fuente unica: el bloque `video` y `output` de cada profile.json. La logica vive
aqui (no duplicada por perfil) para que cualquier subcarpeta nueva la herede al
importar este modulo. Cross-platform: el encoder y la ruta de grabacion se
resuelven por SO. Idempotente: aplicar N veces deja el mismo estado.

Uso desde <perfil>/setup_obs.py:

    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shared"))
    import obs_settings
    ...
    await obs_settings.apply_video_and_output(req, _P)   # req = closure obs-websocket
"""

import os
import sys


def _resolve_encoder(output: dict) -> str:
    """Encoder segun SO. Acepta string ("x264") o mapa {"darwin","win32","default"}.

    Default seguro multiplataforma: x264 (siempre disponible). En Mac Apple Silicon
    conviene apple_h264 (VideoToolbox, hardware); en Windows depende de la GPU.
    """
    enc = output.get("encoder", "x264")
    if isinstance(enc, dict):
        return enc.get(sys.platform) or enc.get("default") or "x264"
    return enc or "x264"


def _resolve_rec_dir(output: dict, profile_name: str) -> str:
    """Ruta de grabacion por SO si no se especifica una absoluta en profile.json."""
    rec = output.get("recPath")
    if rec:
        return os.path.expanduser(rec)
    home = os.path.expanduser("~")
    base = os.path.join(home, "Movies" if sys.platform == "darwin" else "Videos")
    return os.path.join(base, f"OBS-{profile_name}")


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

    # ── Ajustes generales (salida/grabacion/audio) via SetProfileParameter ──
    out = profile.get("output")
    if not out:
        return

    encoder = _resolve_encoder(out)

    async def _param(cat: str, name: str, value) -> None:
        r = await req("SetProfileParameter", {
            "parameterCategory": cat,
            "parameterName": name,
            "parameterValue": str(value),
        })
        if not r["requestStatus"]["result"]:
            print(f"    Aviso {cat}.{name}: {r['requestStatus'].get('comment', '')}")

    await _param("Output",       "Mode",          out.get("mode", "Simple"))
    await _param("SimpleOutput", "VBitrate",      out.get("streamBitrateKbps", 6000))
    await _param("SimpleOutput", "ABitrate",      out.get("audioBitrateKbps", 160))
    await _param("SimpleOutput", "StreamEncoder", encoder)
    await _param("SimpleOutput", "RecEncoder",    encoder)
    await _param("SimpleOutput", "RecFormat2",    out.get("recFormat", "hybrid_mp4"))
    await _param("SimpleOutput", "RecQuality",    out.get("recQuality", "Stream"))
    await _param("Audio",        "SampleRate",    out.get("audioSampleRate", 48000))
    await _param("Audio",        "ChannelSetup",  out.get("audioChannels", "Stereo"))

    rec_dir = _resolve_rec_dir(out, profile.get("name", "perfil"))
    os.makedirs(rec_dir, exist_ok=True)
    await _param("SimpleOutput", "FilePath", rec_dir)
    r_rec = await req("SetRecordDirectory", {"recordDirectory": rec_dir})
    if not r_rec["requestStatus"]["result"]:
        print(f"    Aviso SetRecordDirectory: {r_rec['requestStatus'].get('comment', '')}")

    print(f"  OK Ajustes generales aplicados (encoder={encoder}, rec={rec_dir})")

    await report_canvases(req)


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
