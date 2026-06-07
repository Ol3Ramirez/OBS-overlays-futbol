# convertir_a_mp4.ps1 — Convierte los MKV grabados por OBS a MP4 con nombres descriptivos

$videosDir = "A:\OLE\Documents\MY CLAUDE CODE\projects\wifi-tlx-content\videos"

$templates = @(
    "05-mundial-promo",
    "06-mexico-juega",
    "07-streaming-compare",
    "01-promo-basica",
    "02-nueva-cobertura",
    "03-velocidad",
    "04-conecta-tlaxcala"
)

$mkvFiles = Get-ChildItem -Path $videosDir -Filter "*.mkv" | Sort-Object Name

if ($mkvFiles.Count -eq 0) {
    Write-Error "No se encontraron archivos .mkv en $videosDir"
    exit 1
}

Write-Host ""
Write-Host "WIFITLX -- Conversion MKV a MP4"
Write-Host "================================"
Write-Host ""

$total = [Math]::Min($mkvFiles.Count, $templates.Count)
$ok = 0
$fail = 0

for ($i = 0; $i -lt $total; $i++) {
    $mkv = $mkvFiles[$i]
    $nombre = $templates[$i]
    $mp4 = Join-Path $videosDir "WIFITLX-$nombre.mp4"

    Write-Host "[$($i+1)/$total] $nombre"
    Write-Host "  Entrada: $($mkv.Name)"
    Write-Host "  Salida:  WIFITLX-$nombre.mp4"

    $ffmpegArgs = "-y -i `"$($mkv.FullName)`" -c:v libx264 -preset fast -crf 18 -vf scale=1080:1080 -c:a aac -b:a 128k -movflags +faststart `"$mp4`""

    $proc = Start-Process -FilePath "ffmpeg" -ArgumentList $ffmpegArgs -Wait -PassThru -NoNewWindow

    if ($proc.ExitCode -eq 0) {
        $sizeMB = [math]::Round((Get-Item $mp4).Length / 1MB, 1)
        Write-Host "  OK - $sizeMB MB"
        $ok++
    } else {
        Write-Host "  ERROR (codigo $($proc.ExitCode))"
        $fail++
    }
    Write-Host ""
}

Write-Host "================================"
Write-Host "Completados: $ok de $total"
if ($fail -gt 0) { Write-Host "Errores: $fail" }
Write-Host "Videos en: $videosDir"
