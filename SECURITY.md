# Política de Seguridad

## Modelo de seguridad

Este proyecto está diseñado para uso en **red local (LAN)** o mediante **VPN (Tailscale)**. No está diseñado para exposición directa a internet.

## Vectores conocidos y mitigaciones

### WebSocket relay sin CORS de origen
El relay acepta conexiones de cualquier `Origin`. En LAN local esto es aceptable: el token de autenticación en `profile.json` protege contra inyección de comandos desde dispositivos no autorizados en la misma red.

**Mitigación:** Usar token fuerte (mínimo 32 caracteres hexadecimales) y cambiarlo antes de cada torneo.

### HTTP server sin autenticación
El servidor HTTP sirve todos los archivos del directorio del perfil, incluido `profile.json`.

**Mitigación:** No exponer los puertos 8888–8891 fuera de la red local. Usar firewall del sistema operativo.

### `wsBindAddress: "0.0.0.0"`
El perfil SRYiyo escucha en todas las interfaces para permitir control remoto desde el campo vía Tailscale. Esto es intencional.

**Mitigación:** El token de autenticación protege el relay. Las conexiones desde `localhost` (overlays de OBS) son auto-autenticadas.

## Antes de usar en producción

- [ ] Genera un nuevo `wsToken` con: `python3 -c "import secrets; print(secrets.token_hex(16))"`
- [ ] Actualiza `wsToken` en `profile.json` y `WS_TOKEN` en `config.js`
- [ ] Crea `.env` con `OBS_WS_PASSWORD=<tu_password>` (nunca commitear)
- [ ] Verifica que los puertos 8888–8891 **no** estén redirigidos en tu router
- [ ] Usa Tailscale para acceso remoto seguro en lugar de abrir puertos al internet

## Reportar vulnerabilidades

Si encuentras un problema de seguridad, **no lo publiques en Issues públicos**.
Contacta directamente al autor: [@Ol3Ramirez](https://github.com/Ol3Ramirez)

## Historial de cambios de seguridad

| Fecha | Cambio |
|-------|--------|
| 2026-06-15 | Token por defecto rotado de contraseña débil a token hex de 32 caracteres |
| 2026-06-15 | Documentación de seguridad creada (SECURITY.md) |
| 2026-06-15 | README público con sección de advertencias de seguridad |
