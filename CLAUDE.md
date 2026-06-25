# CLAUDE.md — OBS Overlays Futbol

Sistema de overlays en vivo para transmisiones de futbol con OBS.
Cada subcarpeta es un **perfil/coleccion independiente** con sus propios equipos, colores y puertos.

## Estructura del repositorio

```
OBS-overlays-futbol/
  original/     <- Perfil original (Avila Fisioterapia, puertos 8888/8889)
  SRYiyo/       <- Robles Futbol, Semifinal de Ida (puertos 8890/8891)
  shared/       <- Fuente unica: control_remoto.html, ws-client.js, gen_config.py
  tests/        <- Suite Playwright E2E (marcador, control_remoto, penalty)
  CLAUDE.md     <- Este archivo
```

## SSOT — profile.json es la unica fuente de verdad

Cada perfil se edita SOLO en su `profile.json` (equipos, colores, puertos, logos,
`features`, `scenePrefix`, `scenes`). Lo demas se deriva:

```
profile.json ──(shared/gen_config.py, corre en iniciar_stream)──> config.js   [GENERADO, gitignoreado]
profile.json ──(ws_relay.py)──> SCENE_MAP        profile.json ──(setup_obs.py)──> escenas OBS
profile.json ──(ecosystem.config.js)──> puertos PM2
```

- **NO edites `config.js`**: es generado en cada arranque (igual que `control_remoto.html`).
  El token real sigue en `config.local.js` (gitignoreado), cargado despues de `config.js`.
- Cambiar equipos/colores/escenas = un solo archivo (`profile.json`) por perfil.

## Calidad y tests

```bash
npm install && npx playwright install chromium   # una vez
npm test            # 15 tests E2E headless (no requiere OBS)
npm run lint        # Biome (JS/JSON)        uvx ruff check .   # Python
bash verificar.sh <perfil>    #  /  .\verificar.ps1 <perfil>   (chequeo de salud)
```

Reproducibilidad Mac/Windows: ver `MULTISYSTEM.md`.

## Primer uso en una maquina nueva

### Mac
```bash
# 1. Clonar
git clone https://github.com/Ol3Ramirez/OBS-overlays-futbol
cd OBS-overlays-futbol/SRYiyo

# 2. Instalar uv si no esta instalado
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Configurar password de OBS (una sola vez)
cp .env.example .env
nano .env   # Escribe: OBS_WS_PASSWORD=tu_password_de_obs

# 3b. Configurar token del WebSocket relay (solo perfiles con auth, ej. SRYiyo)
cp profile.local.json.example profile.local.json
cp config.local.js.example config.local.js
python3 -c "import secrets; print(secrets.token_hex(16))"   # genera el token
# Pega el MISMO valor como "wsToken" en profile.local.json y como WS_TOKEN en config.local.js

# 4. Arrancar servidores
bash iniciar_stream.sh

# 5. Configurar OBS (crear escenas automaticamente)
uv run setup_obs.py

# 6. Abrir panel de control en Chrome
open http://localhost:8890/control_remoto.html
```

### Windows (PowerShell 7)
```powershell
# 1. Clonar
git clone https://github.com/Ol3Ramirez/OBS-overlays-futbol
cd OBS-overlays-futbol\SRYiyo

# 2. Instalar uv si no esta instalado
winget install --id=astral-sh.uv -e

# 3. Configurar password de OBS (una sola vez)
copy .env.example .env
notepad .env   # Escribe: OBS_WS_PASSWORD=tu_password_de_obs

# 3b. Configurar token del WebSocket relay (solo perfiles con auth, ej. SRYiyo)
copy profile.local.json.example profile.local.json
copy config.local.js.example config.local.js
python -c "import secrets; print(secrets.token_hex(16))"
# Pega el MISMO valor como "wsToken" en profile.local.json y como WS_TOKEN en config.local.js

# 4. Arrancar servidores
.\iniciar_stream.ps1

# 5. Configurar OBS (crear escenas automaticamente)
uv run setup_obs.py

# 6. Abrir panel de control en Chrome
start http://localhost:8890/control_remoto.html
```

---

## Diferencias Mac vs Windows

| Aspecto | Mac (`iniciar_stream.sh`) | Windows (`iniciar_stream.ps1`) |
|---------|--------------------------|-------------------------------|
| Python | `python3` | `python` (o `python3` si esta en PATH) |
| Verificar puerto | `lsof -i :PORT -sTCP:LISTEN` | `netstat -ano \| Select-String "LISTENING"` |
| Matar proceso por puerto | `lsof -ti :PORT \| xargs kill -9` | `Stop-Process -Id ([int]$procId)` |
| Redirigir logs | Un archivo: `> file 2>&1` | Dos archivos separados (stdout != stderr) |
| Path con espacios | Funciona con `"$DIR/script.py"` | Requiere `"\"$path\""` para uv |
| Git GPG signing | Funciona normalmente | Requiere `-c commit.gpgsign=false` |
| Arrancar OBS | Abrir OBS.app manualmente | Abrir OBS Studio manualmente |

---

## Password de OBS WebSocket

El password **nunca se hardcodea en el codigo**. `setup_obs.py` lo lee en este orden:

