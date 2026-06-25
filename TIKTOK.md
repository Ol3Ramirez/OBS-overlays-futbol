# TikTok / canvas vertical (9:16) con StreamElements

## Qué es automatizable y qué no

OBS (32.x) admite **múltiples canvases** y obs-websocket 5.7+ puede **listarlos**
(`GetCanvasList`), pero **no** puede crearlos ni configurarlos. El canvas vertical
para TikTok lo aporta el plugin **StreamElements (SE.Live)**, que se controla por su
**API propia (CEF)**, no por obs-websocket. Por eso `setup_obs.py`:

- ✅ Configura el canvas **Main** (1920×1080) y todos los ajustes generales (`profile.json`).
- ✅ **Detecta** el canvas vertical de StreamElements y avisa si está sin asignar.
- ❌ **No** puede crear/dimensionar/asignar el canvas vertical de SE (es manual, en SE.Live).

Comprobado en esta máquina: `GetCanvasList` devuelve `Main` (1920×1080) y
`⛔ SE.Live: Managed Canvas (Unassigned)` (sin dimensiones hasta asignarlo).

## Pasos manuales (una vez, en SE.Live)

1. Abre el panel **StreamElements / SE.Live** dentro de OBS.
2. Activa el **canvas Vertical (TikTok / 9:16, 1080×1920)** y asígnalo (deja de estar *Unassigned*).
3. En ese canvas vertical, agrega tus fuentes como Browser Sources:
   - Fondo animado: `http://localhost:<httpPort>/canvas.html`
     (el mismo overlay sirve: usa `clientWidth/Height` + `devicePixelRatio`, así
     se adapta solo a 1080×1920 — no hace falta un archivo aparte).
   - Marcador/eventos: reutiliza los overlays; en vertical conviene escalarlos/recortarlos
     a la zona superior. (Un marcador con layout vertical dedicado es un TODO opcional.)
4. Configura el **multistream** de StreamElements para enviar el canvas vertical a TikTok.

## Verificar

```bash
cd <perfil> && uv run setup_obs.py
# En la salida veras:
#   Canvas: Main (1920x1080)
#   Canvas: ⛔ SE.Live: Managed Canvas (Unassigned) (sin asignar)
#     -> Canvas vertical de StreamElements detectado SIN asignar. ...
```

Cuando lo asignes en SE.Live, el mismo comando mostrará sus dimensiones (p.ej. `1080x1920`).

## Alternativa sin StreamElements (OBS nativo)

Si algún día quieres un perfil **dedicado vertical** sin SE: clona un perfil
(`cp -r plantilla TikTokVertical`), pon en su `profile.json` el bloque `video` a
`1080×1920` y úsalo como colección aparte (su canvas Main sería vertical). No mezcla
con el horizontal en la misma colección, pero es 100% automatizable por `setup_obs`.
