# iniciar_stream.ps1 -- SRYiyo (Windows PowerShell 7)
#
# Principios aplicados:
#   SSOT       -- puertos leidos desde profile.json
#   Idempotente -- mata procesos previos antes de arrancar (re-ejecutar es seguro)
#   Atomico    -- si el WS relay falla, mata el HTTP server antes de salir
#   Fail-fast  -- verifica puertos activos despues de cada arranque
#
# Uso: .\iniciar_stream.ps1

$ErrorActionPreference = "Stop"

$DIR  = $PSScriptRoot
$LOG  = Join-Path $DIR "logs"
if (-not (Test-Path $LOG)) { New-Item -ItemType Directory -Force $LOG | Out-Null }

# Leer puertos desde profile.json (SSOT)
$profilePath = Join-Path $DIR "profile.json"
if (-not (Test-Path $profilePath)) {
    Write-Host "[FATAL] profile.json no encontrado en $profilePath" -ForegroundColor Red
    exit 1
}
try {
    $profile = Get-Content $profilePath -Raw | ConvertFrom-Json
} catch {
    Write-Host "[FATAL] profile.json invalido: $_" -ForegroundColor Red
    exit 1
}
$HTTP_PORT   = $profile.httpPort
$WS_PORT     = $profile.wsPort
$PROFILE_NAME = $profile.name

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  $PROFILE_NAME -- Iniciar Stream" -ForegroundColor White
Write-Host "  HTTP: $HTTP_PORT  |  WS: $WS_PORT" -ForegroundColor Yellow
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

function Test-Port {
    param([int]$port)
    $r = netstat -ano | Select-String (":$port\s") | Select-String "LISTENING"
    return ($null -ne $r)
}

function Kill-Port {
    param([int]$port)
    $lines = netstat -ano | Select-String (":$port\s") | Select-String "LISTENING"
    foreach ($line in $lines) {
        $parts = ($line.ToString() -split '\s+')
        $procId = $parts[-1]
        if ($procId -match '^\d+$') {
            try { Stop-Process -Id ([int]$procId) -Force -ErrorAction SilentlyContinue } catch {}
        }
    }
}

# Idempotencia: matar procesos anteriores
Write-Host "Limpiando puertos $HTTP_PORT / $WS_PORT..." -ForegroundColor DarkGray
Kill-Port $HTTP_PORT
Kill-Port $WS_PORT
Start-Sleep -Seconds 1

# HTTP server
Write-Host "Iniciando HTTP en puerto $HTTP_PORT..." -ForegroundColor DarkGray
$httpLog = Join-Path $LOG "http.log"
$httpErr = Join-Path $LOG "http.err"
$httpJob = $null

foreach ($cmd in @("python", "python3")) {
    try {
        $httpJob = Start-Process -FilePath $cmd `
            -ArgumentList @("-m", "http.server", "$HTTP_PORT") `
            -WorkingDirectory $DIR `
            -RedirectStandardOutput $httpLog `
            -RedirectStandardError  $httpErr `
            -PassThru -WindowStyle Hidden
        break
    } catch { }
}

if (-not $httpJob) {
    Write-Host "  [FALLO] No se encontro python o python3" -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 2

if (Test-Port $HTTP_PORT) {
    Write-Host "  OK HTTP -> http://localhost:$HTTP_PORT" -ForegroundColor Green
} else {
    Write-Host "  [FALLO] No pudo iniciar HTTP server" -ForegroundColor Red
    Stop-Process -Id $httpJob.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# WS relay
Write-Host "Iniciando WS relay en puerto $WS_PORT..." -ForegroundColor DarkGray
$wsScript = Join-Path $DIR "ws_relay.py"
$wsLog    = Join-Path $LOG "ws.log"
$wsErr    = Join-Path $LOG "ws.err"

$wsJob = Start-Process -FilePath "uv" `
    -ArgumentList @("run", "`"$wsScript`"") `
    -RedirectStandardOutput $wsLog `
    -RedirectStandardError  $wsErr `
    -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 3

if (Test-Port $WS_PORT) {
    Write-Host "  OK WS Relay -> ws://localhost:$WS_PORT" -ForegroundColor Green
} else {
    Write-Host "  [FALLO] No pudo iniciar WS relay" -ForegroundColor Red
    # Atomico: mata HTTP antes de salir para no dejar estado corrupto
    Stop-Process -Id $httpJob.Id -Force -ErrorAction SilentlyContinue
    exit 1
}

# OBS check (no bloquea)
Write-Host ""
Write-Host "Verificando OBS WebSocket (puerto 4455)..." -ForegroundColor DarkGray
if (Test-Port 4455) {
    Write-Host "  OK OBS WebSocket detectado" -ForegroundColor Green
} else {
    Write-Host "  AVISO: OBS no detectado -- abrelo antes de usar el panel" -ForegroundColor Yellow
}

# Guardar PIDs
$httpJob.Id | Out-File (Join-Path $LOG "http.pid") -Encoding utf8
$wsJob.Id   | Out-File (Join-Path $LOG "ws.pid")   -Encoding utf8

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Panel: http://localhost:$HTTP_PORT/control_remoto.html" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Para detener: Stop-Process -Id $($httpJob.Id),$($wsJob.Id) -Force" -ForegroundColor DarkGray
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "-- Log WS en vivo (Ctrl+C para salir) --" -ForegroundColor DarkGray
Get-Content $wsLog -Wait
