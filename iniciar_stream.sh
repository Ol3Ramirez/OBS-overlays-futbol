#!/bin/bash
# ────────────────────────────────────────────
#  iniciar_stream.sh — Arranque completo del sistema de overlays
#  Ejecutar ANTES de abrir Claude Code
# ────────────────────────────────────────────

DIR="/Users/oleramirez/Movies/MY CLOUDE CODE/OBS_OVERLAYS_FUTBOL"
LOG="$DIR/logs"
mkdir -p "$LOG"

echo ""
echo "═══════════════════════════════════════════"
echo "   SISTEMA DE OVERLAYS — FÚTBOL 5"
echo "═══════════════════════════════════════════"
echo ""

# 1. Matar procesos anteriores si quedaron colgados
echo "▶ Limpiando procesos anteriores..."
pkill -f "http.server 8888" 2>/dev/null
pkill -f "ws_relay.py"      2>/dev/null
sleep 1

# 2. Servidor HTTP (overlays)
echo "▶ Iniciando servidor HTTP en puerto 8888..."
cd "$DIR"
python3 -m http.server 8888 > "$LOG/http.log" 2>&1 &
HTTP_PID=$!
sleep 1

# Verificar HTTP
if lsof -i :8888 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "  ✅ HTTP OK  (http://localhost:8888)"
else
    echo "  ❌ ERROR: No pudo iniciar el servidor HTTP"
    exit 1
fi

# 3. WebSocket relay
echo "▶ Iniciando WebSocket relay en puerto 8889..."
uv run "$DIR/ws_relay.py" > "$LOG/ws.log" 2>&1 &
WS_PID=$!
sleep 1

# Verificar WS
if lsof -i :8889 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "  ✅ WS Relay OK  (ws://localhost:8889)"
else
    echo "  ❌ ERROR: No pudo iniciar el relay WebSocket"
    exit 1
fi

# 4. Verificar OBS
echo ""
echo "▶ Verificando OBS..."
if lsof -i :4455 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "  ✅ OBS WebSocket detectado en puerto 4455"
else
    echo "  ⚠️  OBS NO está abierto todavía."
    echo "     Abre OBS primero y vuelve a correr este script."
    echo ""
    echo "  (Los servidores HTTP y WS ya arrancaron — solo falta OBS)"
fi

echo ""
echo "═══════════════════════════════════════════"
echo "  Panel de control:"
echo "  http://localhost:8888/control_remoto.html"
echo "═══════════════════════════════════════════"
echo ""
echo "  PIDs activos:"
echo "    HTTP server  → $HTTP_PID"
echo "    WS relay     → $WS_PID"
echo ""
echo "  Para detener todo: Ctrl+C o ejecuta:"
echo "    pkill -f 'http.server 8888' && pkill -f ws_relay.py"
echo ""

# Guardar PIDs para referencia
echo "$HTTP_PID" > "$LOG/http.pid"
echo "$WS_PID"  > "$LOG/ws.pid"

# Mantener el script activo mostrando logs
echo "── Logs en vivo (Ctrl+C para salir) ──"
tail -f "$LOG/http.log" "$LOG/ws.log"
