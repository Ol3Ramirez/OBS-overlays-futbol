# verificar.ps1 -- Chequeo de salud de un perfil (Windows PowerShell 7).
# Equivalente exacto de verificar.sh (Mac/Linux). Mismo formato de salida.
#
# Uso: .\verificar.ps1 [original|SRYiyo]   (por defecto: SRYiyo)

param([string]$Profile = "SRYiyo")

$DIR_ROOT = $PSScriptRoot
$PDIR     = Join-Path $DIR_ROOT $Profile
$script:FAILS = 0

function Ok   ($m) { Write-Host "[OK]  $m" -ForegroundColor Green }
function Warn ($m) { Write-Host "[!]   $m" -ForegroundColor Yellow }
function Bad  ($m) { Write-Host "[X]   $m" -ForegroundColor Red; $script:FAILS++ }

Write-Host "==================================================="
Write-Host "  Verificacion del perfil: $Profile"
Write-Host "==================================================="

# Interprete python segun plataforma (Windows suele tener solo `python`).
$PY = $null
foreach ($c in @("python", "python3")) {
    if (Get-Command $c -ErrorAction SilentlyContinue) { $PY = $c; break }
}

# 1. Dependencias
if ($PY) { Ok "$PY disponible" } else { Bad "python NO encontrado" }
if (Get-Command uv -ErrorAction SilentlyContinue) { Ok "uv disponible" } else { Warn "uv NO encontrado (necesario para ws_relay.py)" }

# 2. profile.json existe y es valido
$profilePath = Join-Path $PDIR "profile.json"
if (-not (Test-Path $profilePath)) {
    Bad "profile.json no existe en $PDIR"
    Write-Host ""; Write-Host "Resultado: $script:FAILS fallo(s)."; exit 1
}
try {
    $profile = Get-Content $profilePath -Raw | ConvertFrom-Json
    Ok "profile.json valido"
} catch {
    Bad "profile.json invalido (JSON corrupto)"
}
$HTTP_PORT = $profile.httpPort
$WS_PORT   = $profile.wsPort

# 3. config.js se regenera desde profile.json (SSOT)
if ($PY) {
    & $PY (Join-Path $DIR_ROOT "shared/gen_config.py") $PDIR | Out-Null
    if ((Test-Path (Join-Path $PDIR "config.js"))) { Ok "config.js se genera desde profile.json" }
    else { Bad "no se pudo generar config.js" }
}

# 4. Puertos escuchando
function Test-Port { param([int]$port)
    $null -ne (netstat -ano | Select-String (":$port\s") | Select-String "LISTENING")
}
if ($HTTP_PORT -and (Test-Port $HTTP_PORT)) { Ok "HTTP escuchando en $HTTP_PORT" } else { Warn "HTTP no escucha en $HTTP_PORT (arranca con iniciar_stream.ps1)" }
if ($WS_PORT   -and (Test-Port $WS_PORT))   { Ok "WS relay escuchando en $WS_PORT" } else { Warn "WS relay no escucha en $WS_PORT" }

# 5. OBS (informativo, no bloquea)
if (Test-Port 4455) { Ok "OBS WebSocket (4455) detectado" } else { Warn "OBS no detectado en 4455 (abrelo antes del partido)" }

Write-Host "==================================================="
if ($script:FAILS -eq 0) {
    Write-Host "Resultado: TODO OK ($Profile)" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Resultado: $script:FAILS fallo(s) critico(s) en $Profile" -ForegroundColor Red
    exit 1
}
