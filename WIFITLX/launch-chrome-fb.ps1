# launch-chrome-fb.ps1
# Lanza Chrome con perfil real + puerto de debug 9222
# IMPORTANTE: usar -ArgumentList como string unico para que el path con espacios
# llegue completo a Chrome. Con array, PowerShell trunca en el primer espacio.

$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chromePath)) {
    $chromePath = "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
}
if (-not (Test-Path $chromePath)) {
    Write-Error "No se encontro Chrome. Verifica la ruta."
    exit 1
}

$userDataDir = "$env:LOCALAPPDATA\Google\Chrome\User Data"

Write-Host ""
Write-Host "1. Cerrando Chrome existente..."
Get-Process -Name "chrome" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

Write-Host "2. Limpiando lock files..."
$lockFiles = @(
    "$userDataDir\SingletonLock",
    "$userDataDir\SingletonSocket",
    "$userDataDir\SingletonCookie"
)
foreach ($lock in $lockFiles) {
    if (Test-Path $lock) {
        Remove-Item $lock -Force -ErrorAction SilentlyContinue
        Write-Host "   Eliminado: $(Split-Path $lock -Leaf)"
    }
}

Write-Host "3. Lanzando Chrome con perfil real + debug port 9222..."

# String unico: el path con espacios va entre comillas embebidas
$argString = "--remote-debugging-port=9222 --user-data-dir=`"$userDataDir`" --profile-directory=Default https://www.facebook.com/WIFITLX"

Start-Process -FilePath $chromePath -ArgumentList $argString

Write-Host "Chrome abierto en puerto 9222."
Write-Host "Avisa cuando Chrome este listo."
Write-Host ""
