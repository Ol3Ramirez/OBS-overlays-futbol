# launch-chrome-fb.ps1
# Abre Chrome con tu sesión de Facebook y puerto de debug 9222
# Esto permite que el MCP chrome-devtools tome control de TU Chrome real
# (con Facebook ya iniciado) para publicar Reels y posts automáticamente.

$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chromePath)) {
    $chromePath = "$env:LOCALAPPDATA\Google\Chrome\User Data\..\Application\chrome.exe"
}
if (-not (Test-Path $chromePath)) {
    Write-Error "No se encontró Chrome. Verifica la ruta."
    exit 1
}

$userDataDir = "$env:LOCALAPPDATA\Google\Chrome\User Data"

Write-Host ""
Write-Host "Lanzando Chrome con perfil real + debug port 9222..."
Write-Host "Facebook se abrirá ya con tu sesión iniciada."
Write-Host ""

Start-Process -FilePath $chromePath -ArgumentList @(
    "--remote-debugging-port=9222",
    "--user-data-dir=`"$userDataDir`"",
    "--profile-directory=Default",
    "--no-first-run",
    "--restore-last-session",
    "https://www.facebook.com/WIFITLX"
)

Write-Host "✓ Chrome abierto en puerto 9222."
Write-Host ""
Write-Host "El MCP chrome-devtools puede tomar control ahora."
Write-Host "Dile a Claude: 'usa chrome-devtools para publicar en Facebook'"
Write-Host ""
Write-Host "NOTA: Mantén esta ventana de Chrome abierta durante la sesión de publicación."
Write-Host "Ciérrala normalmente cuando termines."
