# tiktok-vertical — perfil OBS-nativo vertical (9:16)

Derivado de `plantilla/`. Canvas **Main** a `1080x1920` (en vez de 1920x1080) — útil
para TikTok / Reels / Shorts **sin depender del plugin StreamElements**: este perfil
es 100% automatizable por `setup_obs.py` (ver raíz `TIKTOK.md` para el contraste con
el canvas vertical de SE.Live, que es manual).

- Puertos: HTTP `8894`, WS relay `8895`.
- Colección OBS: `tiktok-vertical - TikTok`, prefijo de escenas `TT - `.
- `canvas.html` ya se adapta solo a 1080×1920 (usa `clientWidth/Height` + `devicePixelRatio`).

Arranque igual que cualquier perfil:

```bash
bash tiktok-vertical/iniciar_stream.sh        # Mac
.\tiktok-vertical\iniciar_stream.ps1          # Windows
cd tiktok-vertical && uv run setup_obs.py     # crea/actualiza la colección en OBS
```

Para crear OTRO perfil nuevo (horizontal o vertical), clona `plantilla/` o este
mismo directorio y edita solo `profile.json` (equipos, colores, puertos +2, sponsor,
`obsCollection`, y el bloque `video` si necesitas otra resolución/orientación).
`config.js`, `control_remoto.html` y `ws-client.js` se generan/copian solos al
arrancar — la única fuente de verdad es `profile.json`. Ver raíz: `CLAUDE.md`,
`MULTISYSTEM.md`, `TIKTOK.md`.
