#!/bin/bash
# verificar.sh -- Chequeo de salud de un perfil (Mac / Linux).
# Equivalente exacto de verificar.ps1 (Windows). Mismo formato de salida.
#
# Uso: bash verificar.sh [original|SRYiyo]   (por defecto: SRYiyo)

set -uo pipefail

DIR_ROOT="$(cd "$(dirname "$0")" && pwd)"
PROFILE="${1:-SRYiyo}"
PDIR="$DIR_ROOT/$PROFILE"

FAILS=0
ok()   { echo "[OK]  $1"; }
warn() { echo "[!]   $1"; }
bad()  { echo "[X]   $1"; FAILS=$((FAILS + 1)); }

echo "==================================================="
echo "  Verificacion del perfil: $PROFILE"
echo "==================================================="

# 1. Dependencias
command -v python3 >/dev/null 2>&1 && ok "python3 disponible" || bad "python3 NO encontrado"
command -v uv      >/dev/null 2>&1 && ok "uv disponible"      || warn "uv NO encontrado (necesario para ws_relay.py)"

# 2. profile.json existe y es valido
if [ ! -f "$PDIR/profile.json" ]; then
  bad "profile.json no existe en $PDIR"
  echo "" ; echo "Resultado: $FAILS fallo(s)." ; exit 1
fi
if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$PDIR/profile.json" 2>/dev/null; then
  ok "profile.json valido"
else
  bad "profile.json invalido (JSON corrupto)"
fi

HTTP_PORT=$(python3 -c "import json;print(json.load(open('$PDIR/profile.json'))['httpPort'])" 2>/dev/null || echo "")
WS_PORT=$(python3   -c "import json;print(json.load(open('$PDIR/profile.json'))['wsPort'])"   2>/dev/null || echo "")

# 3. config.js se regenera desde profile.json (SSOT)
if python3 "$DIR_ROOT/shared/gen_config.py" "$PDIR" >/dev/null 2>&1 && [ -f "$PDIR/config.js" ]; then
  ok "config.js se genera desde profile.json"
else
  bad "no se pudo generar config.js"
fi

# 4. Puertos escuchando
_listening() { lsof -i :"$1" -sTCP:LISTEN >/dev/null 2>&1; }
if [ -n "$HTTP_PORT" ] && _listening "$HTTP_PORT"; then ok "HTTP escuchando en $HTTP_PORT"; else warn "HTTP no escucha en ${HTTP_PORT:-?} (arranca con iniciar_stream.sh)"; fi
if [ -n "$WS_PORT" ]   && _listening "$WS_PORT";   then ok "WS relay escuchando en $WS_PORT"; else warn "WS relay no escucha en ${WS_PORT:-?}"; fi

# 5. OBS (informativo, no bloquea)
if _listening 4455; then ok "OBS WebSocket (4455) detectado"; else warn "OBS no detectado en 4455 (abrelo antes del partido)"; fi

echo "==================================================="
if [ "$FAILS" -eq 0 ]; then
  echo "Resultado: TODO OK ($PROFILE)"
  exit 0
else
  echo "Resultado: $FAILS fallo(s) critico(s) en $PROFILE"
  exit 1
fi
