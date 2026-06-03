# ─────────────────────────────────────────────────────
#  SRYiyo — iniciar_stream.ps1  (Windows)
#  Idempotente: mata procesos anteriores antes de arrancar.
#  Uso: .\iniciar_stream.ps1
# ─────────────────────────────────────────────────────

$DIR  = $PSScriptRoot
$LOG  = Join-Path $DIR "logs"
$HTTP_PORT = 8890
$WS_PORT   = 8891

if (-not (Test-Path $LOG)) { New-Item -ItemType Directory -Force $LOG | Out-Null }

Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   SRYIYO — ROBLES FÚTBOL"                          -ForegroundColor White
Write-Host "   PROVEEDORA ROBLES vs HERMANOS OSORIO"            -ForegroundColor Yellow
Write-Host "   SEMIFINAL DE IDA"                                 -ForegroundColor Yellow
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ── Función: verificar si un puerto está ocupado ──
function Test-Port($port) {
    $r = netstat -ano | Select-String ":$port\s" | Select-String "LISTENING"
    return $null -ne $r
}

# ── Función: matar proceso por puerto ──
function Kill-Port($port) {
    $lines = netstat -ano | Select-String ":$port\s" | Select-String "LISTENING"
    foreach ($line in $lines) {
        $pid = ($line -split '\s+')[-1]
        if ($pid -match '^\d+$') {
            try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch {}
        }
    }
}

# 1. Matar procesos anteriores
Write-Host "▶ Limpiando puertos $HTTP_PORT / $WS_PORT..." -ForegroundColor DarkGray
Kill-Port $HTTP_PORT
Kill-Port $WS_PORT
Start-Sleep -Seconds 1

# 2. Servidor HTTP
Write-Host "▶ Iniciando HTTP en puerto $HTTP_PORT..." -ForegroundColor DarkGray
$httpLog = Join-Path $LOG "http.log"
$httpJob = Start-Process python3 -ArgumentList "-m http.server $HTTP_PORT" `
    -WorkingDirectory $DIR -RedirectStandardOutput $httpLog `
    -RedirectStandardError $httpLog -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 1

if (Test-Port $HTTP_PORT) {
    Write-Host "  ✅ HTTP OK  → http://localhost:$HTTP_PORT" -ForegroundColor Green
} else {
    Write-Host "  ❌ ERROR: No pudo iniciar el servidor HTTP" -ForegroundColor Red
    exit 1
}

# 3. WebSocket relay
Write-Host "▶ Iniciando WS relay en puerto $WS_PORT..." -ForegroundColor DarkGray
$wsLog = Join-Path $LOG "ws.log"
$wsScript = Join-Path $DIR "ws_relay.py"
$wsJob = Start-Process uv -ArgumentList "run `"$wsScript`"" `
    -RedirectStandardOutput $wsLog -RedirectStandardError $wsLog `
    -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2

if (Test-Port $WS_PORT) {
    Write-Host "  ✅ WS Relay OK  → ws://localhost:$WS_PORT" -ForegroundColor Green
} else {
    Write-Host "  ❌ ERROR: No pudo iniciar el relay WebSocket" -ForegroundColor Red
    exit 1
}

# 4. Verificar OBS
Write-Host ""
Write-Host "▶ Verificando OBS WebSocket (puerto 4455)..." -ForegroundColor DarkGray
if (Test-Port 4455) {
    Write-Host "  ✅ OBS WebSocket detectado" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  OBS NO está abierto — ábrelo antes de usar el panel" -ForegroundColor Yellow
}

# Guardar PIDs
$httpJob.Id | Out-File (Join-Path $LOG "http.pid") -Encoding utf8
$wsJob.Id   | Out-File (Join-Path $LOG "ws.pid")   -Encoding utf8

Write-Host ""
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Panel de control:" -ForegroundColor White
Write-Host "  http://localhost:$HTTP_PORT/control_remoto.html" -ForegroundColor Yellow
Write-Host ""
Write-Host "  PIDs: HTTP=$($httpJob.Id)  WS=$($wsJob.Id)" -ForegroundColor DarkGray
Write-Host "  Para detener todos los procesos:" -ForegroundColor DarkGray
Write-Host "    Stop-Process -Id $($httpJob.Id),$($wsJob.Id) -Force" -ForegroundColor DarkGray
Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Presiona Ctrl+C para salir de este script (los servidores siguen corriendo)" -ForegroundColor DarkGray
Write-Host ""

# Tail de logs en tiempo real
Get-Content $wsLog -Wait
