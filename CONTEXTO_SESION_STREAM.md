# Contexto de sesión — OBS Overlays Fútbol
Última actualización: 2026-06-07

---

## Estado actual: SRYiyo ✅ COMPLETO

Todo lo siguiente ya está aplicado y probado en `SRYiyo/`:

### control_remoto.html — mejoras aplicadas
- **FIJAR TIEMPO EXACTO**: inputs Min:Seg + botón "Fijar" → envía `setMinute` al relay
- **MARCADOR DIRECTO**: inputs Local/Visit + botón "✓" → envía `setScore` al relay
- **Banner WS desconectado**: franja roja visible + botones deshabilitados cuando `ws_relay.py` no corre

### marcador.html — rediseño TV Azteca / Liga MX + fix Facebook
- Fonts: Bebas Neue (scores, reloj, nombres) + Barlow Condensed (labels)
- Barra full-width en la parte superior (no centrada)
- Estructura: `clock-block | team-home | score-block | team-away`
- **Fix badge Facebook Live**: `padding-left: 165px` en `.hud` → reloj empieza en x≈165px, fuera del badge "EN VIVO" de Facebook (esquina superior izquierda, ~0–160px)
- Zona oscura vacía a la izquierda funciona como fondo para el badge de Facebook (se ve mejor)

---

## Tarea pendiente: aplicar a `original/`

### Qué hay en original/ ahora
- Diseño DIFERENTE al SRYiyo: `.scoreboard` centrado (`left: 50%; transform: translateX(-50%)`)
- Equipo: Avila Fisioterapia (local) vs otro equipo
- Puertos: HTTP=8888, WS=8889
- Font: solo Barlow Condensed (sin Bebas Neue)
- No tiene el problema del badge de Facebook (está centrado, no en top-left)

### Lo que hay que hacer mañana

**Opción acordada: aplicar plantilla TV Azteca de SRYiyo a original/, adaptada**

1. **Copiar estructura HTML/CSS/JS de `SRYiyo/marcador.html`** a `original/marcador.html`
   - Los datos de equipo vienen de `config.js` dinámicamente → no hay que hardcodear nombres
   - El `config.js` de original/ usa los datos de Avila Fisioterapia
   - Verificar que `original/config.js` tiene las variables correctas (home, away, matchLabel, wsPort=8889, httpPort=8888)

2. **Ajustar puertos en la plantilla**
   - `original/marcador.html` debe conectarse a WS port 8889 (no 8891)
   - La config se carga de `config.js` → si usa `window.SRYI.wsPort` debería funcionar solo
   - Verificar que `original/config.js` exporta el mismo objeto `window.SRYI`

3. **Para el badge de Facebook**
   - Si se usa el mismo diseño de barra full-width, aplicar `padding-left: 165px` igual que SRYiyo
   - Si se decide dejar centrado, no es necesario el fix

4. **Aplicar mismas mejoras a `original/control_remoto.html`**
   - FIJAR TIEMPO EXACTO (Min:Seg)
   - MARCADOR DIRECTO (Local/Visit)
   - Banner WS desconectado

5. **Probar**: iniciar servidor original (`python3 -m http.server 8888` en carpeta `original/`) y verificar en `http://localhost:8888/marcador.html`

---

## Archivos clave para mañana

| Archivo | Estado |
|---------|--------|
| `SRYiyo/marcador.html` | ✅ Referencia final — copiar estructura |
| `SRYiyo/control_remoto.html` | ✅ Referencia final — copiar mejoras |
| `original/marcador.html` | ⏳ Pendiente redesign TV Azteca |
| `original/control_remoto.html` | ⏳ Pendiente mejoras WS + score/tiempo directo |
| `original/config.js` | Revisar que tenga wsPort=8889, httpPort=8888 |

---

## Servidores SRYiyo (corriendo en esta Mac)

```bash
# Verificar que siguen activos:
lsof -i :8890 -sTCP:LISTEN   # HTTP
lsof -i :8891 -sTCP:LISTEN   # WS relay

# Si no, arrancar:
cd "/Users/oleramirez/Movies/MY CLOUDE CODE/OBS_OVERLAYS_FUTBOL/SRYiyo"
python3 -m http.server 8890 &
uv run ws_relay.py &
```

Panel de control: `http://localhost:8890/control_remoto.html`
Marcador preview: `http://localhost:8890/marcador.html`
