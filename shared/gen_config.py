# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Genera config.js (espejo browser) desde profile.json.

profile.json es la UNICA fuente de verdad de cada perfil. Este script lo lee y
emite config.js (window.SRYI) — el archivo que cargan los overlays y el panel.
config.js queda gitignoreado: se regenera en cada arranque (lo invoca
iniciar_stream.sh / .ps1), igual que control_remoto.html se copia desde shared/.

El token real NUNCA se genera aqui: WS_TOKEN queda en null y el valor real vive
en config.local.js (gitignoreado), que el panel carga DESPUES de config.js.

Uso:
    uv run gen_config.py <ruta_perfil>     # ej. uv run gen_config.py ../SRYiyo
    python3 gen_config.py <ruta_perfil>    # tambien sirve sin uv

Sale con codigo 1 (fail-fast) si profile.json no existe o le faltan campos.
"""

import json
import os
import sys

# Campos obligatorios en profile.json (sin ellos, los overlays no renderizan bien).
REQUIRED_KEYS = (
    "home",
    "away",
    "matchLabel",
    "homeColor",
    "awayColor",
    "accent",
    "logo",
    "httpPort",
    "wsPort",
)

# Mapeo profile.json (camelCase) -> window.SRYI (UPPER_SNAKE).
# Los campos opcionales solo se emiten si existen en profile.json, asi un perfil
# minimalista (original) no arrastra claves que solo usa un perfil completo (SRYiyo).
SCALAR_MAP = (
    ("home", "HOME"),
    ("away", "AWAY"),
    ("matchLabel", "MATCH_LABEL"),
    ("homeColor", "HOME_COLOR"),
    ("awayColor", "AWAY_COLOR"),
    ("homeLogo", "HOME_LOGO"),
    ("awayLogo", "AWAY_LOGO"),
    ("accent", "ACCENT"),
    ("wsPort", "WS_PORT"),
    ("httpPort", "HTTP_PORT"),
    ("logo", "LOGO"),
    ("altavozLogo", "ALTAVOZ_LOGO"),
    ("altavozName", "ALTAVOZ_NAME"),
    ("altavozSocial", "ALTAVOZ_SOCIAL"),
    ("sport", "SPORT"),
    ("sponsor", "SPONSOR"),
    ("sponsorSocial", "SPONSOR_SOCIAL"),
    ("altavozFb", "ALTAVOZ_FB"),
    ("hostFb", "HOST_FB"),
)

# Campos que siempre se emiten con un valor por defecto si faltan en profile.json.
DEFAULTS = (
    ("wsHost", "WS_HOST", None),
    ("idaHome", "IDA_HOME", 0),
    ("idaAway", "IDA_AWAY", 0),
)

# Feature flags del panel compartido (shared/control_remoto.html). Origen unico:
# el bloque "features" de profile.json. Si falta, todas quedan apagadas.
FEATURE_FLAGS = (
    "ENABLE_AWAY_ROSTER",
    "ENABLE_PENALTIES",
    "ENABLE_UNDO",
    "ENABLE_IDA_SCORE",
    "ENABLE_QR",
    "ENABLE_REPLAY",
)


def _load_profile(profile_dir: str) -> dict:
    """Carga profile.json del perfil; fail-fast si no existe o esta corrupto."""
    profile_path = os.path.join(profile_dir, "profile.json")
    if not os.path.exists(profile_path):
        sys.exit(f"[FATAL] No existe {profile_path}")
    try:
        with open(profile_path, encoding="utf-8") as f:
            profile = json.load(f)
    except json.JSONDecodeError as err:
        sys.exit(f"[FATAL] profile.json invalido ({profile_path}): {err}")

    faltantes = [k for k in REQUIRED_KEYS if k not in profile]
    if faltantes:
        sys.exit(f"[FATAL] profile.json sin campos requeridos: {', '.join(faltantes)}")
    return profile


def _emit_line(key: str, value: object) -> str:
    """Devuelve una linea 'KEY: <literal JS>,' usando JSON (valido como literal JS)."""
    return f"  {key}: {json.dumps(value, ensure_ascii=False)},"


def build_config_js(profile: dict) -> str:
    """Construye el contenido de config.js (window.SRYI) desde el profile."""
    name = profile.get("name", "perfil")
    lines = [
        "/**",
        f" * {name} — config.js GENERADO desde profile.json por shared/gen_config.py.",
        " * NO editar a mano: se sobreescribe en cada arranque. Edita profile.json.",
        " * El token real va en config.local.js (gitignoreado), cargado despues de este.",
        " */",
        "window.SRYI = {",
    ]

    for src_key, dst_key in SCALAR_MAP:
        if src_key in profile:
            lines.append(_emit_line(dst_key, profile[src_key]))

    for src_key, dst_key, default in DEFAULTS:
        lines.append(_emit_line(dst_key, profile.get(src_key, default)))

    # Placeholders: el valor real lo aporta config.local.js / el panel en runtime.
    lines.append(_emit_line("WS_TOKEN", None))
    lines.append(_emit_line("PLAYERS", []))

    features = profile.get("features", {})
    for flag in FEATURE_FLAGS:
        lines.append(_emit_line(flag, bool(features.get(flag, False))))

    lines.append("};")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    profile_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    profile_dir = os.path.abspath(profile_dir)
    profile = _load_profile(profile_dir)

    config_js = build_config_js(profile)
    out_path = os.path.join(profile_dir, "config.js")

    # Escritura atomica: tmp + replace (evita config.js a medias si se interrumpe).
    tmp_path = out_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(config_js)
    os.replace(tmp_path, out_path)

    print(f"[OK] config.js generado desde profile.json -> {out_path}")


if __name__ == "__main__":
    main()
