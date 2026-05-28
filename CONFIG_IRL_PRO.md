# Configuración IRL Pro — Cámara Android
### Actualizado: 28 Mayo 2026

> Abre IRL Pro en el Android, ve a **Configuración → Streaming**, y aplica estos valores exactos.

---

## ⚙️ CONFIGURACIÓN COMPLETA

| Parámetro | Valor anterior | **Valor nuevo** | Motivo |
|---|---|---|---|
| **Protocolo** | SRT | **SRT** | Sin cambio |
| **Mode** | Caller | **Caller** | Sin cambio |
| **URL / Destino** | `srt://100.112.130.14:5000` | **`srt://100.112.130.14:5000`** | Sin cambio |
| **Latencia** | 2500 ms | **4000 ms** | Ver explicación abajo |
| **Codec de video** | H.265 | **H.264** (opcional, ver nota M4) | Ver explicación abajo |
| **Bitrate de video** | 8,000 kbps | **8,000 kbps** | Sin cambio |
| **Codec de audio** | AAC | **AAC** | Sin cambio |
| **Bitrate de audio** | 128 kbps | **128 kbps** | Sin cambio |
| **EIS (Estabilización)** | Activado | **Activado** | Sin cambio |
| **Resolución** | 1080p | **1080p** | Sin cambio |
| **FPS** | 30 | **30** | Sin cambio |

---

## 📍 PASOS EN LA APP IRL PRO

1. Abrir **IRL Pro** en el Android
2. Ir a ⚙️ **Settings** (engrane inferior derecho)
3. Tocar **Stream Settings** o **Streaming**
4. **Latency / Buffer** → cambiar de `2500` a **`4000`**
5. **Video Codec** → cambiar de `H.265 (HEVC)` a **`H.264 (AVC)`**
6. Guardar y cerrar configuración
7. Verificar que **Tailscale** está activo antes de conectar

---

## 🔴 ANTES DE CADA PARTIDO

```
1. Abrir Tailscale en Android → verificar que mac-ole aparece como activo
2. Abrir IRL Pro
3. Verificar que la URL dice: srt://100.112.130.14:5000
4. Tap en "Start Streaming"
5. En OBS: Sources → SRT input → debe mostrar señal verde
```

---

## 💡 POR QUÉ ESTOS CAMBIOS

### Latencia 4000 ms

El protocolo SRT usa un buffer de latencia para recuperar paquetes perdidos. La fórmula mínima es:

```
Latencia mínima = RTT × 4
```

- RTT Tailscale entre dispositivos: ~50 ms en condiciones normales
- RTT con señal móvil débil: puede subir a **150–200 ms** con jitter
- Con 2500 ms → el buffer se agota cuando hay picos de latencia, causando cortes
- Con **4000 ms** → cubre hasta RTT de 1000 ms, eliminando prácticamente todos los cortes
- Costo: **4 segundos de delay total** entre la cámara y lo que ve el espectador (aceptable para streams de fútbol)

### Codec H.264 vs H.265 — Nota para Mac M4 (Apple Silicon)

| Característica | H.265 (HEVC) | H.264 (AVC) |
|---|---|---|
| Calidad visual | Mejor (mismos kbps) | Muy buena |
| Decode en Mac M4 | **Hardware** (VideoToolbox) ✅ | **Hardware** (VideoToolbox) ✅ |
| CPU Mac M4 | ~1% | ~1% |
| Compatibilidad | Limitada | Universal |

> **Tu Mac es M4 (Apple Silicon 2025):** tiene hardware decode para H.265 Y H.264. No hay diferencia de CPU entre los dos.

- **Si tu señal a Facebook Live es estable:** puedes quedarte en H.265 (mejor calidad visual a igual bitrate)
- **Recomendación práctica:** usar H.264 tiene mejor compatibilidad universal y es el estándar de la industria para streaming
- **Para el stream a Facebook:** OBS ya está configurado con VideoToolbox H264 en el encoder de salida (esto es lo que importa para la calidad que ven los espectadores)
- La diferencia real es en la señal IRL Pro → OBS (solo tú y OBS la ven)

---

## 🌐 RED TAILSCALE — IPs

| Dispositivo | IP Tailscale | Rol |
|---|---|---|
| `mac-ole` (Mac con OBS) | `100.112.130.14` | Receptor SRT + overlays |
| `honor-x8a-nick` (Android cámara) | `100.117.102.37` | Cámara IRL |

> El Android **debe tener Tailscale activo** antes de abrir IRL Pro. Si no, la URL SRT no conectará.

---

## 🔧 SOLUCIÓN DE PROBLEMAS

| Problema | Causa probable | Solución |
|---|---|---|
| OBS no recibe señal | Tailscale no activo en Android | Activar Tailscale, esperar 5s, reiniciar stream |
| Cortes frecuentes | Señal móvil débil | Subir latencia a 5000 ms en IRL Pro |
| Lag mayor a 6 segundos | Latencia muy alta | Bajar a 3000 ms si la señal es estable |
| Imagen pixelada | Bitrate insuficiente | Verificar que el hotspot tiene >10 Mbps de upload |
| Audio desincronizado | Latencia de red variable | Reiniciar IRL Pro y OBS |

---

*Documento generado por Claude Code · 28 Mayo 2026*
