# ROADMAP — OBS Overlays Fútbol

> Lee este archivo al inicio de una nueva sesión para retomar sin perder contexto.
> Actualizado: 2026-06-07

---

## Estado actual del proyecto

Perfil activo: **SRYiyo** (Robles Fútbol · siguiente partido pendiente de fecha)
Equipos actuales: **MOTO EQUIPOS RODRIGUEZ** (rojo #C62828) vs **HERMANOS OSORIO** (blanco #FFFFFF)
Repo: `main` — limpio ✅ (commiteado sesión 2026-06-07)

### Cambios sesión 2026-06-07 ✅ COMMITEADOS

| Archivo | Cambio |
|---------|--------|
| `SRYiyo/control_remoto.html` | Rediseño Stream Deck: tabs (Reloj/Goles/Cards/Cambios/Más), reloj restaurado, hotkeys G/H/Space |
| `SRYiyo/marcador.html` | Logo Altavoz Studio: 18px → 34px, opacidad 0.7 → 0.85 |
| `SRYiyo/profile.json` | Equipos sesión 2026-06-06: MOTO EQUIPOS vs HERMANOS OSORIO |
| `SRYiyo/config.js` | Espejo de profile.json — equipos/colores actualizados |
| `SRYiyo/ws_relay.py` | Token auth, keepalive, mejoras de estabilidad |
| `SRYiyo/setup_obs.py` | Escenas adicionales configuradas automáticamente |
| `SRYiyo/musica_inicio.html` | Nuevo overlay de música de inicio |

### Últimos cambios commiteados (2026-06-02)

| Commit | Descripción |
|--------|-------------|
| `8be9bd4` | chore: add Python __pycache__ to .gitignore |
| `48aae37` | feat: performance, onboarding y arquitectura — 4 sprints completos |
| `0b05e1d` | chore: dejar de rastrear original/logs/http.log |
| `80fa9a5` | docs: agregar ROADMAP.md con pendientes y contexto multi-máquina |

**Sprint 48aae37 resumen:**
- `original/ws-client.js` creado — eliminadas 5 IIFEs WS duplicadas (6 conexiones → 1)
- `cardFlip` 3D (`rotateY`) → 2D (`scale+opacity`) en ambos perfiles
- `scorePop` `filter:drop-shadow` → `text-shadow` en original/marcador.html
- Rotación de logs >5MB en los 4 scripts de arranque (Mac + Windows)
- Quick Start Modal en ambos paneles (3 pasos, localStorage, primera visita)
- WS indicator: 7px → 12px, amarillo parpadeante al conectar, tooltip
- Responsive móvil 480px en original/control_remoto.html
- Atajos de teclado G/H/Y/R/ESPACIO en original (sincronizado con SRYiyo)
- `badgePulse` box-shadow → opacity en original/entrevista.html
- `textShine` 4s → 8s + will-change + prefers-reduced-motion en ambos medio_tiempo.html
- `width`/`height` en 6 logos `<img>` (evita layout shift)
- `setup_obs.py` original: code 601 ahora actualiza URL + refresca Browser Source
- `broadcast()` → `asyncio.wait_for` timeout 2s en ambos ws_relay.py
- MANUAL.md: guía offline completa para ambos perfiles

---

## Control en vivo desde Claude (sin panel)

Cuando el usuario necesite corregir el marcador o manejar el reloj directamente:

```bash
cd "/Users/oleramirez/Movies/MY CLOUDE CODE/OBS_OVERLAYS_FUTBOL/SRYiyo"
uv run --with websockets python3 -c "
import asyncio, json, websockets
async def go():
    async with websockets.connect('ws://localhost:8891') as ws:
        await ws.send(json.dumps({'fn': 'FUNCION', 'args': [ARGS]}))
asyncio.run(go())
"
```

| fn | args | Efecto |
|----|------|--------|
| `setScore` | `[home, away]` | Fijar marcador exacto |
| `goalHome` | `['Jugador', min]` | +1 local + banner GOL |
| `goalAway` | `['Jugador', min]` | +1 visitante |
| `toggleClock` | `[]` | Iniciar / Pausar reloj |
| `setMinute` | `[45]` | Saltar a minuto específico |
| `nextHalf` | `[]` | Activar 2do tiempo (45:00) |
| `addedTime` | `[3]` | Banner +3 minutos descuento |

Para refrescar un Browser Source en OBS (después de editar un overlay):
```
mcp__obs__obs-set-input-settings(NombreSource, {url: "URL?v=N"})  → revertir sin ?v=N
```
Source del marcador: `Browser-Partido`

---

## Pendientes — retomar aquí

### 1. Tests Playwright — panel de control (MEDIA prioridad)
Las features nuevas no tienen cobertura automática:
- `control_remoto.html` — Undo: verificar que el marcador retrocede
- `control_remoto.html` — Event Log: persistencia en sessionStorage al recargar
- `control_remoto.html` — Hotkeys: G/H/Y/R/Espacio/Z/Escape funcionan sin input enfocado
- `control_remoto.html` — Tab Penales: flujo completo 3 y 5 kicks, turnos alternados
- `penalty.html` — slots cambian visualmente con comandos WS (`setPenaltyKick`)

### 2. ecosystem.config.js leer puertos de profile.json (BAJA)
Puertos 8888/8889/8890/8891 hardcodeados. Deberían leerse de `profile.json` (SSOT).
```javascript
// Patrón a implementar en ecosystem.config.js:
const sryiyo = require('./SRYiyo/profile.json');
args: `-m http.server ${sryiyo.httpPort}`,
```

### 3. Overlay `jugador_del_partido.html` ✅ LISTO (sesión 2026-06-03)
Implementado como `Browser-MVP` en OBS (desactivado por defecto).
API: `setMOM(name, team, stats)` / `clearMOM()`. Toggle desde tab Escenas del panel.

---

## Cómo arrancar en una nueva máquina

```bash
# 1. Clonar
git clone https://github.com/Ol3Ramirez/OBS-overlays-futbol.git
cd OBS-overlays-futbol

# 2. Arrancar servidores (pide password OBS la primera vez, crea .env solo)
cd SRYiyo && bash iniciar_stream.sh   # Mac
# .\iniciar_stream.ps1                 # Windows

# 3. Configurar OBS (idempotente, seguro re-correr)
uv run setup_obs.py

# 4. Panel de control
# http://localhost:8890/control_remoto.html
```

Ver `MANUAL.md` para la guía completa sin internet.

---

## Arquitectura rápida

```
SRYiyo/profile.json  ←── SSOT de configuración (puertos, equipos, token)
       ↓ lee
SRYiyo/config.js     ←── espejo browser (window.SRYI)
SRYiyo/ws-client.js  ←── módulo WS compartido por todos los overlays
SRYiyo/ws_relay.py   ←── relay broadcast JSON { fn, args }
```

**Panel → Relay → Overlays OBS:**
```
control_remoto.html → ws://localhost:8891 → ws_relay.py → broadcast → marcador.html
                                                                     → evento_jugador.html
                                                                     → penalty.html
                                                                     → ... etc
```

---

## Reglas del proyecto

- Commits en inglés siguiendo Conventional Commits
- Perfiles son **independientes e idempotentes** — no correr los dos a la vez
- Al preguntar "inicia el sistema" → preguntar cuál perfil antes de lanzar
- `profile.json` es SSOT — si cambias equipos/puertos, editar solo ahí
- Password OBS siempre en `.env` (gitignoreado) — nunca en código fuente
