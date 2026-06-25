# plantilla — perfil base para clonar

Perfil derivado de `original/`. Para crear un perfil real:

1. `cp -r plantilla NuevoPerfil`
2. Edita `NuevoPerfil/profile.json` (equipos, colores, puertos +2, sponsor, obsCollection).
3. (Opcional, control remoto con token) crea `profile.local.json` y `config.local.js` — ver `.env.example` y la raíz `CLAUDE.md`.
4. `bash NuevoPerfil/iniciar_stream.sh`  (Mac) · `.\NuevoPerfil\iniciar_stream.ps1` (Windows)
5. `cd NuevoPerfil && uv run setup_obs.py`  (crea la colección en OBS; pide el password de OBS la 1ª vez)

`config.js`, `control_remoto.html` y `ws-client.js` se generan/copian solos al arrancar.
La única fuente de verdad es `profile.json`. Ver raíz: `CLAUDE.md`, `MULTISYSTEM.md`.
