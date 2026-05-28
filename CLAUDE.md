# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Starting the System

**Always open OBS before Claude Code** — the OBS MCP won't connect if Claude Code is launched first.

```bash
# Recommended: one command starts both servers
bash "/Users/oleramirez/Movies/MY CLOUDE CODE/OBS_OVERLAYS_FUTBOL/iniciar_stream.sh"

# Manual alternative (two terminals):
python3 -m http.server 8888          # Terminal 1 — serves HTML overlays
python3 ws_relay.py                  # Terminal 2 — WebSocket relay

# Stop everything
pkill -f 'http.server 8888' && pkill -f ws_relay.py
```

Panel de control: `http://localhost:8888/control_remoto.html`

## Architecture

```
Chrome (control_remoto.html)
        │  ws://localhost:8889
        ▼
   ws_relay.py  ──── broadcast ────▶  OBS Browser Sources
                                       marcador.html
                                       evento_jugador.html
                                       estadisticas.html
                                       alineacion.html
```

- `ws_relay.py` — broadcast relay with **state store** (websockets 15.x): stores last command per `fn`, replays state to newly connected overlays so they recover after reload.
- All overlays connect to `ws://localhost:8889` on load and listen for `{ fn, args }` JSON commands.
- **No localStorage** — all communication goes through WebSocket only.
- OBS Browser Sources must use `http://localhost:8888/` (not `file://` — macOS CEF blocks local file access).
- Font: **Barlow Condensed** (Google Fonts, loaded in all overlays) — sports-optimized typography.

## Sending Commands

Commands are JSON objects `{ "fn": "functionName", "args": [...] }` sent to `ws://localhost:8889`.

From Python / Claude Code:
```bash
python3 -c "
import asyncio, json
from websockets.asyncio.client import connect

async def cmd(fn, *args):
    async with connect('ws://localhost:8889') as ws:
        await ws.send(json.dumps({'fn': fn, 'args': list(args)}))

asyncio.run(cmd('setTeams', 'CHIVAS', 'AMERICA'))
asyncio.run(cmd('goalHome', 'Chicharito'))
"
```

## Overlay API Reference

### marcador.html
```javascript
setTeams('LOCAL', 'VISITANTE')
goalHome('Nombre')      // +1 home + banner GOL 4s
goalAway('Nombre')      // +1 away
setScore(0, 0)          // override score
toggleClock()           // start/pause clock
nextHalf()              // jump to 2nd half (45:00)
setMinute(45)           // set clock to specific minute
```

### evento_jugador.html
```javascript
goal(scorer, team, min, score)     // full-screen goal overlay
yellow(player, team, min)
red(player, team, min)
sub(out, into, team, min)          // substitution
miss(player, team, min)
clear()
```

### estadisticas.html
```javascript
show() / hide() / toggle()
update({ home, away, possession: [58,42], rows: [...] })
```

### alineacion.html
```javascript
setName('EQUIPO')
setFormation('4-3-3')
setTeam({ name, formation, coach, players: [{num, name, pos, x, y}] })
// x, y = position percentage on the pitch field
```

### entrevista.html
```javascript
setSpeaker('Nombre', 'Rol / Cargo', 'left'|'right')  // slide-in lower third
clearSpeaker()                                          // slide-out lower third
setTopic('Texto del tema')                              // activar ticker scrolling
clearTopic()                                            // ocultar ticker
showBadge('ENTREVISTA EN VIVO')                         // badge superior con dot rojo
hideBadge()
setMode('overlay'|'standalone'|'lower-third')           // modo de pantalla
setSocial('Avila Fisioterapia')                         // CTA facebook badge
```
Modos: `standalone` = fondo completo con beams+sparkles; `overlay` = fondo transparente (sobre cámara); `lower-third` = solo franja inferior.

## Ports

| Port | Service |
|------|---------|
| 8888 TCP | HTTP server — HTML overlays |
| 8889 TCP | WebSocket relay — real-time commands |
| 4455 TCP | OBS WebSocket (obs-mcp) |
| 5000 UDP | SRT — Android camera input |

## Network / Camera

- **Tailscale** must be active on both devices before opening IRL Pro.
- `mac-ole` (Mac/OBS): `100.112.130.14`
- `honor-x8a-nick` (Android camera): `100.117.102.37`
- IRL Pro SRT: `srt://100.112.130.14:5000`, Mode: Caller, H.265, 8000 kbps, latency 2500ms

## CSS Customization

Each overlay uses CSS variables at the top of the file:
```css
:root {
  --gold: #FFD700;
  --glass: rgba(8, 8, 20, 0.88);
  --accent: #00e5ff;
  --home-color: #3b82f6;
  --away-color: #ef4444;
}
```

## OBS MCP

Configured in `~/.claude.json` under `mcpServers.obs`. Command: `npx -y obs-mcp@latest`, port 4455. Allows controlling OBS scenes and sources with natural language.

After adding a new scene in OBS that uses a Browser Source, right-click the source → **Refresh** to reload the HTML.

## Installed Skills (.claude/skills/)

Installed from aitmpl.com (claude-code-templates) — available in this project:
- `frontend-design` — production-grade HTML/CSS interfaces, avoids generic AI aesthetics
- `ui-ux-pro-max` — 50 styles, glassmorphism, animations, design system generator
- `senior-frontend` — CSS performance, bundle optimization, component patterns
- `canvas-design` — visual art/poster design with professional fonts
- `ui-design-system` — design token generator, consistency tools
- `code-reviewer` — code quality, security, antipatterns
- `webapp-testing` — Playwright-based overlay testing

Agents: `frontend-developer`, `ui-ux-designer`, `code-reviewer`, `debugger`
Commands: `/ultra-think`, `/code-review`, `/refactor-code`, `/commit`, `/update-docs`
Hooks: auto-format HTML/CSS/JS (prettier), desktop notifications, change tracker

## OBS Scenes (current)

| Scene | Source | URL |
|-------|--------|-----|
| Inicio | Pantalla Inicio (browser) | `http://localhost:8888/intro.html` |
| Partido en Vivo | marcador + evento + stats | multiple |
| Alineacion | browser | `http://localhost:8888/alineacion.html` |
| Medio Tiempo | browser | `http://localhost:8888/medio_tiempo.html` |
| Entrevista | Overlay Entrevista (browser) | `http://localhost:8888/entrevista.html` |
| Promo Sponsor | browser | `http://localhost:8888/promo_avila.html` |

## Known Bugs Fixed

- `slideDown` animation on `.scoreboard` preserves `translateX(-50%)` — removing it shifts the scoreboard off-center. The keyframe must include `translateX(-50%)` at both `from` and `to`.
- `ws_relay.py` requires `from websockets.asyncio.server import broadcast, serve` (websockets 15.x API — not the legacy import path).
- `marcador.html`: `updateRunningDot()` used `getElementById('clock-label')` (no such ID) — fixed to `querySelector('.clock-label')`. The running-dot now shows correctly.
- `marcador.html`: rAF loop could start multiple instances if `toggleClock()` was called rapidly — fixed with `_rafId` guard + `cancelAnimationFrame`.
- `control_remoto.html`: WebSocket reconnect could trigger multiple simultaneous reconnects — fixed with `readyState` check and single-timer guard.
