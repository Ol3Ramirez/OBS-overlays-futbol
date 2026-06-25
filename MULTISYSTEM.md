# MULTISYSTEM — Reproducir el repo en Mac y Windows

Este repo está pensado para clonarse y correr igual en **macOS/Linux** y en **Windows**.
Cada acción tiene su par de scripts equivalentes; este documento lista los requisitos,
las diferencias legítimas entre plataformas y cómo verificar que todo quedó bien.

## Requisitos por sistema

| | macOS / Linux | Windows |
|---|---|---|
| Python | `python3` 3.11+ | `python` 3.11+ (instala con `winget install astral-sh.uv` o python.org) |
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `winget install --id=astral-sh.uv -e` |
| Node (solo para tests/lint) | 18+ | 18+ |
| Shell | bash / zsh | PowerShell 7 |
| OBS | OBS Studio + WebSocket (4455) | OBS Studio + WebSocket (4455) |

## Pares de scripts (paridad)

| Acción | macOS / Linux | Windows |
|---|---|---|
| Arrancar un perfil | `bash <perfil>/iniciar_stream.sh` | `.\<perfil>\iniciar_stream.ps1` |
| Solo WS relay | `bash <perfil>/run_ws.sh` | `.\<perfil>\run_ws.ps1` |
| Verificar salud | `bash verificar.sh <perfil>` | `.\verificar.ps1 <perfil>` |
| Demo de escenas | `uv run demo_obs.py` | `.\demo.ps1` |
| Generar config.js | `python3 shared/gen_config.py <perfil>` | `python shared\gen_config.py <perfil>` |

> Ambos scripts de arranque hacen lo mismo: copian `control_remoto.html`/`ws-client.js`
> desde `shared/`, **generan `config.js` desde `profile.json`**, levantan HTTP + WS relay,
> verifican puertos y guardan PIDs. Reejecutarlos es idempotente.

## Diferencias legítimas entre plataformas (no son bugs)

| Tema | macOS / Linux | Windows |
|---|---|---|
| Intérprete Python | `python3` | `python` (los scripts prueban `python` y luego `python3`) |
| Ver puerto abierto | `lsof -i :PORT -sTCP:LISTEN` | `netstat -ano \| Select-String LISTENING` |
| Matar por puerto | `lsof -ti :PORT \| xargs kill -9` | `Stop-Process -Id <pid>` |
| Logs | un archivo `> file 2>&1` | stdout/stderr separados (`http.log` + `http.err`) |
| Arrancar Ollama / OBS | manual | manual |

## Verificación (clon nuevo)

```bash
# 1. Clonar y entrar
git clone <repo> && cd OBS-overlays-futbol

# 2. Configurar password OBS + token (una vez por máquina) — ver CLAUDE.md de cada perfil
# 3. Arrancar
bash SRYiyo/iniciar_stream.sh         # Mac/Linux
#  .\SRYiyo\iniciar_stream.ps1        # Windows

# 4. Verificar salud (en otra terminal)
bash verificar.sh SRYiyo              # Mac/Linux
#  .\verificar.ps1 SRYiyo             # Windows
```

`verificar.{sh,ps1}` confirma: python/uv presentes, `profile.json` válido,
`config.js` se regenera desde `profile.json`, y los puertos HTTP/WS/OBS.
Sale con código 0 si no hay fallos críticos (los puertos sin escuchar son avisos,
no fallos: solo significan que aún no arrancaste el stream).

## Tests automatizados (cualquier plataforma)

```bash
npm install            # una vez
npx playwright install chromium
npm test               # 15 tests E2E headless (no requiere OBS)
```
