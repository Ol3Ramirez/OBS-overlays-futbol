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
┌─────────────────────┐
│  Panel Control Web  │  ← celular / PC en la cancha
│  control_remoto.html│
└────────┬────────────┘
         │ WebSocket (puerto 8891)
         ▼
┌─────────────────────┐      broadcast
│  ws_relay.py        │ ──────────────────────┐
│  (Python relay)     │                       │
└────────┬────────────┘                       │
         │                                    │
         ▼                                    ▼
┌─────────────────────┐          ┌────────────────────┐
│  OBS Studio         │          │  Otros overlays    │
│  Browser Sources    │          │  (marcador, goles) │
│  (puerto 8888)      │          │  en la misma red   │
└─────────────────────┘          └────────────────────┘
         │
         ▼ OBS WebSocket (puerto 4455)
┌─────────────────────┐
│  Cambio de escenas  │
│  automático         │
└─────────────────────┘
```

**Flujo de datos:**
`Comando en celular → relay WebSocket → broadcast simultáneo → todos los overlays actualizan`

`profile.json` es la fuente única de verdad (puertos, equipos, colores). `config.js` lo espeja para el navegador.

---

## 📋 Overlays disponibles

| Overlay | Archivo | Descripción |
|---------|---------|-------------|
| 🏆 Marcador | `marcador.html` | Marcador con reloj en vivo, equipos y escudo |
| ⚽ Evento jugador | `evento_jugador.html` | Animación de gol, tarjeta amarilla/roja, cambio |
| 📋 Formaciones | `alineacion.html` | Formación táctica con nombres de jugadores |
| 📢 Lower third | `lower_third.html` | Banner inferior con mensaje personalizable |
| ⏱️ Cuenta regresiva | `cuenta_regresiva.html` | Temporizador para pre-partido |
| ⏸️ Medio tiempo | `medio_tiempo.html` | Pantalla de intermedio |

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
│   ├── lower_third.html
│   ├── cuenta_regresiva.html
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

---

## 📱 Control remoto desde celular

1. Asegúrate de que tu celular esté en la misma red WiFi que la PC con OBS
2. Abre el navegador del celular
3. Entra a: `http://<IP_de_tu_PC>:<HTTP_PORT>/control_remoto.html`
   - Ejemplo: `http://192.168.1.50:8890/control_remoto.html`
4. Para encontrar la IP de tu PC:
   - **macOS:** `ipconfig getifaddr en0`
   - **Windows:** `ipconfig` → busca "Dirección IPv4"

El panel de control tiene pestañas: **Reloj / Goles / Cards / Cambios**.

---

## 🛡️ Seguridad

> **Este sistema está diseñado para uso en LAN local.** Entiende las implicaciones antes de usarlo.

### ⚠️ Advertencias importantes

**1. WebSocket sin autenticación CORS**
El relay acepta conexiones de cualquier origen en la red. En LAN local es aceptable. **No expongas los puertos a internet.**

**2. HTTP Server sin autenticación**
El servidor HTTP sirve todos los archivos del directorio del perfil, incluyendo `profile.json`. No lo expongas fuera de tu red local.

**3. Token de autenticación (perfil SRYiyo)**
El token por defecto en este repo es un **ejemplo**. Genera uno nuevo para producción:
```bash
python3 -c "import secrets; print(secrets.token_hex(16))"
```
Actualiza `wsToken` en `profile.json` y `config.js`, y **nunca lo commitees a git**.

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

- [ ] Cambiar token en `profile.json` y `config.js` (si usas perfil con token)
- [ ] Revisar `wsBindAddress` (`127.0.0.1` para local, `0.0.0.0` solo si necesitas LAN)
- [ ] Crear `.env` con `OBS_WS_PASSWORD=<tu_password>`
- [ ] Verificar que los puertos 8888–8891 **no** estén redirigidos en tu router
- [ ] No commitear `.env` ni tokens al repositorio

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
