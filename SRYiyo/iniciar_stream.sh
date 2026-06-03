#!/bin/bash
# ─────────────────────────────────────────────────────
#  SRYiyo — iniciar_stream.sh  (Mac / Linux)
#  Idempotente: mata procesos anteriores antes de arrancar.
#  Uso: bash ./iniciar_stream.sh
# ─────────────────────────────────────────────────────

DIR="$(cd "$(dirname "$0")" && pwd)"
LOG="$DIR/logs"
mkdir -p "$LOG"

HTTP_PORT=8890
WS_PORT=8891

echo ""
echo "═══════════════════════════════════════════════════"
echo "   SRYIYO — ROBLES FÚTBOL"
echo "   PROVEEDORA ROBLES vs HERMANOS OSORIO"
echo "   SEMIFINAL DE IDA"
echo "═══════════════════════════════════════════════════"
echo ""

# 1. Matar procesos anteriores
echo "▶ Limpiando procesos anteriores en puertos $HTTP_PORT / $WS_PORT..."
pkill -f "http.server $HTTP_PORT" 2>/dev/null
pkill -f "ws_relay.py" 2>/dev/null
# Espera liberación de puertos
sleep 1

# 2. Servidor HTTP
echo "▶ Iniciando HTTP en puerto $HTTP_PORT..."
cd "$DIR" && python3 -m http.server $HTTP_PORT > "$LOG/http.log" 2>&1 &
HTTP_PID=$!
sleep 1

if lsof -i :$HTTP_PORT -sTCP:LISTEN >/dev/null 2>&1; then
    echo "  ✅ HTTP OK  → http://localhost:$HTTP_PORT"
else
    echo "  ❌ ERROR: No pudo iniciar el servidor HTTP"
    exit 1
fi

# 3. WebSocket relay
echo "▶ Iniciando WS relay en puerto $WS_PORT..."
uv run "$DIR/ws_relay.py" > "$LOG/ws.log" 2>&1 &
WS_PID=$!
sleep 1

if lsof -i :$WS_PORT -sTCP:LISTEN >/dev/null 2>&1; then
    echo "  ✅ WS Relay OK  → ws://localhost:$WS_PORT"
else
    echo "  ❌ ERROR: No pudo iniciar el relay WebSocket"
    exit 1
fi

# 4. Verificar OBS
echo ""
echo "▶ Verificando OBS WebSocket (puerto 4455)..."
if lsof -i :4455 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "  ✅ OBS WebSocket detectado"
else
    echo "  ⚠️  OBS NO está abierto — ábrelo antes de usar el panel"
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "  Panel de control:"
echo "  http://localhost:$HTTP_PORT/control_remoto.html"
echo ""
echo "  PIDs: HTTP=$HTTP_PID  WS=$WS_PID"
echo "  Para detener:"
echo "    pkill -f 'http.server $HTTP_PORT' && pkill -f ws_relay.py"
echo "═══════════════════════════════════════════════════"
echo ""

echo "$HTTP_PID" > "$LOG/http.pid"
echo "$WS_PID"   > "$LOG/ws.pid"

echo "── Logs en vivo (Ctrl+C para salir) ──"
tail -f "$LOG/http.log" "$LOG/ws.log"
