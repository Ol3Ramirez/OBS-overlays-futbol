# ⚽ OBS Overlays Fútbol

> Sistema de overlays en tiempo real para transmisiones de fútbol en OBS Studio — controlable desde cualquier celular en la cancha.

![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-010101?style=flat&logo=socket.io&logoColor=white)
![OBS Studio](https://img.shields.io/badge/OBS_Studio-302E31?style=flat&logo=obsstudio&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

---

## ✨ Características

- 📺 **6 overlays HTML** listos para usar como Browser Source en OBS
- 📱 **Panel de control remoto** — operable desde celular vía WiFi local
- ⚡ **Tiempo real** mediante relay WebSocket en Python
- 🔁 **Multiples perfiles** — un perfil por torneo o patrocinador
- 🎨 **Totalmente personalizable** — equipos, colores, logos sin tocar el HTML
- 🖥️ **Compatible** con macOS y Windows (PowerShell 7+)
- 🗂️ **Fuente única de verdad** — `profile.json` centraliza toda la configuración

---

## 🏗️ Arquitectura

```
  MESA DE TRANSMISIÓN                      CANCHA (celular)
  ┌──────────────────────────────┐         ┌────────────────────┐
  │  Python HTTP Server :8890    │         │  control_remoto    │
  │  Sirve archivos HTML         │         │  .html             │
  └────────────┬─────────────────┘         │  vía Tailscale     │
               │ http://localhost:8890      │  100.x.x.x:8890   │
               │                           └────────┬───────────┘
    ┌──────────┴──────────────────────────┐         │
    │          │            │             │         │
    ▼          ▼            ▼             ▼         │
marcador   evento_     alineacion   entrevista      │
 .html     jugador.html  .html        .html         │
 intro     medio_tiempo  penalty  (Browser Sources  │
 .html       .html        .html    en OBS Studio)   │
    │          │            │             │         │
    └──────────┴────────────┴─────────────┴────┐    │
                                               │    │
                    WebSocket ws://:8891        │    │
                    (clientes → relay)          │    │
                                               ▼    ▼
                              ┌─────────────────────────────┐
                              │       ws_relay.py :8891      │
                              │       Python — broadcast      │
                              │       a todos los clientes   │
                              └──────────────┬──────────────┘
                                             │
                                             │ ws://localhost:4455
                                             ▼
                              ┌─────────────────────────────┐
                              │       OBS Studio             │
                              │       WebSocket :4455        │
                              │  ← setScene automático       │
                              └─────────────────────────────┘
```

**Flujo de un comando:**
```
Celular (cancha) → ws_relay.py → broadcast → todos los overlays actualizan simultáneamente
                                           → OBS cambia de escena (si el comando es setScene)
```

**Reglas clave:**
- Todos los HTMLs (overlays + panel) son **clientes WebSocket** que se conectan al relay
- El relay hace **broadcast** a todos — un comando del celular actualiza todos los overlays a la vez
- `control_remoto.html` no es un Browser Source de OBS — es el panel de operación
- `ws_relay.py` mantiene conexión persistente con OBS WS (4455) para cambios de escena
- `profile.json` es la fuente única de verdad — puertos, equipos, colores (el token va aparte, en `profile.local.json` gitignoreado)

---

## 📋 Overlays disponibles

| Overlay | Archivo | Descripción |
|---------|---------|-------------|
| 🏆 Marcador | `marcador.html` | Marcador con reloj en vivo, equipos y escudo |
| ⚽ Evento jugador | `evento_jugador.html` | Animación de gol, tarjeta amarilla/roja, cambio |
| 📋 Formaciones | `alineacion.html` | Formación táctica con nombres de jugadores |
| 🎙️ Entrevista | `entrevista.html` | Lower third deslizable + ticker de texto inferior |
| ⏱️ Intro / Cuenta regresiva | `intro.html` | Pantalla de inicio con countdown |
| ⏸️ Medio tiempo | `medio_tiempo.html` | Pantalla de intermedio |
| 🥅 Penales | `penalty.html` | Tablero de tanda de penales |

---

## 📁 Estructura del repositorio

```
OBS-overlays-futbol/
├── original/                  # Perfil base (Avila Fisioterapia)
│   ├── ws_relay.py            # Relay WebSocket Python
│   ├── config.js              # Configuración cliente (espejo de profile.json)
│   ├── profile.json           # ← Fuente única de verdad del perfil
│   ├── iniciar_stream.sh      # Script de inicio macOS
│   ├── iniciar_stream.ps1     # Script de inicio Windows
│   ├── marcador.html
│   ├── evento_jugador.html
│   ├── alineacion.html
│   ├── entrevista.html
│   ├── intro.html
│   ├── medio_tiempo.html
│   └── control_remoto.html    # Panel de control web
├── SRYiyo/                    # Perfil secundario (Robles Futbol)
├── ecosystem.config.js        # Configuración PM2
├── CLAUDE.md                  # Guía de desarrollo con Claude AI
├── MANUAL.md                  # Manual de operación completo
└── ROADMAP.md                 # Funcionalidades pendientes
```

---

## 🖥️ Perfiles configurados

| Perfil | Patrocinador | Puerto HTTP | Puerto WS | Bind |
|--------|-------------|-------------|-----------|------|
| `original` | Avila Fisioterapia | 8888 | 8889 | 127.0.0.1 |
| `SRYiyo` | Robles Futbol | 8890 | 8891 | 0.0.0.0 |

---

## 🚀 Instalación

### Requisitos previos

- [OBS Studio](https://obsproject.com/) con WebSocket habilitado (menú: Herramientas → Servidor WebSocket)
- Python 3.11+
- [`uv`](https://astral.sh/uv) — gestor de paquetes Python moderno
- Git

### macOS

```bash
# 1. Clonar el repositorio
git clone https://github.com/Ol3Ramirez/OBS-overlays-futbol
cd OBS-overlays-futbol

# 2. Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Configurar credenciales OBS
cp .env.example .env
nano .env   # agregar OBS_WS_PASSWORD=tu_password

# 4. Iniciar
cd original   # o SRYiyo según el perfil
chmod +x iniciar_stream.sh
./iniciar_stream.sh
```

### Windows (PowerShell 7+)

```powershell
# 1. Clonar el repositorio
git clone https://github.com/Ol3Ramirez/OBS-overlays-futbol
cd OBS-overlays-futbol

# 2. Instalar uv desde https://astral.sh/uv

# 3. Configurar credenciales OBS
Copy-Item .env.example .env
notepad .env   # agregar OBS_WS_PASSWORD=tu_password

# 4. Iniciar
cd original   # o SRYiyo según el perfil
./iniciar_stream.ps1
```

### Verificar que funciona

Abre en el navegador: `http://localhost:8888/control_remoto.html`

Si ves el panel de control con los botones de gol y reloj, todo está correcto.

---

## ⚙️ Configuración rápida

Edita `profile.json` dentro del perfil que uses — es la **única fuente de verdad**:

```json
{
  "serviceName": "Mi Torneo 2026",
  "httpPort": 8888,
  "wsPort": 8889,
  "wsBindAddress": "127.0.0.1",
  "teamHome": "ÁGUILAS FC",
  "teamAway": "TIGRES",
  "colorHome": "#1e40af",
  "colorAway": "#dc2626",
  "sponsor": "Mi Patrocinador",
  "logoSponsor": "./logo_sponsor.jpg"
}
```

Después de editar, ejecuta nuevamente `iniciar_stream.sh` / `iniciar_stream.ps1`.

> **Nota:** `config.js` se genera o debe mantenerse sincronizado con `profile.json`. No edites `config.js` directamente.

---

## ➕ Agregar nuevo perfil (torneo nuevo)

```bash
# 1. Copiar perfil existente
cp -r original mi_nuevo_torneo

# 2. Editar profile.json con datos del nuevo torneo
cd mi_nuevo_torneo
nano profile.json   # cambiar puertos (usar 8892/8893 para no conflictar)

# 3. Actualizar ecosystem.config.js si usas PM2
# Agregar nueva entrada apuntando a mi_nuevo_torneo/

# 4. Iniciar
./iniciar_stream.sh
```

**Regla de puertos:** cada perfil incrementa en 2.
- `original`: 8888 / 8889
- `SRYiyo`: 8890 / 8891
- `nuevo_torneo`: 8892 / 8893

> Si copias un perfil **con token** (como `SRYiyo`) en vez de `original`, genera
> un token nuevo para el perfil copiado — no reutilices `profile.local.json`/`config.local.js`
> del perfil original. Ver checklist de seguridad más abajo.

---

## 📱 Control remoto desde celular

El panel de control está diseñado para operarse desde un celular en la cancha mientras la PC corre OBS en la mesa de transmisión. Hay dos modos:

---

### 🌐 Opción A — Tailscale (recomendado para el campo)

[Tailscale](https://tailscale.com) crea una VPN privada entre tu celular y tu PC. Funciona desde cualquier red — no importa si el celular tiene datos o WiFi diferente.

**Configuración (una sola vez):**
1. Instala Tailscale en tu PC: [tailscale.com/download](https://tailscale.com/download)
2. Instala Tailscale en tu celular (iOS / Android)
3. Inicia sesión con la misma cuenta en ambos dispositivos
4. En tu PC, ejecuta: `tailscale ip -4` → anota tu IP Tailscale (ej. `100.112.130.14`)

**Verificar que `wsBindAddress` sea `"0.0.0.0"`** en `profile.json` (necesario para aceptar conexiones fuera de localhost):
```json
"wsBindAddress": "0.0.0.0"
```

**El día del partido:**
1. Abre Tailscale en el celular → verifica que diga *Connected*
2. En el navegador del celular: `http://100.112.130.14:8890/control_remoto.html`
   (reemplaza con tu IP Tailscale)
3. El panel detecta automáticamente que es una conexión remota y envía el token

El panel QR (ícono 📱 en la barra superior) genera el link listo para escanear.

---

### 📶 Opción B — WiFi local (misma red)

Si el celular y la PC están en la misma red WiFi:

1. Encuentra la IP local de tu PC:
   - **macOS:** `ipconfig getifaddr en0`
   - **Windows:** `ipconfig` → busca "Dirección IPv4"
2. En el celular: `http://192.168.1.X:8890/control_remoto.html`

> ⚠️ Esta opción falla si el estadio/cancha tiene WiFi que aísla clientes (modo AP isolation). En ese caso usa Tailscale.

---

El panel tiene pestañas: **Reloj / Goles / Cards / Cambios / Más**.

---

## 🛡️ Seguridad

> **Este sistema está diseñado para uso en LAN local.** Entiende las implicaciones antes de usarlo.

### ⚠️ Advertencias importantes

**1. WebSocket sin autenticación CORS**
El relay acepta conexiones de cualquier origen en la red. En LAN local es aceptable. **No expongas los puertos a internet.**

**2. HTTP Server sin autenticación**
El servidor HTTP sirve todos los archivos del directorio del perfil, incluyendo `profile.json`. No lo expongas fuera de tu red local.

**3. Token de autenticación (perfil SRYiyo)**
El token **nunca vive en `profile.json` ni en `config.js`** (ambos se commitean).
Vive en dos archivos gitignoreados que debes crear en cada máquina donde clones el repo:

```bash
cd SRYiyo
cp profile.local.json.example profile.local.json   # token del lado servidor (ws_relay.py)
cp config.local.js.example config.local.js         # mismo token del lado navegador (control_remoto.html)

# Generar el token:
python3 -c "import secrets; print(secrets.token_hex(16))"
# Pegarlo como "wsToken" en profile.local.json Y como WS_TOKEN en config.local.js (mismo valor)
```

`ws_relay.py` carga `profile.json` y superpone `profile.local.json` si existe.
Si no creas estos archivos, el relay arranca sin token (`token=NO` en el log) —
aceptable solo en `127.0.0.1`. Antes de exponer el panel por Tailscale/LAN, créalos.
Detalle completo en `SRYiyo/CLAUDE.md` (sección "Token de WebSocket — dónde va realmente").

### ✅ Lo que ya está protegido

- La contraseña OBS WebSocket nunca está hardcodeada — se carga desde variable de entorno → `.env` → prompt interactivo
- `.env` está en `.gitignore`
- El relay valida JSON antes de hacer broadcast
- Timeout de 2s para clientes lentos (previene bloqueos)
- Logs con rotación automática a 5 MB

### Configuración recomendada según caso de uso

| Escenario | `wsBindAddress` | Token |
|-----------|-----------------|-------|
| Solo tu PC (OBS + overlays en misma máquina) | `127.0.0.1` | No requerido |
| LAN local (celular en la cancha) | `0.0.0.0` | Token fuerte generado aleatoriamente |
| Acceso remoto | VPN / Tailscale | Token fuerte + WireGuard |

### Checklist antes de producción

- [ ] Crear `profile.local.json` y `config.local.js` con un token generado (nunca en `profile.json`/`config.js`)
- [ ] Revisar `wsBindAddress` (`127.0.0.1` para local, `0.0.0.0` solo si necesitas LAN)
- [ ] Crear `.env` con `OBS_WS_PASSWORD=<tu_password>`
- [ ] Verificar que los puertos 8888–8891 **no** estén redirigidos en tu router
- [ ] No commitear `.env`, `profile.local.json` ni `config.local.js` al repositorio

### Reportar vulnerabilidades

Si encuentras un problema de seguridad, **no lo publiques en Issues públicos**. Contacta directamente al autor.

---

## 📖 Documentación adicional

| Documento | Descripción |
|-----------|-------------|
| [MANUAL.md](./MANUAL.md) | Manual de operación completo (arranque, overlays, troubleshooting) |
| [ROADMAP.md](./ROADMAP.md) | Funcionalidades pendientes y estado del proyecto |
| [CLAUDE.md](./CLAUDE.md) | Guía de arquitectura para desarrollo con Claude AI |

---

## 🤝 Contribuir

1. Fork del repositorio
2. Crea una rama: `git checkout -b feature/nombre-corto`
3. Commit con Conventional Commits: `feat(overlay): add penalty shootout screen`
4. Push y abre un Pull Request describiendo el cambio

**Para agregar un nuevo overlay:**
- Usa `ws-client.js` existente para recibir comandos del relay
- Sigue el patrón `window.obsOverlay.nombreFuncion()` para exponer comandos
- Documenta el nuevo comando en `MANUAL.md`

---

## 📜 Licencia

MIT © [Ol3Ramirez](https://github.com/Ol3Ramirez)
