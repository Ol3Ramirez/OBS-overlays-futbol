# SRYiyo -- iniciar_stream.ps1 (Windows)
# Idempotente: mata procesos anteriores antes de arrancar.
# Uso: .\iniciar_stream.ps1

$DIR       = $PSScriptRoot
$LOG       = Join-Path $DIR "logs"
$HTTP_PORT = 8890
$WS_PORT   = 8891

if (-not (Test-Path $LOG)) { New-Item -ItemType Directory -Force $LOG | Out-Null }

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  SRYIYO -- ROBLES FUTBOL" -ForegroundColor White
Write-Host "  PROVEEDORA ROBLES vs HERMANOS OSORIO" -ForegroundColor Yellow
Write-Host "  SEMIFINAL DE IDA" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

function Test-Port {
    param($port)
    $r = netstat -ano | Select-String (":$port\s") | Select-String "LISTENING"
    return ($null -ne $r)
}

function Kill-Port {
    param($port)
    $lines = netstat -ano | Select-String (":$port\s") | Select-String "LISTENING"
    foreach ($line in $lines) {
        $parts = ($line.ToString() -split '\s+')
        $procId = $parts[-1]
        if ($procId -match '^\d+$') {
            try { Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue } catch {}
        }
    }
}

Write-Host "Limpiando puertos $HTTP_PORT / $WS_PORT..." -ForegroundColor DarkGray
Kill-Port $HTTP_PORT
Kill-Port $WS_PORT
Start-Sleep -Seconds 1

# HTTP server
Write-Host "Iniciando HTTP en puerto $HTTP_PORT..." -ForegroundColor DarkGray
$httpLog = Join-Path $LOG "http.log"
$httpErr = Join-Path $LOG "http.err"
$httpJob = Start-Process -FilePath "python" `
    -ArgumentList @("-m", "http.server", "$HTTP_PORT") `
    -WorkingDirectory $DIR `
    -RedirectStandardOutput $httpLog `
    -RedirectStandardError $httpErr `
    -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 2

if (Test-Port $HTTP_PORT) {
    Write-Host "  OK HTTP -> http://localhost:$HTTP_PORT" -ForegroundColor Green
} else {
    Write-Host "  ERROR: No pudo iniciar HTTP. Intentando con python3..." -ForegroundColor Yellow
    $httpJob = Start-Process -FilePath "python3" `
        -ArgumentList @("-m", "http.server", "$HTTP_PORT") `
        -WorkingDirectory $DIR `
        -RedirectStandardOutput $httpLog `
        -RedirectStandardError $httpErr `
        -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 2
    if (Test-Port $HTTP_PORT) {
        Write-Host "  OK HTTP -> http://localhost:$HTTP_PORT" -ForegroundColor Green
    } else {
        Write-Host "  FALLO: No pudo iniciar el servidor HTTP" -ForegroundColor Red
        exit 1
    }
}

# WS relay
Write-Host "Iniciando WS relay en puerto $WS_PORT..." -ForegroundColor DarkGray
$wsScript = Join-Path $DIR "ws_relay.py"
$wsLog    = Join-Path $LOG "ws.log"
$wsErr    = Join-Path $LOG "ws.err"
$wsJob = Start-Process -FilePath "uv" `
    -ArgumentList @("run", "`"$wsScript`"") `
    -RedirectStandardOutput $wsLog `
    -RedirectStandardError $wsErr `
    -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 3

if (Test-Port $WS_PORT) {
    Write-Host "  OK WS Relay -> ws://localhost:$WS_PORT" -ForegroundColor Green
} else {
    Write-Host "  FALLO: No pudo iniciar el relay WebSocket" -ForegroundColor Red
    exit 1
}

# OBS check
Write-Host ""
Write-Host "Verificando OBS (puerto 4455)..." -ForegroundColor DarkGray
if (Test-Port 4455) {
    Write-Host "  OK OBS WebSocket detectado" -ForegroundColor Green
} else {
    Write-Host "  AVISO: OBS no esta abierto -- abrelo antes de usar el panel" -ForegroundColor Yellow
}

if ($httpJob) { $httpJob.Id | Out-File (Join-Path $LOG "http.pid") -Encoding utf8 }
if ($wsJob)   { $wsJob.Id   | Out-File (Join-Path $LOG "ws.pid")   -Encoding utf8 }

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Panel de control:" -ForegroundColor White
Write-Host "  http://localhost:$HTTP_PORT/control_remoto.html" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Para detener los servidores cierra esta terminal" -ForegroundColor DarkGray
Write-Host "  o ejecuta: Stop-Process -Id $($httpJob.Id),$($wsJob.Id) -Force" -ForegroundColor DarkGray
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# Tail del log WS en vivo
Write-Host "-- Log WS en vivo (Ctrl+C para salir) --" -ForegroundColor DarkGray
Get-Content $wsLog -Wait
