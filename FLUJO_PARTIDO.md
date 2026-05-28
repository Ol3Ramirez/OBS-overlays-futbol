# Flujo de Partido — Stream Fútbol 5
### Última actualización: 28 Mayo 2026

---

## ORDEN DE ARRANQUE (MUY IMPORTANTE)

El orden correcto evita errores de conexión:

```
1. Abrir OBS          ← primero siempre
2. Ejecutar script    ← inicia servidores
3. Abrir Chrome       ← panel de control
4. Abrir Claude Code  ← solo si lo necesitas
```

> ⚠️ **Si abres Claude Code ANTES de OBS**, el MCP de OBS no conecta.
> Solución: cierra Claude Code, abre OBS, vuelve a abrir Claude Code.

---

## ANTES DEL PARTIDO

### 1. Abrir OBS primero

Abre OBS Studio y espera a que cargue completamente (verás tus escenas en el panel izquierdo).

---

### 2. Encender los servidores — Script automático (recomendado)

Abre una terminal y ejecuta **un solo comando**:

```bash
bash "/Users/oleramirez/Movies/MY CLOUDE CODE/OBS_OVERLAYS_FUTBOL/iniciar_stream.sh"
```

El script hace todo solo:
- ✅ Inicia servidor HTTP (puerto 8888)
- ✅ Inicia relay WebSocket (puerto 8889)
- ✅ Verifica que OBS esté abierto
- ✅ Muestra los logs en vivo

**Deja esta terminal abierta.** Para detener: `Ctrl + C`

---

#### Alternativa manual (si el script falla)

Necesitas **dos terminales**:

**Terminal 1:**
```bash
cd "/Users/oleramirez/Movies/MY CLOUDE CODE/OBS_OVERLAYS_FUTBOL"
python3 -m http.server 8888
```
Debe aparecer: `Serving HTTP on 0.0.0.0 port 8888`

**Terminal 2:**
```bash
cd "/Users/oleramirez/Movies/MY CLOUDE CODE/OBS_OVERLAYS_FUTBOL"
python3 ws_relay.py
```
Debe aparecer: `WS Relay escuchando en ws://localhost:8889`

---

> **Si cierras accidentalmente una terminal:** vuelve a ejecutar el mismo comando. El panel reconecta solo en 2 segundos.

> **Para detener:** Ctrl + C en cada terminal al finalizar el partido.

### 2. Abrir el Panel de Control en Chrome

```
http://localhost:8888/control_remoto.html
```

El status bar debe decir: **"✅ Conectado al relay — OBS listo"**

### 3. Actualizar fuentes en OBS

En OBS, **click derecho** en cada fuente → **Actualizar**:
- Marcador
- Evento Jugador
- Estadisticas

> Hacer esto siempre que se hayan cambiado archivos HTML.

### 4. Configurar equipos

En el panel → sección **Configurar Equipos**:
1. Escribe nombre del equipo local
2. Escribe nombre del equipo visitante
3. Click **Guardar Nombres**

Esto actualiza el marcador Y las estadísticas automáticamente.

### 5. Configurar alineación (opcional)

Panel → Tab **Alineación**: escribe el nombre del equipo, formación (ej. 2-2), DT y los 5 jugadores con su número y posición. Click **Enviar Alineación**.

### 5b. Pantallas del sponsor — Antes de arrancar

Crear estas dos escenas en OBS (si no existen):

| Escena OBS | URL del Browser Source |
|---|---|
| **Inicio** | `http://localhost:8888/intro.html` |
| **Medio Tiempo** | `http://localhost:8888/medio_tiempo.html` |

> Tamaño del Browser Source: **1920 × 1080**

**Flujo típico:**
1. Al encender OBS → cambiar a escena **Inicio** → countdown de 5 min empieza solo
2. Desde el panel → Tab **Escenas** → **Iniciar Countdown** (o dejar que corra solo)
3. Al pitazo → OBS cambia a escena **Partido en Vivo**
4. Al silbato de medio tiempo → OBS cambia a escena **Medio Tiempo** (se ve "Volvemos Pronto")
5. Al iniciar 2do tiempo → OBS vuelve a **Partido en Vivo**

### 6. Cámara Android — IRL Pro

```
App:      IRL Pro
URL SRT:  srt://100.112.130.14:5000
Mode:     Caller
Latency:  2500 ms
Codec:    H.265
Bitrate:  8,000 kbps
EIS:      activado
```

