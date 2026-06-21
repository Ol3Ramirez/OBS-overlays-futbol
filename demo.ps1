# demo.ps1 -- Levanta ambos perfiles y verifica overlays en Chrome
# Uso:        .\demo.ps1          (arrancar)
# Detener:    .\demo.ps1 -stop

param([switch]$stop)

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$LOG  = Join-Path $ROOT "logs-demo"

$PROFILES = @(
    @{ name = "original"; dir = Join-Path $ROOT "original"; http = 8888; ws = 8889 },
    @{ name = "SRYiyo";   dir = Join-Path $ROOT "SRYiyo";   http = 8890; ws = 8891 }
)

function Test-Port { param([int]$p)
    return ($null -ne (netstat -ano | Select-String (":$p\s") | Select-String "LISTENING"))
}

function Kill-Port { param([int]$p)
    $lines = netstat -ano | Select-String (":$p\s") | Select-String "LISTENING"
    foreach ($line in $lines) {
        $parts = ($line.ToString() -split '\s+')
        $pid   = $parts[-1]
        if ($pid -match '^\d+$') {
            try { Stop-Process -Id ([int]$pid) -Force -ErrorAction SilentlyContinue } catch {}
        }
    }
}

# ── Modo detener ─────────────────────────────────────────────────────────────
if ($stop) {
    Write-Host ""
    Write-Host "Deteniendo demo..." -ForegroundColor Yellow
    foreach ($p in $PROFILES) {
        Kill-Port $p.http
        Kill-Port $p.ws
        Write-Host "  $($p.name): puertos $($p.http)/$($p.ws) liberados" -ForegroundColor Green
    }
    Write-Host ""
    exit 0
}

# ── Arranque ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DEMO -- OBS Overlays (ambos perfiles)" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $LOG)) { New-Item -ItemType Directory -Force $LOG | Out-Null }

foreach ($p in $PROFILES) {
    Write-Host "[$($p.name)]  HTTP $($p.http)  WS $($p.ws)" -ForegroundColor Yellow

    Kill-Port $p.http
    Kill-Port $p.ws

    # HTTP server
    $hJob = $null
    foreach ($cmd in @("python", "python3")) {
        try {
            $hJob = Start-Process -FilePath $cmd `
                -ArgumentList @("-m", "http.server", "$($p.http)") `
                -WorkingDirectory $p.dir `
                -RedirectStandardOutput (Join-Path $LOG "$($p.name)-http.log") `
                -RedirectStandardError  (Join-Path $LOG "$($p.name)-http.err") `
                -PassThru -WindowStyle Hidden
            break
        } catch {}
    }
    if (-not $hJob) {
        Write-Host "  [FALLO] python no encontrado en PATH" -ForegroundColor Red
        continue
    }

    # WS relay
    $wsScript = Join-Path $p.dir "ws_relay.py"
    $wJob = Start-Process -FilePath "uv" `
        -ArgumentList @("run", "`"$wsScript`"") `
        -RedirectStandardOutput (Join-Path $LOG "$($p.name)-ws.log") `
        -RedirectStandardError  (Join-Path $LOG "$($p.name)-ws.err") `
        -PassThru -WindowStyle Hidden

    $hJob.Id | Out-File (Join-Path $LOG "$($p.name)-http.pid") -Encoding utf8
    $wJob.Id  | Out-File (Join-Path $LOG "$($p.name)-ws.pid")  -Encoding utf8
}

Write-Host ""
Write-Host "Esperando arranque (3s)..." -ForegroundColor DarkGray
Start-Sleep -Seconds 3

# ── Verificacion de puertos ───────────────────────────────────────────────────
Write-Host ""
Write-Host "Estado de servicios:" -ForegroundColor White
$allOk = $true
foreach ($p in $PROFILES) {
    $hOk = Test-Port $p.http
    $wOk = Test-Port $p.ws
    if (-not $hOk -or -not $wOk) { $allOk = $false }
    $hTxt  = if ($hOk) { "OK" } else { "FALLO" }
    $wTxt  = if ($wOk) { "OK" } else { "FALLO" }
    $hClr  = if ($hOk) { "Green" } else { "Red" }
    $wClr  = if ($wOk) { "Green" } else { "Red" }
    Write-Host "  $($p.name)" -ForegroundColor Cyan
    Write-Host "    HTTP :$($p.http)  $hTxt" -ForegroundColor $hClr
    Write-Host "    WS   :$($p.ws)  $wTxt"   -ForegroundColor $wClr
}
$obsOk = Test-Port 4455
$obsTxt = if ($obsOk) { "OK" } else { "NO DETECTADO (abre OBS)" }
$obsClr = if ($obsOk) { "Green" } else { "Yellow" }
Write-Host "  OBS WebSocket :4455  $obsTxt" -ForegroundColor $obsClr

# ── Abrir Chrome con panels + overlays clave ──────────────────────────────────
$urls = @(
    "http://localhost:8888/control_remoto.html",
    "http://localhost:8888/marcador.html",
    "http://localhost:8888/intro.html",
    "http://localhost:8890/control_remoto.html",
    "http://localhost:8890/marcador.html",
    "http://localhost:8890/intro.html"
)

Write-Host ""
Write-Host "Abriendo Chrome ($($urls.Count) tabs)..." -ForegroundColor DarkGray

$chromePaths = @(
    "$env:PROGRAMFILES\Google\Chrome\Application\chrome.exe",
    "$env:PROGRAMFILES(X86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)
$chrome = $chromePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($chrome) {
    # Primer tab + nuevos tabs para los demas
    $firstUrl  = $urls[0]
    $extraArgs = ($urls[1..($urls.Length - 1)] | ForEach-Object { "--new-tab $_" }) -join " "
    Start-Process $chrome "$firstUrl $extraArgs"
    Write-Host "  OK" -ForegroundColor Green
} else {
    Write-Host "  Chrome no encontrado -- abrir manualmente:" -ForegroundColor Yellow
    $urls | ForEach-Object { Write-Host "    $_" -ForegroundColor White }
}

# ── Resumen final ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
if ($allOk) {
    Write-Host "  DEMO ACTIVA  --  todo OK" -ForegroundColor Green
} else {
    Write-Host "  DEMO con errores  --  revisar arriba" -ForegroundColor Red
}
Write-Host ""
Write-Host "  original  ->  http://localhost:8888/control_remoto.html" -ForegroundColor Yellow
Write-Host "  SRYiyo    ->  http://localhost:8890/control_remoto.html" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Logs:       $LOG" -ForegroundColor DarkGray
Write-Host "  Detener:    .\demo.ps1 -stop" -ForegroundColor DarkGray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
