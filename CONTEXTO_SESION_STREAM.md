# Contexto de sesión — OBS Overlays Fútbol
Última actualización: 2026-06-25

> **2026-06-25 (rama refactor/ssot-multiplatform-best-practices):** `config.js` ahora se
> GENERA desde `profile.json` (`shared/gen_config.py`) en cada arranque — `profile.json` es
> la única fuente de verdad (incluye `features`, `scenePrefix`, `scenes`). Escenas derivadas
> de `profile.json` (sin hardcodeo). Suite Playwright 15/15. `verificar.sh`/`.ps1` +
> `MULTISYSTEM.md`. **Diseño TV Azteca ya migrado a `original/marcador.html`** (ver abajo, ✅).

---

## Estado actual del repo ✅ LIMPIO — main sincronizado

Último commit: `fix(marcador): load sponsor logo from config instead of hardcoded path`

---

## SRYiyo/ ✅ COMPLETO

### marcador.html
- Diseño TV Azteca / Liga MX: barra full-width, Bebas Neue + Barlow Condensed
- Fix badge Facebook Live: `padding-left: 165px`
- **Logo Altavoz Studio**: lee `window.SRYI.ALTAVOZ_LOGO` vía script inline DESPUÉS del elemento `<img>` (evita race condition DOM)
- `ws_relay.py` corre en puerto 8891, bind 0.0.0.0 (Tailscale activo)

### control_remoto.html
- 5 tabs: Goles, Tarjetas, Cambios, Tiempo, Alineación, Escenas, Entrevista
- FIJAR TIEMPO EXACTO (Min:Seg) + MARCADOR DIRECTO (setScore)
- Banner WS desconectado visible
- GOL LOCAL (chip jugador) + GOL VISITANTE (input)

### iniciar_stream.sh
- `python3 -m http.server "$HTTP_PORT" --directory "$DIR"` ← rutas relativas correctas sin importar desde dónde se ejecute

---

## original/ ✅ PARCIALMENTE ACTUALIZADO

### control_remoto.html ✅ TERMINADO HOY (2026-06-07)
- **SVG sprite completo (26 símbolos Lucide)** — reemplaza todos ~35 emoji `.ico`
- Tabs sin emojis: Goles, Tarjetas, Cambios, Tiempo, Alineación, Escenas, Entrevista
- `aria-label` en 3 botones sel-clear + 2 botones icon-only (clearTopic, hideBadge)
- Focus-visible rings, 44px touch targets, transiciones 150-300ms

### marcador.html ✅ BUG IMAGEN CORREGIDO HOY (2026-06-07)
- Logo Avila Fisioterapia: lee `window.SRYI.ALTAVOZ_LOGO` desde config (ya no hardcodeado)
- El setter corre dentro del bloque `if (window.SRYI)` DESPUÉS del elemento HTML → sin race condition
- ⚠️ Diseño sigue siendo el ORIGINAL (centrado, sin TV Azteca) — NO se migró a plantilla SRYiyo

### config.js ✅
- Agregado `ALTAVOZ_LOGO: './logo_sponsor.jpg'` (Avila Fisioterapia)

### iniciar_stream.sh ✅
- `--directory "$DIR"` agregado

---

## Tarea: migrar diseño TV Azteca a original/marcador.html ✅ HECHO (2026-06-25)

`original/marcador.html` ya usa el diseño TV Azteca (barra full-width, Bebas Neue +
Barlow Condensed) leyendo nombres/colores de `window.SRYI`. Se conservaron IDs y la API
`obsOverlay` — los 4 tests `marcador.html [original]` pasan. Detalle histórico abajo.

### Lo que hay que hacer
1. Copiar estructura HTML/CSS/JS de `SRYiyo/marcador.html` a `original/marcador.html`
2. Los datos vienen de `config.js` dinámicamente — no requiere hardcodear nombres
3. Ajustar: `wsPort=8889`, `httpPort=8888` (vienen de `window.SRYI` automático)
4. Si se usa barra full-width: aplicar `padding-left: 165px` para Facebook badge
5. Probar: `bash original/iniciar_stream.sh` y verificar `http://localhost:8888/marcador.html`

---

## Archivos de referencia

| Archivo | Estado |
|---------|--------|
| `SRYiyo/marcador.html` | ✅ Referencia final — copiar diseño si se migra |
| `SRYiyo/control_remoto.html` | ✅ Referencia funcional |
| `original/control_remoto.html` | ✅ ui-ux-pro-max SVG sprite aplicado |
| `original/marcador.html` | ✅ Bug logo corregido / ⏳ Diseño TV Azteca pendiente |
| `original/config.js` | ✅ Completo — incluye ALTAVOZ_LOGO |

---

## Comando para verificar servidores

```bash
lsof -i :8890 -sTCP:LISTEN   # SRYiyo HTTP
lsof -i :8891 -sTCP:LISTEN   # SRYiyo WS relay
lsof -i :8888 -sTCP:LISTEN   # original HTTP
lsof -i :8889 -sTCP:LISTEN   # original WS relay
```

## Arranque rápido SRYiyo

```bash
cd "/Users/oleramirez/Movies/MY CLOUDE CODE/OBS_OVERLAYS_FUTBOL/SRYiyo"
bash iniciar_stream.sh
```

Panel: `http://localhost:8890/control_remoto.html`