> El Android debe estar conectado a **Tailscale** antes de abrir IRL Pro.

---

## DURANTE EL PARTIDO — Qué hacer en cada momento

### Al pitazo inicial

1. Panel → Tab **⏱ Tiempo** → click **Iniciar** ▶️
2. OBS → cambiar a escena **Partido en Vivo**

### Gol

1. Panel → Tab **⚽ Goles**
2. **Local**: toca el chip del goleador (aparece en dorado) → click **Gol Local**
3. **Visitante**: escribe el nombre → click **Gol Visitante**
4. Minuto se captura automático del reloj (editable si necesitas)

**Lo que pasa automáticamente:**
- Marcador se actualiza (ej. 1-0)
- Banner "¡GOL!" aparece 4 segundos en el marcador
- Overlay grande "¡GOL! · NOMBRE · MINUTO" aparece en pantalla
- Evento con el gol aparece abajo a la izquierda

### Tarjeta Amarilla

1. Panel → Tab **Tarjetas**
2. Nombre jugador + equipo + minuto
3. Click **Amarilla** 🟨

### Tarjeta Azul (suspensión temporal — 2 minutos)

1. Panel → Tab **Tarjetas**
2. Nombre jugador + equipo + minuto
3. Click **Azul 2min** 🟦

> En fútbol 5 AMF: el jugador sale 2 minutos. El equipo juega con un jugador menos durante ese tiempo.

### Tarjeta Roja (expulsión)

1. Panel → Tab **Tarjetas**
2. Nombre jugador + equipo + minuto
3. Click **Roja** 🟥

### Sustitución / Cambio

1. Panel → Tab **Cambios**
2. Jugador que **SALE** + jugador que **ENTRA** + equipo + minuto
3. Click **Registrar Cambio**

### Medio Tiempo

1. Panel → Tab **Tiempo** → click **Pausar Reloj** ⏸️
2. OBS → cambiar a escena de descanso (opcional)

### Inicio 2do Tiempo

1. Panel → Tab **Tiempo** → click **2do Tiempo** ➡️
   - El reloj salta a 45:00 y cambia a "2do Tiempo"
2. Click **Iniciar Reloj** ▶️
3. OBS → volver a escena **Partido en Vivo**

### Tiempo de Descuento

1. Panel → Tab **Tiempo** → sección **Tiempo de Descuento**
2. Click en **+1' · +2' · +3' · +4' · +5'** según los minutos añadidos
3. En el marcador OBS aparece `+3'` en dorado 8 segundos y desaparece solo

### Si el reloj se desfasa

1. Panel → Tab **Tiempo**
2. Escribe el minuto real en el campo "Minuto manual"
3. Click **Fijar Min** ⏱️

### Mostrar Estadísticas

1. Panel → Tab **Stats**
2. Click **Mostrar/Ocultar** 📊
3. Click de nuevo para ocultarlas

---

## RESUMEN DE TABS DEL PANEL

| Tab | Para qué |
|---|---|
| **⚽ Goles** | Toca el chip del goleador local → Gol Local. Visitante: escribe nombre → Gol Visitante. Minuto auto. |
| **🟨 Tarjetas** | Toca chip jugador local o escribe visitante → toca Amarilla / Azul / Roja. Minuto auto. |
| **🔄 Cambios** | Toca chip quien SALE (local) o escribe visitante · escribe quien ENTRA · equipo · Registrar. |
| **⏱ Tiempo** | Iniciar ▶ / Pausar ⏸ / Reiniciar ↺ · 2do Tiempo · Fijar minuto · Tiempo de descuento +1'…+5' |
| **📋 Alineación** | Pre-carga jugadores del roster · agrega más · Enviar Alineación |
| **📺 Escenas** | Countdown pantalla de inicio · Textos pantalla de medio tiempo |
| **🎙 Entrevista** | Speaker, topic, badge, modo pantalla |

> **Stats eliminado** — el overlay estadisticas.html fue removido.

---

## AL FINALIZAR

1. IRL Pro → detener stream
2. Panel → Tab **Tiempo** → **Pausar Reloj**
3. Cerrar las dos terminales (Ctrl+C en cada una)
4. OBS → Detener transmisión/grabación

---

## PUERTOS EN USO

