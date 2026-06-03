#!/bin/bash
# iniciar_stream.sh -- SRYiyo (Mac / Linux)
#
# Principios aplicados:
#   SSOT       -- puertos leidos desde profile.json
#   Idempotente -- mata procesos previos antes de arrancar (re-ejecutar es seguro)
#   Atomico    -- si el WS relay falla, mata el HTTP server antes de salir
#   Fail-fast  -- verifica puertos activos despues de cada arranque
#
# Uso: bash iniciar_stream.sh

set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/logs"
mkdir -p "$LOG"

# Leer puertos desde profile.json (SSOT)
if ! command -v python3 &>/dev/null; then
  echo "[FATAL] python3 no encontrado. Instala Python 3.11+."
  exit 1
fi

HTTP_PORT=$(python3 -c "import json; d=json.load(open('$DIR/profile.json')); print(d['httpPort'])" 2>/dev/null || echo "8890")
WS_PORT=$(python3   -c "import json; d=json.load(open('$DIR/profile.json')); print(d['wsPort'])"   2>/dev/null || echo "8891")
PROFILE_NAME=$(python3 -c "import json; d=json.load(open('$DIR/profile.json')); print(d.get('name','SRYiyo'))" 2>/dev/null || echo "SRYiyo")

echo ""
echo "==================================================="
echo "  $PROFILE_NAME -- Iniciar Stream"
echo "  HTTP: $HTTP_PORT  |  WS: $WS_PORT"
echo "==================================================="
echo ""

# Auto-crear .env si no existe (primera vez en Mac — idempotente)
ENV_FILE="$DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "AVISO: .env no encontrado — configuracion inicial"
  echo ""
  if [ -f "$DIR/.env.example" ]; then
    # Intentar leer password de forma interactiva
    printf "  Ingresa el password de OBS WebSocket (puerto 4455): "
    read -r -s OBS_PWD
    echo ""
    if [ -n "$OBS_PWD" ]; then
      echo "OBS_WS_PASSWORD=$OBS_PWD" > "$ENV_FILE"
      echo "  OK .env creado (gitignoreado)"
    else
      echo "  AVISO: .env no creado — setup_obs.py pedira el password al conectar"
    fi
  fi
  echo ""
fi

# Funcion de limpieza atomica: si algo falla, mata lo que ya arranco
HTTP_PID=""
WS_PID=""

cleanup_on_fail() {
  echo "[!] Fallo detectado -- limpiando procesos parciales..."
  [ -n "$HTTP_PID" ] && kill "$HTTP_PID" 2>/dev/null || true
  [ -n "$WS_PID"   ] && kill "$WS_PID"   2>/dev/null || true
  exit 1
}
trap cleanup_on_fail ERR

# 1. Idempotencia: matar procesos anteriores en estos puertos
echo "Limpiando puertos $HTTP_PORT / $WS_PORT..."
lsof -ti :"$HTTP_PORT" 2>/dev/null | xargs -r kill -9 2>/dev/null || true
lsof -ti :"$WS_PORT"   2>/dev/null | xargs -r kill -9 2>/dev/null || true
sleep 1

# 2. HTTP server
echo "Iniciando HTTP en puerto $HTTP_PORT..."
python3 -m http.server "$HTTP_PORT" \
  > "$LOG/http.log" 2>&1 &
HTTP_PID=$!
sleep 1

if lsof -i :"$HTTP_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "  OK HTTP -> http://localhost:$HTTP_PORT"
else
  echo "  [FALLO] No pudo iniciar HTTP server"
  exit 1
fi

# 3. WS relay
echo "Iniciando WS relay en puerto $WS_PORT..."
uv run "$DIR/ws_relay.py" \
  > "$LOG/ws.log" 2>&1 &
WS_PID=$!
sleep 2

if lsof -i :"$WS_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "  OK WS Relay -> ws://localhost:$WS_PORT"
else
  echo "  [FALLO] No pudo iniciar WS relay"
  # Atomico: mata HTTP antes de salir
  kill "$HTTP_PID" 2>/dev/null || true
  exit 1
fi

# 4. Verificar OBS (no bloquea el arranque)
echo ""
echo "Verificando OBS WebSocket (puerto 4455)..."
if lsof -i :4455 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "  OK OBS WebSocket detectado"
else
  echo "  AVISO: OBS no detectado -- abrelo antes de usar el panel"
fi

# Guardar PIDs
echo "$HTTP_PID" > "$LOG/http.pid"
echo "$WS_PID"   > "$LOG/ws.pid"

echo ""
echo "==================================================="
echo "  Panel: http://localhost:$HTTP_PORT/control_remoto.html"
echo ""
echo "  Para detener:"
echo "    kill $HTTP_PID $WS_PID"
echo "    o: lsof -ti :$HTTP_PORT :$WS_PORT | xargs kill -9"
echo "==================================================="
echo ""
echo "-- Log WS en vivo (Ctrl+C para salir) --"
tail -f "$LOG/ws.log"
