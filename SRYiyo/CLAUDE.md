# CLAUDE.md — SRYiyo (Robles Fútbol)

## Perfil
**Partido**: PROVEEDORA ROBLES vs HERMANOS OSORIO  
**Torneo**: SEMIFINAL DE VUELTA  
**Productora**: Altavoz Studio (`logo_altavoz_studio.png`)  
**Equipo local**: Proveedora Robles (`logo_robles.jpeg`, secundario)

---

## Arranque rápido

**Mac (primera vez o despues de git pull):**
```bash
cd SRYiyo
bash iniciar_stream.sh   # pide password OBS si .env no existe, lo crea solo
uv run setup_obs.py      # configura OBS + refresca Browser Sources automaticamente
```

**Mac (siguiente vez — ya configurado):**
```bash
bash iniciar_stream.sh   # arranca y listo
```

**Windows:**
```powershell
cd SRYiyo
.\iniciar_stream.ps1     # pide password OBS si .env no existe, lo crea solo
uv run setup_obs.py      # configura OBS + refresca Browser Sources
```

Panel local: `http://localhost:8890/control_remoto.html`

> **Idempotente:** correr cualquiera de estos comandos N veces produce el mismo resultado.
> El `.env` se crea solo la primera vez. `setup_obs.py` refresca sources si ya existen.

---

## Control remoto desde el campo (Tailscale)

Alguien en la cancha puede controlar los overlays desde su celular.

### Requisitos
- Tailscale instalado y activo en el celular del campo
- La Mac corriendo los servidores (`iniciar_stream`)
- La Mac con Tailscale activo (IP: `100.112.130.14`)

### Pasos el día del partido

**1. Antes de empezar — en la Mac:**
```bash
# Verificar que wsBindAddress sea "0.0.0.0" en profile.json (ya configurado)
# Reiniciar el relay si estaba corriendo con 127.0.0.1
pkill -f ws_relay   # Mac
bash iniciar_stream.sh
```

**2. En el celular del campo:**
1. Abrir Tailscale → asegurarse que dice "Connected"
2. Abrir Chrome → `http://100.112.130.14:8890/control_remoto.html`
3. O escanear el **QR** que aparece tocando el icono 📱 en la barra del panel

**3. El panel detecta automáticamente que es remoto** y envía el token de seguridad.
Verás: `✅ Autenticado — control activo`

### Funcionamiento simultáneo
| Dispositivo | URL | Estado |
|-------------|-----|--------|
| Mac (mesa) | `http://localhost:8890/control_remoto.html` | ✅ siempre funciona |
| Celular campo | `http://100.112.130.14:8890/control_remoto.html` | ✅ con Tailscale activo |

Ambos pueden controlar al mismo tiempo. Los comandos de uno se ven en el otro.

### Token de seguridad
El token `robles2025` está en `profile.json` y `config.js`. Se envía automáticamente al conectar desde una IP remota. Las conexiones desde `localhost` no necesitan token (son los overlays de OBS).

### Si Tailscale no está disponible
Fallback: conectar el celular al **mismo WiFi** que la Mac y usar la IP local:
```bash
# Mac: ver IP local
ipconfig getifaddr en0   # Mac WiFi
# Celular: http://192.168.x.x:8890/control_remoto.html
```

---

## Puertos

| Puerto | Servicio |
|--------|---------|
| 8890 TCP | HTTP — overlays |
| 8891 TCP | WebSocket relay (bind: 0.0.0.0) |
| 4455 TCP | OBS WebSocket (compartido) |

---

## Arquitectura

```
Mesa de transmision          Campo
control_remoto.html    control_remoto.html (celular Tailscale)
  ws://localhost:8891    ws://100.112.130.14:8891
         │                        │
         └──────────┬─────────────┘
                    ▼
             ws_relay.py :8891
             (token auth para remotos)
                    │  broadcast
                    ▼
         OBS Browser Sources :8890
           marcador · evento · alineacion
           entrevista · intro · medio_tiempo
```

---

## SSOT — profile.json

Editar solo `profile.json` para cambiar cualquier configuracion del perfil.
`config.js` (browser) y todos los scripts Python/bash leen de ahí.

```json
{
  "home":          "PROVEEDORA ROBLES",
  "away":          "HERMANOS OSORIO",
  "matchLabel":    "SEMIFINAL DE IDA",
  "httpPort":      8890,
  "wsPort":        8891,
  "wsBindAddress": "0.0.0.0",
  "wsToken":       "robles2025",
  "obsCollection": "SRYiyo - Robles Futbol"
}
```

---

## Overlay API

### marcador.html
```javascript
setTeams('PROVEEDORA ROBLES', 'HERMANOS OSORIO')
goalHome('Jugador')    // +1 local + banner GOL
goalAway('Jugador')    // +1 visitante
setScore(0, 0)
toggleClock()
nextHalf()             // 45:00, 2do tiempo
setMinute(45)
addedTime(3)           // +3 minutos descuento
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

---

## OBS Browser Sources

| Escena | URL |
|--------|-----|
| Marcador | `http://localhost:8890/marcador.html` |
| Evento Jugador | `http://localhost:8890/evento_jugador.html` |
| Alineacion | `http://localhost:8890/alineacion.html` |
| Entrevista | `http://localhost:8890/entrevista.html` |
| Intro / Countdown | `http://localhost:8890/intro.html` |
| Medio Tiempo | `http://localhost:8890/medio_tiempo.html` |

---

## Nuevo perfil (coleccion adicional)

```bash
cp -r SRYiyo/ NuevoPerfil/
# Editar NuevoPerfil/profile.json: equipos, puertos (+2), token
bash NuevoPerfil/iniciar_stream.sh
```

---

## OBS WebSocket
- Puerto: `4455`
- Password: en `SRYiyo/.env` como `OBS_WS_PASSWORD=...` (gitignoreado)
- `uv run setup_obs.py` configura OBS automaticamente (idempotente)