| Puerto | Servicio |
|---|---|
| `8888` TCP | Servidor HTTP — overlays HTML |
| `8889` TCP | WebSocket Relay — comandos en tiempo real |
| `4455` TCP | OBS WebSocket (obs-mcp) |
| `5000` UDP | SRT — entrada cámara Android |

## RED TAILSCALE

| Dispositivo | IP | Rol |
|---|---|---|
| `mac-ole` | `100.112.130.14` | Mac con OBS |
| `honor-x8a-nick` | `100.117.102.37` | Cámara Android |

---

## SOLUCIÓN DE PROBLEMAS RÁPIDOS

| Problema | Solución |
|---|---|
| Panel dice "Desconectado del relay" | Verificar que `ws_relay.py` está corriendo en Terminal 2 |
| Overlay no se actualiza en OBS | Click derecho en la fuente → **Actualizar** |
| El reloj no corre | Tab Tiempo → click Iniciar Reloj |
| Los eventos no aparecen (tarjetas, cambios) | Click derecho en "Evento Jugador" en OBS → **Actualizar** |
| Las stats muestran LOCAL/VISITANTE | Primero usa **Guardar Nombres** en el panel |
| Cámara Android no conecta | Verificar Tailscale activo en Android, URL: `srt://100.112.130.14:5000` |

---

---

## ARCHIVOS DEL PROYECTO

| Archivo | Qué hace |
|---|---|
| `marcador.html` | Marcador en vivo con goles, reloj y tiempo de descuento (+N') |
| `evento_jugador.html` | Overlay de eventos (gol, tarjetas, cambios, confetti) |
| `estadisticas.html` | Panel de estadísticas por equipo con contadores animados |
| `alineacion.html` | Formación táctica visual con dots animados y capitán ring |
| `intro.html` | Pantalla de inicio con countdown, sparkles y logo glow |
| `medio_tiempo.html` | Pantalla "Volvemos Pronto" — DNA visual promo, marcador 1er tiempo |
| `control_remoto.html` | Panel de control (7 tabs + botones de descuento) |
| `ws_relay.py` | Relay WebSocket — sincroniza panel con overlays |
| `promo_avila.html` | Animación 1920×1080 para redes (3 escenas en loop: Fútbol 5 → Avila → CTA) |
| `CLAUDE.md` | Guía de arquitectura para Claude Code |

---

## ANIMACIÓN PROMOCIONAL — Para difundir en redes

### Ver la animación

```
http://localhost:8888/promo_avila.html
```

Abre en Chrome (con el servidor HTTP corriendo). Loop automático de 29 segundos con 3 escenas:
1. **FÚTBOL 5 AMF** — badge "Transmisión en Vivo" con punto rojo parpadeante
2. **Avila Fisioterapia** — logo, tagline "Muévete Sin Dolor · Vive Mejor", servicios
3. **Facebook CTA** — "Síguenos en Facebook · Avila Fisioterapia" · dirección · tel. 951 100 98 13

### Grabar con OBS para redes

1. En OBS → escena **Promo Sponsor** → **Iniciar Grabación**
2. Esperar ~30 s (un ciclo completo de las 3 escenas)
3. **Detener Grabación** → el video queda listo para subir a Facebook / Reels

### Datos del patrocinador (Avila Fisioterapia)

| Dato | Valor |
|---|---|
| Página Facebook | Avila Fisioterapia |
| Teléfono | 951 100 98 13 |
| Dirección | Héroes de Chapultepec #45, Barrio San Nicolás, Tlaxiaco |
| Tagline | "Muévete Sin Dolor, Vive Mejor" |
| Servicio | Fisioterapia profesional · Rehabilitación · Servicio a domicilio |

### API medio_tiempo — Mostrar marcador del 1er tiempo

Cuando cambias a la escena Medio Tiempo, puedes enviar el marcador del primer tiempo:

```bash
python3 -c "
import asyncio, json
from websockets.asyncio.client import connect
async def cmd(fn, *args):
    async with connect('ws://localhost:8889') as ws:
        await ws.send(json.dumps({'fn': fn, 'args': list(args)}))
asyncio.run(cmd('setTeams', 'CHIVAS', 'AMERICA'))
asyncio.run(cmd('setScore', 1, 0))
"
```

O desde el panel de control (Tab **Escenas**) → sección **Medio Tiempo**.

*Actualizado por Claude Code · 28 Mayo 2026*
