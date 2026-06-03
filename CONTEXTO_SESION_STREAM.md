# Contexto de Sesión — Stream de Fútbol
### Última actualización: 28 Mayo 2026 — Sesión Ultra Plan · Claude Code (claude-sonnet-4-6)

> Comparte este archivo al inicio de una nueva sesión con Claude Code para retomar exactamente donde dejamos.
> Frase de arranque: **"Lee CONTEXTO_SESION_STREAM.md y continuemos con el stream de fútbol"**

---

## Estado actual del proyecto — TODO FUNCIONA

### Archivos del proyecto

| Archivo | Estado | Descripción |
|---|---|---|
| `marcador.html` | OPTIMIZADO | Barlow Condensed, glassmorphism, **bug running-dot corregido**, rAF guard |
| `alineacion.html` | LISTO | Dots pop-in escalonado, capitán ring pulsante, pitch depth gradient |
| `evento_jugador.html` | OPTIMIZADO | Barlow Condensed, glassmorphism event-card, prefers-reduced-motion |
| `estadisticas.html` | OPTIMIZADO | Barlow Condensed, glassmorphism stats-panel gold border, prefers-reduced-motion |
| `intro.html` | LISTO | Sparkles (8), logo glow burst, countdown pulse 1.1×, finalShake |
| `medio_tiempo.html` | LISTO | DNA visual completo: side-decos, beams, sparks, corners, 3 rings, textShine |
| `entrevista.html` | **NUEVO** | Overlay Interview/Talk-Show: lower-third slide, topic ticker, 3 modos, WebSocket API |
| `control_remoto.html` | ACTUALIZADO | Panel de control web — **8 tabs** (+ Tab Entrevista), WS reconnect corregido |
| `promo_avila.html` | LISTO | 1920×1080, 3 escenas auto-loop (Fútbol5 → Avila → CTA), side-decos 390px |
| `ws_relay.py` | OPTIMIZADO | **State store** — replay estado a overlays reconectados, timestamp logging. Dep: uv/PEP 723 (`websockets>=15`) |
| `FLUJO_PARTIDO.md` | LISTO | Guía operativa día de partido |
| `CLAUDE.md` | ACTUALIZADO | Entrevista API, skills instalados, OBS scenes, bugs corregidos |

### Skills instalados en .claude/skills/
- `frontend-design`, `ui-ux-pro-max`, `senior-frontend`, `canvas-design`, `ui-design-system`, `code-reviewer`, `webapp-testing`
- Agents: `frontend-developer`, `ui-ux-designer`, `code-reviewer`, `debugger`
- Hooks activos: auto-format HTML/CSS (prettier), notificaciones macOS, change-tracker
- Commands: `/ultra-think`, `/code-review`, `/refactor-code`, `/commit`, `/update-docs`

### Cambios OBS (sesión 28 Mayo 2026 — Parte 2)
- Escena eliminada: `Escena` (estaba vacía, sin sources)
- Escena creada: `Entrevista` → Browser Source `http://localhost:8888/entrevista.html` (1920×1080, bg transparente)
- Escenas activas: Entrevista · Inicio · Promo Sponsor · Medio Tiempo · Partido en Vivo · Alineacion

### Bugs corregidos esta sesión
1. `marcador.html`: `getElementById('clock-label')` → `querySelector('.clock-label')` (el running-dot ahora funciona)
2. `marcador.html`: race condition rAF — doble loop al pulsar toggleClock() rápido (fixed con `_rafId` guard)
3. `control_remoto.html`: reconexión múltiple WebSocket (fixed con `readyState` check + single timer)
4. `ui-ux-pro-max/scripts/design_system.py`: SyntaxError f-string backslash (Python 3.9 compat — fixed)
5. `entrevista.html`: overlay modo standalone (fondo oscuro) → cambiado a `overlay` (fondo transparente por defecto)
6. `entrevista.html`: capas OBS invertidas (overlay debajo de cámara) → recreado en orden correcto (cámara=index 0, overlay=index 1)
7. `entrevista.html`: ícono Facebook era carácter "f" → reemplazado con SVG oficial de Facebook
8. `entrevista.html`: side-decos muy sutiles (opacidad 0.06) → aumentado contraste, líneas, SVG icons (micrófono / antena)
9. `entrevista.html`: badge sin fondo sólido → border gold 50% opacidad + box-shadow + texto más grande

### Configuración escena OBS Entrevista
```
Fuentes (orden correcto):
  [1] Overlay Entrevista  (browser_source, index 1 = ENCIMA)
                          URL: http://localhost:8888/entrevista.html
                          1920×1080, bg transparente
  [0] Camara Android      (ffmpeg_source, index 0 = FONDO)
                          SRT desde IRL Pro Android
```