1. Variable de entorno: `export OBS_WS_PASSWORD=tu_password`
2. Archivo `.env` en la carpeta del perfil (gitignoreado)
3. Prompt interactivo — te lo pide al correr el script y te ofrece guardarlo

**Encontrar el password en OBS:**
OBS -> Herramientas -> Ajustes del servidor WebSocket -> Mostrar informacion de conexion

---

## Token del WebSocket relay (perfiles con auth, ej. SRYiyo)

El token **nunca se commitea** — `profile.json` y `config.js` solo tienen los
nombres de los campos (`wsToken` / `WS_TOKEN`), nunca el valor real. El valor
real vive en dos archivos gitignoreados, uno por lado (servidor y navegador),
que cada quien crea en su propia maquina:

| Lado | Archivo real (gitignoreado) | Plantilla versionada |
|------|------------------------------|------------------------|
| Servidor (`ws_relay.py`) | `<perfil>/profile.local.json` | `profile.local.json.example` |
| Navegador (`control_remoto.html`) | `<perfil>/config.local.js` | `config.local.js.example` |

`ws_relay.py` carga `profile.json` y le superpone `profile.local.json` si existe.
`control_remoto.html` carga `config.js` y luego `config.local.js` (que sobreescribe
`WS_TOKEN`). Sin estos archivos el relay arranca sin token — valido solo en `127.0.0.1`.

```bash
cd <perfil>   # ej. SRYiyo
cp profile.local.json.example profile.local.json
cp config.local.js.example config.local.js
python3 -c "import secrets; print(secrets.token_hex(16))"
# Pega el MISMO valor en "wsToken" (profile.local.json) y WS_TOKEN (config.local.js)
```

---

## Puertos por perfil

| Perfil | HTTP | WS Relay | OBS WS |
|--------|------|----------|--------|
| `original/` | 8888 | 8889 | 4455 |
| `SRYiyo/` | 8890 | 8891 | 4455 |
| Proximo perfil | 8892 | 8893 | 4455 |

El puerto 4455 (OBS WebSocket) es compartido — todos los perfiles controlan el mismo OBS.

---

## Arquitectura

```
Chrome / Celular
  | ws://localhost:8891
  v
ws_relay.py (puerto 8891, solo 127.0.0.1)
  | broadcast
  v
OBS Browser Sources (puerto 8890)
  marcador.html       <- scoreboard + reloj
  evento_jugador.html <- goles, tarjetas, cambios
  alineacion.html     <- formacion del equipo
  entrevista.html     <- lower third + ticker
  intro.html          <- countdown de inicio
  medio_tiempo.html   <- pantalla de descanso

control_remoto.html   <- panel de control (no es source de OBS)
```

---

## Crear un nuevo perfil

```bash
# Mac
cp -r SRYiyo/ NuevoPerfil/
# Editar NuevoPerfil/config.js: equipos, colores, puertos (+2)
# Editar NuevoPerfil/ws_relay.py: cambiar 8891 -> 8893
bash NuevoPerfil/iniciar_stream.sh

# Windows
xcopy SRYiyo\ NuevoPerfil\ /E /I
# Editar NuevoPerfil\config.js y ws_relay.py
.\NuevoPerfil\iniciar_stream.ps1
```

Solo hay que editar `config.js` — todos los overlays leen los datos desde ahi.

> **Si `SRYiyo/profile.local.json` o `config.local.js` ya existian** (token de otro
> partido), el `cp -r` los copia tal cual. Regenera el token para el nuevo perfil
> en vez de reusar el viejo — ver [Token del WebSocket relay](#token-del-websocket-relay-perfiles-con-auth-ej-sryiyo).

---

## Panel de control compartido (`shared/`)

`control_remoto.html` y `ws-client.js` ya NO se editan dentro de cada perfil.
Viven una sola vez en `shared/` y cada `iniciar_stream.sh`/`.ps1` copia una version
fresca a la carpeta del perfil antes de levantar el servidor HTTP — asi un cambio
en `shared/control_remoto.html` se distribuye a todos los perfiles en el siguiente arranque.

- **Editar SOLO** `shared/control_remoto.html` / `shared/ws-client.js`.
- Las copias `original/control_remoto.html`, `SRYiyo/control_remoto.html` (y sus
  `ws-client.js`) son generadas — estan en `.gitignore`, no se commitean.
- Las diferencias entre perfiles (roster visitante, penales, deshacer+historial,
  marcador global IDA, QR de acceso desde cancha) son **feature flags en `config.js`**:
  `ENABLE_AWAY_ROSTER`, `ENABLE_PENALTIES`, `ENABLE_UNDO`, `ENABLE_IDA_SCORE`, `ENABLE_QR`.
  `original/` las tiene todas en `false` (panel minimo); `SRYiyo/` las tiene en `true`.
- Un perfil nuevo (`cp -r`) hereda el paso de sync automaticamente — no hay que tocar nada.

---

## OBS WebSocket MCP (control desde Claude)

Configurado en `~/.claude.json` -> `mcpServers.obs`.
Permite decirle a Claude "cambia a escena Partido" o "activa el marcador" directamente.
Para activarlo: reiniciar Claude Code despues de agregar el MCP.
