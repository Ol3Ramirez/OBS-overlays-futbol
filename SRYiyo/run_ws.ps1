# run_ws.ps1 — Wrapper Windows para PM2
# PM2 llama este script directamente; uv run maneja las dependencias (PEP 723)
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
uv run "$dir\ws_relay.py"
