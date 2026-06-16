# Manual de Operación — OBS Overlays Fútbol

> **Para usar sin internet.** Todo lo que necesitas saber para arrancar, operar y solucionar problemas.

---

## Tabla de contenidos

1. [¿Qué es este sistema?](#qué-es-este-sistema)
2. [Cómo funciona todo (arquitectura simple)](#cómo-funciona-todo)
3. [Instalación — primera vez](#instalación--primera-vez)
4. [Día del partido — arranque rápido](#día-del-partido--arranque-rápido)
5. [Cómo usar el panel de control](#cómo-usar-el-panel-de-control)
6. [Qué hace cada overlay](#qué-hace-cada-overlay)
7. [Cambiar equipos, colores o nombre del partido](#cambiar-equipos-colores-o-nombre-del-partido)
8. [Perfiles disponibles](#perfiles-disponibles)
9. [Crear un nuevo perfil](#crear-un-nuevo-perfil)
10. [Control remoto desde el campo (celular)](#control-remoto-desde-el-campo-celular)
11. [Comandos directos por WebSocket](#comandos-directos-por-websocket)
12. [Solución de problemas](#solución-de-problemas)
13. [Referencia de puertos](#referencia-de-puertos)
14. [Glosario](#glosario)

---

## ¿Qué es este sistema?

Es un conjunto de **overlays (gráficos en pantalla)** que se muestran encima del video de la transmisión en OBS. Incluye:

- **Marcador** con reloj en vivo, nombre de equipos y goles
- **Tarjetas de eventos** — gol, tarjeta amarilla/roja, sustitución
- **Alineación** del equipo con posiciones en el campo
- **Lower thirds** de entrevista con ticker de texto
- **Pantalla de intro** con cuenta regresiva
- **Pantalla de medio tiempo**

Todo se controla **manualmente** desde un panel web (`control_remoto.html`). No hay ninguna API externa ni base de datos — tú eres quien manda los comandos.

---

## Cómo funciona todo

Imagina una cadena de tres eslabones:

```
TÚ (panel de control)
    │
    │  Mandas un comando: "GOL del equipo local — lo metió García"
    │
    ▼
ws_relay.py  (el "cartero" — corre en tu computadora)
    │
    │  Reenvía el comando a todos los overlays al mismo tiempo
    │
    ▼
OBS Browser Sources  (las "pantallas" que ve el espectador)
    marcador.html → aparece el banner de GOL + sube el marcador
    evento_jugador.html → aparece la tarjeta grande "GOL — García"
```

**Regla de oro:** `ws_relay.py` debe estar corriendo SIEMPRE. Si se cierra, los overlays dejan de recibir comandos.

### Los tres procesos que deben estar activos

| Proceso | Qué hace | Cómo arranca |
|---------|----------|--------------|
| **HTTP server** | Sirve los archivos HTML a OBS | Parte de `iniciar_stream` |
| **ws_relay.py** | Recibe y distribuye comandos | Parte de `iniciar_stream` |
| **OBS Studio** | Muestra los overlays al espectador | Lo abres manualmente |

El script `iniciar_stream` arranca los dos primeros automáticamente.

---

## Instalación — primera vez

### Requisitos previos

1. **Python** instalado (Windows: `python`, Mac: `python3`)
2. **uv** — manejador de dependencias Python (reemplaza pip/venv)
3. **OBS Studio** abierto con WebSocket activado en puerto 4455
4. **PowerShell 7** en Windows (no PowerShell 5 que viene por default)

### Instalar uv

**Windows:**
```powershell
winget install --id=astral-sh.uv -e
# Cierra y vuelve a abrir PowerShell para que se actualice el PATH
```

**Mac:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Cierra y vuelve a abrir la terminal
```

### Activar OBS WebSocket

En OBS: `Herramientas → Ajustes del servidor WebSocket`
- Activa "Habilitar servidor WebSocket"
- Puerto: `4455`
- Activa "Habilitar autenticación"
- Pon una contraseña y guárdala — la necesitarás después

### Clonar el repositorio

```powershell
# Windows
git clone https://github.com/Ol3Ramirez/OBS-overlays-futbol
cd OBS-overlays-futbol

# Mac
git clone https://github.com/Ol3Ramirez/OBS-overlays-futbol
cd OBS-overlays-futbol
```

### Configurar el password de OBS

Entra a la carpeta del perfil que vas a usar:

```powershell
# Windows — perfil SRYiyo
cd SRYiyo
copy .env.example .env
notepad .env
```

```bash
# Mac — perfil SRYiyo
cd SRYiyo
cp .env.example .env
nano .env
```

Escribe esto en el archivo `.env`:
```
OBS_WS_PASSWORD=tu_password_de_obs
```

> El `.env` está en `.gitignore` — nunca se sube a GitHub. Si no lo creas, el script te lo pedirá interactivo la primera vez.

---

## Día del partido — arranque rápido

### Paso 0 — ¿qué perfil vas a usar?

El repo tiene **dos perfiles independientes**. Cada uno tiene sus propios equipos, colores y puertos. Antes de cualquier comando, decide cuál corresponde al partido de hoy:

| Perfil | Carpeta | Patrocinador | Puerto panel |
|--------|---------|--------------|--------------|
| Robles Fútbol | `SRYiyo/` | Robles Fútbol | http://localhost:**8890**/control_remoto.html |
| Avila Fisioterapia | `original/` | Avila Fisioterapia | http://localhost:**8888**/control_remoto.html |

> Todos los comandos siguientes usan `SRYiyo/` como ejemplo.
> Si usas `original/`, **sustituye `SRYiyo` por `original`** y **8890 por 8888** en cada línea.

---

### Windows (PowerShell)

```powershell
# 1. Abrir OBS Studio manualmente (siempre primero)

# 2. Ir a la carpeta del perfil que corresponde al partido
#    — Robles Fútbol:
cd "ruta-donde-clonaste\OBS-overlays-futbol\SRYiyo"
#    — Avila Fisioterapia:
# cd "ruta-donde-clonaste\OBS-overlays-futbol\original"

# 3. Arrancar servidores (HTTP + WebSocket relay)
.\iniciar_stream.ps1

# 4. Primera vez: configurar las escenas en OBS automáticamente
#    (las siguientes veces ya no es necesario)
uv run setup_obs.py

# 5. Abrir el panel de control en Chrome
#    — SRYiyo:
start http://localhost:8890/control_remoto.html
#    — original:
# start http://localhost:8888/control_remoto.html
```

### Mac

```bash
# 1. Abrir OBS Studio manualmente

# 2. Ir a la carpeta del perfil que corresponde al partido
#    — Robles Fútbol:
cd ~/Movies/OBS-overlays-futbol/SRYiyo
#    — Avila Fisioterapia:
# cd ~/Movies/OBS-overlays-futbol/original

# 3. Arrancar servidores
bash iniciar_stream.sh

# 4. Primera vez: configurar OBS
#    (las siguientes veces ya no es necesario)
uv run setup_obs.py

# 5. Abrir panel
#    — SRYiyo:
open http://localhost:8890/control_remoto.html
#    — original:
# open http://localhost:8888/control_remoto.html
```

### ¿Qué hace `iniciar_stream` exactamente?

1. Lee los puertos desde `profile.json` (no hardcodea nada)
2. Si no existe `.env`, te pregunta el password de OBS y lo crea
3. Mata cualquier proceso que ya esté usando esos puertos (idempotente)
4. Arranca el HTTP server en background
5. Arranca `ws_relay.py` con `uv` en background
6. Verifica que ambos puertos estén escuchando
7. Avisa si OBS está abierto o no
8. Guarda los PIDs en `logs/http.pid` y `logs/ws.pid`
9. Queda mostrando el log de WebSocket en vivo (Ctrl+C para cerrar la terminal sin apagar los procesos)

> **Re-ejecutar es seguro.** Si algo falla, vuelve a correr `.\iniciar_stream.ps1` — mata lo anterior y arranca limpio.

---

## Cómo usar el panel de control

Abre en Chrome: `http://localhost:8890/control_remoto.html`

### Secciones del panel

#### Estado de conexión
En la parte superior verás el estado del WebSocket:
- `✅ Conectado` — todo bien, los overlays reciben comandos
- `⚠️ Reconectando...` — el relay se cayó, espera o reinícialo

#### Equipos y partido
- Muestra los equipos cargados desde `config.js`
- Botón **Inicializar overlays** — manda el nombre de equipos a todos los overlays (úsalo al arrancar)

#### Marcador
| Botón | Qué hace |
|-------|----------|
| ▶ / ⏸ | Inicia o pausa el reloj |
| Gol Local | +1 al marcador local + banner "GOL" por 4 segundos |
| Gol Visitante | +1 al visitante + banner "GOL" |
| Siguiente Tiempo | Salta a 2do tiempo (reloj a 45:00) |
| +3 / +5 | Agrega tiempo de descuento (aparece "+3'" en el reloj) |

#### Eventos (tarjetas grandes)
- Campos para nombre del jugador, minuto, equipo
- Botones: Gol, Tarjeta Amarilla, Tarjeta Roja, Cambio, Falla
- Cada evento muestra una tarjeta animada por ~5 segundos y desaparece sola
- **Limpiar** — la quita inmediatamente si necesitas

#### Alineación
- Formulario para introducir formación y jugadores
- Se muestra en la escena "Alineación" de OBS

#### Entrevista
- **Conferencista** — nombre y rol (aparece como lower third)
- **Tema** — texto que corre en ticker
- **Badge** — "EN VIVO" con punto rojo parpadeante

---

## Qué hace cada overlay

Todos los overlays están en `http://localhost:8890/` (o 8888 para el perfil original).

| Archivo | Escena OBS | Propósito |
|---------|-----------|-----------|
| `marcador.html` | Partido en Vivo | Scoreboard + reloj + banner de gol |
| `evento_jugador.html` | Partido en Vivo | Tarjeta animada de gol/falta/cambio |
| `alineacion.html` | Alineación | Formación táctica sobre campo verde |
| `entrevista.html` | Entrevista | Lower third + ticker scrolling |
| `intro.html` | Inicio | Countdown antes del partido |
| `medio_tiempo.html` | Medio Tiempo | Pantalla de descanso |

### Cómo los conecta OBS

Cada overlay es una **Browser Source** en OBS que carga la URL del servidor HTTP local. OBS renderiza el HTML como si fuera Chrome y lo usa como capa transparente encima del video.

**Para refrescar un overlay** si no se ve: clic derecho en la source → **Refresh**.

---

## Cambiar equipos, colores o nombre del partido

**Solo edita `profile.json`** — es la fuente única de verdad.

```json
{
  "home":       "NOMBRE EQUIPO LOCAL",
  "away":       "NOMBRE EQUIPO VISITANTE",
  "matchLabel": "FINAL — TORNEO VERANO 2026",

  "homeColor": "#c62828",
  "awayColor": "#1565C0",
  "accent":    "#FFD700",
  "logo":      "./logo_robles.jpeg",

  "sponsor":      "Nombre del Patrocinador",
  "sponsorSocial": "HandleEnRedes"
}
```

Después de editar `profile.json`:
1. Edita también `config.js` con los mismos valores (es la copia para el browser)
2. Reinicia los servidores: `.\iniciar_stream.ps1`
3. Haz clic en **Refresh** en cada Browser Source de OBS
4. En el panel: presiona **Inicializar overlays**

---

## Perfiles disponibles

### `SRYiyo/` — Robles Fútbol (perfil activo)

| Dato | Valor |
|------|-------|
| Patrocinador | Robles Fútbol |
| Partido | PROVEEDORA ROBLES vs HERMANOS OSORIO |
| Etiqueta | SEMIFINAL DE IDA |
| HTTP | `http://localhost:8890` |
| WebSocket | `ws://localhost:8891` |
| WS bind | `0.0.0.0` (acepta conexiones de red — celular en campo) |
| Token auth | en `profile.local.json` / `config.local.js` (gitignoreados, no en este repo — ver `SRYiyo/CLAUDE.md`) |

Panel: `http://localhost:8890/control_remoto.html`

---

### `original/` — Avila Fisioterapia

| Dato | Valor |
|------|-------|
| Patrocinador | Avila Fisioterapia |
| Partido | LOCAL vs VISITANTE |
| Etiqueta | PARTIDO AMISTOSO |
| HTTP | `http://localhost:8888` |
| WebSocket | `ws://localhost:8889` |
| WS bind | `127.0.0.1` (solo local — sin acceso de red) |

Panel: `http://localhost:8888/control_remoto.html`

---

## Crear un nuevo perfil

Un nuevo perfil = nuevo torneo o patrocinador con sus propios colores.

```powershell
# Windows
xcopy SRYiyo\ NuevoPerfil\ /E /I
cd NuevoPerfil
```

```bash
# Mac
cp -r SRYiyo/ NuevoPerfil/
cd NuevoPerfil/
```

Luego edita `NuevoPerfil/profile.json`:
- Cambia `httpPort` a `8892` (siguiente par disponible)
- Cambia `wsPort` a `8893`
- Actualiza equipos, colores, sponsor, token

Regla de puertos: cada perfil usa un par `+2` del anterior.

| Perfil | HTTP | WS |
|--------|------|----|
| original | 8888 | 8889 |
| SRYiyo | 8890 | 8891 |
| Siguiente | 8892 | 8893 |

---

## Control remoto desde el campo (celular)

Puedes controlar los overlays desde el celular mientras estás en la cancha.

### Con Tailscale (recomendado)

**Requisitos:**
- Tailscale instalado y activo en el celular
- Tailscale activo en la Mac/PC con OBS
- IP Tailscale de la Mac: `100.112.130.14`

**En el celular:**
1. Abrir Tailscale → confirmar "Connected"
2. Abrir Chrome → `http://100.112.130.14:8890/control_remoto.html`
3. El panel detecta que es conexión remota y envía el token automáticamente
4. Deberías ver: `✅ Autenticado — control activo`

**Funciona simultáneo:** mesa de transmisión + celular en campo al mismo tiempo.

### Sin Tailscale (mismo WiFi)

```bash
# En la Mac, ver la IP local
ipconfig getifaddr en0

# En el celular: http://192.168.X.X:8890/control_remoto.html
```

Asegúrate de que `wsBindAddress` sea `"0.0.0.0"` en `profile.json`.

---

## Comandos directos por WebSocket

Si necesitas mandar un comando sin usar el panel (desde Python o terminal):

```bash
# Windows / Mac — requiere uv y websockets
uv run --with websockets python -c "
import asyncio, json
from websockets.asyncio.client import connect

async def cmd(fn, *args):
    async with connect('ws://localhost:8891') as ws:
        await ws.send(json.dumps({'fn': fn, 'args': list(args)}))

asyncio.run(cmd('setTeams', 'CHIVAS', 'AMERICA'))
"
```

### Referencia completa de comandos

#### `marcador.html`
```javascript
setTeams('EQUIPO LOCAL', 'EQUIPO VISITANTE')
setScore(2, 1)           // forzar marcador a 2-1
goalHome('García')       // +1 local + banner GOL
goalAway('López')        // +1 visitante + banner GOL
toggleClock()            // iniciar / pausar reloj
nextHalf()               // ir a 2do tiempo (reloj 45:00)
setMinute(45)            // saltar a minuto específico
addedTime(3)             // mostrar "+3'" de tiempo extra
startClock()             // iniciar (sin toggle)
stopClock()              // pausar (sin toggle)
resetClock()             // regresar a 0:00
```

#### `evento_jugador.html`
```javascript
goal('García', 'Chivas', 23, 'Chivas 1 – 0 América')
yellow('López', 'América', 35)
red('Hernández', 'Chivas', 67)
blue('Mora', 'América', 55)         // tarjeta azul
sub('Salida', 'Entrada', 'Chivas', 70)
miss('García', 'Chivas', 80)        // falla notable
clear()                              // quitar tarjeta actual
```

#### `alineacion.html`
```javascript
setName('PROVEEDORA ROBLES')
setFormation('4-3-3')
setTeam({
  name: 'PROVEEDORA ROBLES',
  formation: '4-3-3',
  coach: 'Entrenador',
  players: [
    { num: 1, name: 'Portero', pos: 'GK', x: 50, y: 85 },
    // x, y = porcentaje de posición en el campo (0-100)
  ]
})
```

#### `entrevista.html`
```javascript
setSpeaker('Juan García', 'Entrenador en jefe', 'left')
clearSpeaker()
setTopic('Texto que corre en el ticker de abajo')
clearTopic()
showBadge('ENTREVISTA EN VIVO')
hideBadge()
setSocial('Robles Futbol')           // badge de red social
setMode('overlay')                   // 'overlay' | 'standalone' | 'lower-third'
```

---

## Solución de problemas

### Los overlays no se actualizan

**Causa más común:** `ws_relay.py` no está corriendo.

```powershell
# Verificar si el puerto WS está activo
netstat -ano | Select-String ":8891"

# Si no aparece → reiniciar
.\iniciar_stream.ps1
```

Después haz **Refresh** en las Browser Sources de OBS.

---

### El panel dice "Sin conexión WebSocket"

1. Verifica que `ws_relay.py` esté corriendo (ver arriba)
2. Revisa el log: `logs\ws.log` y `logs\ws.err`
3. El panel reconecta automáticamente — espera 5-10 segundos
4. Si sigue fallando, recarga la página del panel (`F5`)

---

### `iniciar_stream.ps1` falla con error de Python

```powershell
# Verificar que Python está instalado
python --version
# o
python3 --version

# Si no está → instalar desde python.org
```

---

### `uv run setup_obs.py` falla con "contraseña incorrecta"

1. Verifica el password en OBS: `Herramientas → Ajustes del servidor WebSocket`
2. Actualiza `.env`:
   ```
   OBS_WS_PASSWORD=nuevo_password
   ```
3. Vuelve a correr `uv run setup_obs.py`

---

### OBS no muestra el overlay (pantalla negra en Browser Source)

1. La URL debe usar `http://localhost:8890/` — **no** `file://`
2. Verifica que el HTTP server esté corriendo:
   ```powershell
   netstat -ano | Select-String ":8890"
   ```
3. Abre la misma URL en Chrome — si se ve ahí, el problema es la source de OBS
4. Clic derecho en la source → **Refresh**
5. Si sigue: borra la source y créala de nuevo

---

### El reloj no se ve o no corre

El reloj vive en `marcador.html`. Si no ves nada:
1. Abre `http://localhost:8890/marcador.html` en Chrome directamente
2. Si se ve en Chrome pero no en OBS → refresh de la source
3. Si no se ve en Chrome → revisa la consola del browser (F12 → Console)

---

### Error "puerto en uso" al arrancar

`iniciar_stream.ps1` mata los procesos anteriores automáticamente. Si persiste:

```powershell
# Ver qué proceso usa el puerto 8891
netstat -ano | Select-String ":8891" | Select-String "LISTENING"
# El último número es el PID

# Matar ese proceso
Stop-Process -Id 1234 -Force
```

---

### Logs útiles

```powershell
# Log del WebSocket relay (ver mensajes en tiempo real)
Get-Content logs\ws.log -Wait

# Ver errores del relay
Get-Content logs\ws.err

# Ver errores del HTTP server
Get-Content logs\http.err
```

---

## Referencia de puertos

| Puerto | Servicio | Perfil |
|--------|---------|--------|
| **8888** | HTTP overlays | original |
| **8889** | WebSocket relay | original |
| **8890** | HTTP overlays | SRYiyo |
| **8891** | WebSocket relay | SRYiyo |
| **4455** | OBS WebSocket | todos (compartido) |
| **5000 UDP** | SRT — cámara Android | original (IRL Pro) |

---

## Glosario

| Término | Significado |
|---------|-------------|
| **overlay** | Gráfico transparente que se pone encima del video |
| **Browser Source** | Fuente de OBS que carga una página web como si fuera Chrome |
| **WebSocket** | Conexión de red de dos vías, siempre abierta, para mensajes instantáneos |
| **relay** | El "cartero" — `ws_relay.py` recibe un mensaje y lo manda a todos |
| **perfil** | Carpeta con configuración propia (equipos, colores, puertos) |
| **uv** | Manejador de dependencias Python moderno — instala y corre scripts sin venv manual |
| **PEP 723** | Estándar que permite declarar dependencias dentro del propio archivo `.py` |
| **SSOT** | Single Source of Truth — `profile.json` es el único lugar donde cambiar la config |
| **idempotente** | Puedes correr el script N veces y el resultado siempre es el mismo |
| **Tailscale** | VPN privada que conecta dispositivos como si estuvieran en la misma red local |
| **lower third** | Gráfico en la franja inferior de pantalla — típico en noticias y entrevistas |
| **ticker** | Texto que corre horizontalmente de derecha a izquierda |
| **broadcast** | Mandar el mismo mensaje a todos los conectados al mismo tiempo |

---

*Manual generado en sesión Claude Code — 2026-06-02*
