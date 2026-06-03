# CLAUDE.md — SRYiyo (Robles Fútbol)

## Perfil
**Partido**: PROVEEDORA ROBLES vs HERMANOS OSORIO  
**Torneo**: SEMIFINAL DE IDA  
**Sponsor**: Robles Fútbol (`logo_robles.jpeg`)  

## Arranque (idempotente)

**Mac / Linux:**
```bash
bash "./SRYiyo/iniciar_stream.sh"
```

**Windows:**
```powershell
.\SRYiyo\iniciar_stream.ps1
```

Panel de control: `http://localhost:8890/control_remoto.html`

## Puertos (independientes del perfil original)

| Puerto | Servicio |
|--------|---------|
| 8890 TCP | HTTP — overlays SRYiyo |
| 8891 TCP | WebSocket relay SRYiyo |
| 4455 TCP | OBS WebSocket (compartido) |

## Arquitectura

```
control_remoto.html
    │  ws://localhost:8891
    ▼
ws_relay.py (puerto 8891)
    │  broadcast
    ▼
marcador.html · evento_jugador.html · alineacion.html
entrevista.html · intro.html · medio_tiempo.html
```

## config.js — Punto único de configuración

Editar `config.js` para cambiar equipos, colores o torneo sin tocar cada overlay:

```javascript
window.SRYI = {
  HOME:        'PROVEEDORA ROBLES',
  AWAY:        'HERMANOS OSORIO',
  MATCH_LABEL: 'SEMIFINAL DE IDA',
  HOME_COLOR:  '#c62828',   // rojo
  AWAY_COLOR:  '#1565C0',   // azul marino
  WS_PORT:     8891,
  HTTP_PORT:   8890,
  SPONSOR:     'Robles Fútbol',
};
```

## Overlay API

### marcador.html
```javascript
setTeams('PROVEEDORA ROBLES', 'HERMANOS OSORIO')
goalHome('Jugador')   // +1 local + banner GOL
goalAway('Jugador')   // +1 visitante
setScore(0, 0)
toggleClock()
nextHalf()            // → 45:00 2do tiempo
setMinute(45)
addedTime(3)
```

### evento_jugador.html
```javascript
goal(player, team, min, scoreline)
yellow(player, team, min)
red(player, team, min)
sub(out, into, team, min)
clear()
```

### alineacion.html
```javascript
setTeam({ name, formation, coach, players: [{num, name, pos, x, y}] })
setName('PROVEEDORA ROBLES')
setFormation('2-2')
```

## Crear un nuevo perfil (colección)

Para agregar un tercer perfil (ej. "Torneo2025"):
1. Copiar la carpeta `SRYiyo/` → `Torneo2025/`
2. Editar `Torneo2025/config.js` con los nuevos equipos y puertos (8892/8893)
3. El resto de los archivos se adaptan automáticamente via `window.SRYI`

## OBS Browser Sources (este perfil)

| Escena | URL |
|--------|-----|
| Marcador | `http://localhost:8890/marcador.html` |
| Evento Jugador | `http://localhost:8890/evento_jugador.html` |
| Alineación | `http://localhost:8890/alineacion.html` |
| Entrevista | `http://localhost:8890/entrevista.html` |
| Intro / Countdown | `http://localhost:8890/intro.html` |
| Medio Tiempo | `http://localhost:8890/medio_tiempo.html` |

## OBS WebSocket
- Puerto: `4455`
- Contraseña: configurada en `C:\Users\OLE\.claude\settings.json` → `mcpServers.obs`
