# ROADMAP — OBS Overlays Fútbol

> Lee este archivo al inicio de una nueva sesión para retomar sin perder contexto.
> Actualizado: 2026-06-03

---

## Estado actual del proyecto

Perfil activo: **SRYiyo** (Robles Fútbol · Semifinal de Ida)
Repo: `main` — limpio, sincronizado con origin
PM2: `sryiyo-http` (8890) y `sryiyo-ws` (8891) activos · `original-*` detenido

### Últimos cambios (2026-06-03)

| Commit | Descripción |
|--------|-------------|
| `c5765b1` | docs: GUIA_OPERADOR.md — flujo, hotkeys, troubleshooting |
| `db3ccdc` | feat: overlay `penalty.html` + tab Penales en panel |
| `242e4ef` | feat: Undo, Event Log, Keyboard Shortcuts en control_remoto.html |
| `781eb3d` | fix: hmac token auth, DocumentFragment, updateRunningDot sin innerHTML, colores SSOT |

---

## Pendientes — retomar aquí

### 1. Tests Playwright — panel de control (MEDIA prioridad)
Las features nuevas no tienen cobertura automática todavía:
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

### 3. Sincronizar mejoras SRYiyo → original/ (BAJA)
El perfil `original/` no recibió las mejoras de esta sesión:
- `ws-client.js` — `_safeArgs()` + retry counter
- `alineacion.html` — DocumentFragment + animaciones stagger
- `marcador.html` — `updateRunningDot()` sin innerHTML

### 4. Overlay `jugador_del_partido.html` (ROADMAP)
Lower-third post-partido para anunciar al MVP.
```javascript
// API propuesta:
setMOM(name, team, stats)   // mostrar jugador del partido
clearMOM()                  // ocultar
```
Basarse en la estructura de `entrevista.html` (lower-third + speaker).

### 5. control_remoto.html mobile-friendly (ROADMAP)
El panel funciona en celular pero los botones son pequeños en 5-6".
- Botones mínimo 48px en touch
- Spacing mínimo 16px
- Media query `@media (max-width: 480px)`

---

## Cómo arrancar en una nueva máquina

```bash
# 1. Clonar e instalar
git clone https://github.com/Ol3Ramirez/OBS-overlays-futbol.git
cd OBS-overlays-futbol

# 2. Crear .env con contraseña de OBS (se pregunta automáticamente)
cd SRYiyo && bash iniciar_stream.sh

# 3. Configurar OBS (idempotente, seguro re-correr)
uv run setup_obs.py

# 4. Panel de control
# http://localhost:8890/control_remoto.html
```

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

- Commits en **español** siguiendo Conventional Commits
- Perfiles son **independientes e idempotentes** — no correr los dos a la vez
- Al preguntar "inicia el sistema" → preguntar cuál perfil antes de lanzar PM2
- `profile.json` es SSOT — si cambias equipos/puertos, editar solo ahí