### Archivos eliminados esta sesión
- `record_promo.sh` — exportación MP4, obsoleto (se graba con OBS directamente)
- `logs/` — carpeta vacía
- `TUTORIAL_OVERLAYS_FUTBOL.md` — redundante con CLAUDE.md + FLUJO_PARTIDO.md

### Ruta de los archivos

```
/Users/oleramirez/Movies/MY CLOUDE CODE/OBS_OVERLAYS_FUTBOL/
```

---

## Arquitectura WebSocket (implementada y probada)

```
Chrome (control_remoto.html)
        │  ws://localhost:8889
        ▼
   ws_relay.py  ←────── broadcast ──────→  OBS Browser Sources
        │                                   marcador.html
        │                                   evento_jugador.html
        │                                   estadisticas.html
        │                                   alineacion.html
        │                                   medio_tiempo.html
        └── También acepta comandos de Python directo (desde Claude)
```

Protocolo JSON: `{ "fn": "goalHome", "args": ["Chicharito"] }`

---

## Arranque del partido (resumen rápido)

```bash
# Recomendado — un solo comando
bash "/Users/oleramirez/Movies/MY CLOUDE CODE/OBS_OVERLAYS_FUTBOL/iniciar_stream.sh"

# Manual — Terminal 1: servidor HTML
cd "/Users/oleramirez/Movies/MY CLOUDE CODE/OBS_OVERLAYS_FUTBOL"
python3 -m http.server 8888

# Manual — Terminal 2: relay WebSocket
uv run ws_relay.py
```

OBS Browser Sources → URL base: `http://localhost:8888/`
Panel de control: `http://localhost:8888/control_remoto.html`

---

## OBS — Configuración

- **OBS MCP:** configurado en `~/.claude.json` (comando: `npx -y obs-mcp@latest`, puerto 4455)
- **Browser Sources:** deben usar `http://localhost:8888/` (no `file://` — macOS lo bloquea)
- **Tamaño de fuentes:** 1920×1080 px, 30 FPS

### Escenas OBS

| Escena | Uso | Browser Source |
|---|---|---|
| `Inicio` | Countdown pre-partido | Pantalla Inicio → `intro.html` |
| `Partido en Vivo` | Juego activo | Marcador + Evento Jugador + Estadisticas |
| `Alineacion` | Formaciones al inicio | Overlay Alineacion → `alineacion.html` |
| `Medio Tiempo` | Descanso | Pantalla Medio Tiempo → `medio_tiempo.html` |
| `Promo Sponsor` | Redes sociales | Promo Avila → `promo_avila.html` |
| `Escena` | Pantalla de espera | — |

### OBS Encoder
| Parámetro | Valor |
|---|---|
| Encoder | Apple VideoToolbox H264 (hardware M4) |
| Bitrate | 4000 kbps CBR |
| Keyframe | 2 segundos |
| FPS | 30 |
| Output | Facebook Live RTMPS |

---

## Setup de cámara Android (IRL Pro)

```
App:      IRL Pro (Google Play)
URL SRT:  srt://100.112.130.14:5000
Mode:     Caller
Latency:  2500 ms (ver CONFIG_IRL_PRO.md para cambiar a 4000ms)
Codec:    H.265 (M4 decode hardware, OK)
Bitrate:  8,000 kbps
EIS:      activado
```

### Red Tailscale
| Dispositivo | IP Tailscale | Rol |
|---|---|---|
| `mac-ole` (Mac con OBS) | `100.112.130.14` | Receptor SRT + overlays |
| `honor-x8a-nick` (Android compañero) | `100.117.102.37` | Cámara IRL |

---

## API de los overlays — Referencia completa

```javascript
// ── marcador.html ──
setTeams('LOCAL', 'VISITANTE')
goalHome('Chicharito')          // +1 gol local + banner GOL + partículas
goalAway('Henry Martín')        // +1 gol visitante
setScore(0, 0)                  // override score
toggleClock()                   // iniciar/pausar reloj (muestra dot rojo parpadeante)
nextHalf()                      // saltar a 2do tiempo (45:00)
setMinute(45)                   // fijar minuto manual
addedTime(3)                    // mostrar "+3'" en dorado 8 segundos

// ── evento_jugador.html ──
goal(scorer, team, min, score)  // GOL letra×letra + confetti 30pcs
yellow(player, team, min)       // tarjeta amarilla + cardFlip
red(player, team, min)          // expulsión + cardFlip + shakeX
blue(player, team, min)         // suspensión temporal 2min
sub(out, into, team, min)       // cambio
miss(player, team, min)         // ocasión fallada
clear()

// ── estadisticas.html ──
show() / hide() / toggle()
update({ home, away, possession: [58,42], rows: [...] })

// ── alineacion.html ──
setName('CHIVAS')
setFormation('4-3-3')
setTeam({ name, formation, coach, players: [{num, name, pos, x, y, captain}] })

// ── medio_tiempo.html ──
setText('Volvemos Pronto', 'Disfruta el descanso')
setBadge('MEDIO TIEMPO')                    // texto del badge cyan
setTeams('CHIVAS', 'AMERICA')              // nombres en el score line
setScore(1, 0)                              // muestra score line (CHIVAS 1-0 AMERICA)
clearScore()                                // oculta score line
```

