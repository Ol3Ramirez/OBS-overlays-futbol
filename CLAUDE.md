# CLAUDE.md — OBS Overlays Fútbol

Sistema de overlays en vivo para transmisiones de fútbol con OBS.
Cada subcarpeta es un **perfil/colección independiente** con sus propios equipos, colores y puertos.

## Estructura del repositorio

```
OBS-overlays-futbol/
  original/     ← Perfil original (Avila Fisioterapia · puertos 8888/8889)
  SRYiyo/       ← Robles Fútbol · Semifinal de Ida (puertos 8890/8891)
  CLAUDE.md     ← Este archivo
```

## Cómo crear un nuevo perfil

1. Copiar una carpeta existente: `cp -r SRYiyo/ NuevoPerfil/`
2. Editar `NuevoPerfil/config.js` — cambiar equipos, colores y **puertos** (+2 del anterior)
3. Arrancar con `bash NuevoPerfil/iniciar_stream.sh` (Mac) o `.\NuevoPerfil\iniciar_stream.ps1` (Windows)

## Perfiles activos

| Perfil | Sponsor | HTTP | WS | Partido |
|--------|---------|------|----|---------|
| `original/` | Avila Fisioterapia | 8888 | 8889 | Genérico |
| `SRYiyo/` | Robles Fútbol | 8890 | 8891 | Semifinal de Ida |

## OBS WebSocket global
- Puerto: `4455` (todos los perfiles usan el mismo OBS)
- Contraseña: en `~/.claude/settings.json` → `mcpServers.obs`