### Desde Python / Claude Code

```bash
uv run --with websockets python3 -c "
import asyncio, json
from websockets.asyncio.client import connect

async def cmd(fn, *args):
    async with connect('ws://localhost:8889') as ws:
        await ws.send(json.dumps({'fn': fn, 'args': list(args)}))

asyncio.run(cmd('setTeams', 'CHIVAS', 'AMERICA'))
asyncio.run(cmd('goalHome', 'Chicharito'))
# Al medio tiempo:
asyncio.run(cmd('setTeams', 'CHIVAS', 'AMERICA'))   # medio_tiempo
asyncio.run(cmd('setScore', 1, 0))                  # muestra marcador 1er tiempo
"
```

---

## Mejoras completadas — Historial completo

### 26 Mayo 2026
- Sistema base WebSocket (ws_relay.py, control_remoto.html)
- Todos los overlays HTML con API básica
- OBS configurado (scenes, browser sources, encoder VideoToolbox)

### 28 Mayo 2026 — Sesión de optimización
- Backdrop-filter eliminado de todos los overlays
- Will-change GPU en elementos animados
- WebSocket exponential backoff (1s → ×1.5 → 30s max)
- rAF clock en marcador.html
- DocumentFragment en alineacion.html (batch DOM)
- Posesión scaleX (GPU) en estadisticas.html
- promo_avila.html: 1080×1080 → 1920×1080 con side-decos 390px
- OBS FPS → 30 en todos los browser sources
- CONFIG_IRL_PRO.md creado (latencia 4000ms recomendada)

### 28 Mayo 2026 — Migración a uv
- **Python**: limpiados directorios huérfanos python3.12 y python3.13 (~20 MB)
- **uv 0.11.16** instalado via Homebrew — reemplaza pip/venv/pyenv
- **ws_relay.py**: bloque PEP 723 inline (`# /// script` con `websockets>=15`)
- **iniciar_stream.sh**: `python3 ws_relay.py` → `uv run ws_relay.py`
- Snippets de comandos Python actualizados a `uv run --with websockets python3 -c "..."`
- `websockets` desinstalado del sistema Python — ahora lo gestiona uv aislado

### 28 Mayo 2026 — Sesión de rediseño visual
- **marcador.html**: score 56px, 28 partículas en gol, running-clock dot
- **evento_jugador.html**: GOL letra×letra, confetti 30pcs, cardFlip, redCard shakeX
- **estadisticas.html**: contadores animados 800ms, winner highlight, possession entrada animada
- **alineacion.html**: dots pop-in escalonado 80ms, capitán ring pulsante, pitch depth gradient
- **intro.html**: 8 sparkles, logo glow burst, countdown 1.1× pulse, finalShake
- **medio_tiempo.html**: rediseño COMPLETO — DNA visual = promo_avila, 3 rings, side-decos, textShine, API setScore()
- Limpieza: eliminados record_promo.sh, logs/, TUTORIAL_OVERLAYS_FUTBOL.md
- OBS: todos los browser sources refrescados via WebSocket

---

## Puertos en uso

| Puerto | Servicio |
|---|---|
| `8888` TCP | Servidor HTTP — overlays HTML |
| `8889` TCP | WebSocket Relay — comandos en tiempo real |
| `4455` TCP | OBS WebSocket (obs-mcp) |
| `5000` UDP | SRT — entrada cámara Android |

---

## Mejoras planeadas (próximas sesiones)

- [ ] Overlay de **penales** (serie de penales con kicks marcados)
- [ ] Overlay de **intro del partido** (animación con escudos de los 2 equipos)
- [ ] Overlay de **jugador del partido** (al final del juego)
- [ ] **Mobile-friendly** `control_remoto.html` (controlar desde teléfono)
- [ ] Añadir **escudos/logos de equipos** como imágenes
- [ ] Integrar con **API de resultados en tiempo real**
- [ ] Botón en panel para enviar `setScore()` a medio_tiempo al cambiar de escena
- [ ] Actualizar estadísticas numéricas desde el panel (no solo mostrar/ocultar)

---

## Para retomar esta sesión

```
Lee el archivo /Users/oleramirez/Movies/MY\ CLOUDE\ CODE/OBS_OVERLAYS_FUTBOL/CONTEXTO_SESION_STREAM.md
y continuemos con el stream de fútbol
```

---

*Sesión actualizada por Claude Code · 28 Mayo 2026 — Rediseño visual completo + medio_tiempo nuevo + limpieza + migración a uv*
