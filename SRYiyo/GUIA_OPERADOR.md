# Guía de Operador — SRYiyo Robles Fútbol

**Última actualización:** 2026-06-02  
**Perfil:** PROVEEDORA ROBLES vs HERMANOS OSORIO — Semifinal de Ida

---

## Inicio rápido

### Antes del partido
```bash
# 1. Abre OBS Studio (si no está abierto)
# 2. Mac: corre esto
cd ~/Movies/MY\ CLOUDE\ CODE/OBS_OVERLAYS_FUTBOL/SRYiyo
bash iniciar_stream.sh

# 3. Configura Browser Sources en OBS (si es la primera vez, setup_obs.py lo hace automático)
uv run setup_obs.py

# 4. Abre el panel de control
# Mac: http://localhost:8890/control_remoto.html
# Celular con Tailscale: http://100.112.130.14:8890/control_remoto.html
```

### Barra de estado
En la parte inferior del panel verás una barra negra que dice:
- **Punto verde** = conectado al relay WebSocket ✅
- **Punto rojo** = desconectado, reconectando automáticamente
- **Ícono 📱** = toca para mostrar QR (compartir control con celular del campo)

---

## Arquitectura: Cómo funciona todo

```
Mac (control_remoto.html)         Celular en el campo (Tailscale)
      ↓                                    ↓
  http://localhost:8890          http://100.112.130.14:8890
      ↓                                    ↓
      └─────── ws_relay.py ───────────────┘
              (Puerto 8891)
                    ↓ broadcast
         OBS Browser Sources
         (marcador, evento, alineacion, etc.)
```

Los overlays corren en **OBS por HTTP** — el panel remoto envía comandos por **WebSocket**.

---

## Atajos de teclado (hotkeys invisibles)

Presiona estas teclas cuando el panel esté enfocado. **NO funcionan si estás escribiendo en un campo de texto.**

| Tecla | Acción |
|-------|--------|
| `G` | Gol local (usa el goleador seleccionado o "Jugador") |
| `H` | Gol visitante |
| `Y` | Tarjeta amarilla |
| `R` | Tarjeta roja |
| `Espacio` | Play/Pause del reloj |
| `Z` | Deshacer último evento |
| `Escape` | Limpiar todas las selecciones de chips |

**Ejemplo:** Durante el partido, el goleador local marca. Presiona `G` en lugar de hacer clic → mucho más rápido.

---

## Deshacer (Undo)

### Botón ↶ Deshacer
Visible en la barra superior. Revierte:
- **Goles:** Descuenta del marcador
- **Tarjetas:** Limpia el overlay de evento
- **Cambios:** Limpia el overlay de evento

### Limitaciones
- Historial máximo de **10 acciones**
- Se vacía al presionar **Reset Total**
- No puedes deshacer cambios del reloj

---

## Historial de eventos (Event Log)

### Botón 📋 (esquina inferior derecha)
- **Toque rápido:** Muestra el último evento
- **Doble toque o click expandido:** Muestra los últimos 15 eventos con timestamp
- Se persiste durante la sesión (sessionStorage)
- Se limpia al recargar la página

**Ejemplo del historial:**
```
⚽ 12' — GOL ROBLES — PEPE GARCIA
🟨 18' — AMARILLA — JUAN OSORIO (OSORIO)
🔄 23' — ↓CARLOS ↑DIEGO (ROBLES)
```

---

## Tabs principales

### ⚽ Goles

**Equipo Local:**
1. Toca un chip con el nombre del goleador (aparece en rojo)
2. El minuto se llena automáticamente (o edítalo manualmente)
3. Presiona **Gol Local** (o atajo `G`)

**Equipo Visitante:**
1. Escribe el nombre en el campo "Goleador — Visitante (nombre)"
2. Minuto automático (o edita)
3. Presiona **Gol Visitante** (o atajo `H`)

**En tiempo real:**
- El marcador en OBS sube automáticamente
- Aparece un banner "GOL" en la pantalla
- El evento se registra en el historial

---

### 🟨 Tarjetas

**Amarilla / Azul 2min / Roja**

**Local:**
1. Selecciona jugador (chip en rojo)
2. Minuto automático
3. Presiona el botón de tarjeta

**Visitante:**
1. Escribe nombre en "Jugador — Visitante"
2. Minuto
3. Presiona el botón

**Nota:** Las tarjetas limpian el overlay después de unos segundos automáticamente.

---

### 🔄 Cambios (Sustituciones)

**Paso a paso:**
1. Selecciona **Local** o **Visitante** (botones en la parte inferior)
2. **Si es Local:** selecciona con chip quién sale
3. **Si es Visitante:** escribe en "Jugador que SALE — Visitante"
4. Escribe quién entra en "Jugador que ENTRA"
5. Minuto automático
6. Presiona **Registrar Cambio**

**Visualización:** Aparece "↓SALE ↑ENTRA" en el overlay de evento.

---

### ⏱ Tiempo

**Panel grande en el centro:** Reloj en vivo del partido

#### Controles principales
| Botón | Acción |
|-------|--------|
| ▶️ Iniciar | Comienza el reloj (o atajo Espacio) |
| ⏸️ Pausar | Pausa el reloj (o atajo Espacio) |
| ↺ Reiniciar | Vuelve a 00:00 |
| ➡️ 2do Tiempo (45') | Salta a 45:00, cambia a "2do Tiempo" |

#### Fijar minuto manual
Escribe un número en "Fijar minuto" (0-120) y presiona el botón ⏱️ al lado.

#### Descuento (Tiempo extra)
Botones de **+1'** a **+5'** para agregar minutos. Envía el descuento a los overlays.

#### Reset
- **Reiniciar Marcador:** Vuelve score a 0-0 pero mantiene reloj
- **Reset Total:** Vuelve TODO a cero (marcador, reloj, eventos)

---

### 📋 Alineación

Muestra la formación táctica en OBS.

**Pasos:**
1. Escribe nombre del equipo (pre-llenado con equipo local)
2. Escribe formación (ej: "2-2", "1-3", "3-1")
3. DT (opcional)
4. Agrega jugadores desde abajo (+ de Agregar)
5. Presiona **Enviar Alineación**

**Los datos:**
- Automáticamente carga jugadores de la plantilla configurada arriba
- Edita números, nombres, posiciones
- Borra jugadores tocando la X

---

### 📺 Escenas

#### Countdown (Pantalla de Inicio)
Para la introducción pre-partido:
1. Escribe minutos (default 5)
2. Presiona ▶️ Iniciar Countdown
3. En OBS aparece un countdown visual en la pantalla de intro
4. Al llegar a cero, automáticamente se detiene

#### Medio Tiempo
Pantalla de descanso:
1. **Texto principal** — ej: "Descanso"
2. **Subtexto** — ej: "Analista Roberto Martínez"
3. **Badge** — ej: "Medio Tiempo" (default)
4. Presiona **Actualizar Textos** para cambiar dinámicamente
5. Presiona **Badge Medio Tiempo** para mostrar la pantalla de descanso con marcador actual

**Nota:** El badge aparece en grande sobre el fondo de alineación. Sirve para marcar el momento del descanso.

---

### 🎙 Entrevista

Operación de lower third (tercio inferior) + ticker.

#### Speaker / Entrevistado
1. Escribe **Nombre** (ej: "Roberto Martínez")
2. Escribe **Rol** (ej: "Analista", "Capitán")
3. Botones:
   - **◄ Izquierda** — speaker a la izquierda
   - **► Derecha** — speaker a la derecha
   - **✕ Limpiar** — quita el speaker

#### Tema de Entrevista (ticker)
Escribe un tema en el campo "Tema actual (ticker)" y presiona 📡 Enviar.

**Ejemplo:** "¿Por qué el equipo local presiona en los primeros minutos?"

La línea aparece como ticker en la parte superior/inferior de la pantalla.

#### Acciones Rápidas
- **🎙 ENTREVISTA EN VIVO** — muestra el badge grande
- **⚽ ANÁLISIS MEDIO TIEMPO** — badge para análisis
- **🧹 Limpiar Todo** — quita speaker, tema y badge

---

## Control remoto desde el campo (Tailscale)

### Requisitos
- Tailscale instalado y **activo** en el celular
- Mac corriendo `bash iniciar_stream.sh`
- Mac con Tailscale activo (IP: `100.112.130.14`)

### Procedimiento el día del partido

**En la Mac (antes de empezar):**
```bash
# Asegúrate que wsBindAddress sea "0.0.0.0" en profile.json
# (ya viene configurado por defecto)
bash iniciar_stream.sh
```

**En el celular del campo:**
1. Abre Tailscale → verifica "Connected" (checkmark verde)
2. Abre Chrome → `http://100.112.130.14:8890/control_remoto.html`
3. O toca el ícono 📱 en la barra inferior del panel (en la Mac) para ver un QR y escanéalo

**Automatismo de seguridad:**
- El panel detecta que es remoto (IP != localhost)
- Envía el token `***REMOVED-TOKEN***` automáticamente
- Deberías ver: `✅ Autenticado — control activo`

### Simultáneo
Ambos paneles pueden controlar al mismo tiempo:
| Dispositivo | URL |
|-------------|-----|
| Mac (mesa) | `http://localhost:8890/control_remoto.html` |
| Celular campo | `http://100.112.130.14:8890/control_remoto.html` |

Los comandos de uno se sincronizan con el otro automáticamente.

### Fallback (sin Tailscale)
Si Tailscale falla, conecta el celular al mismo WiFi que la Mac:
```bash
# En Mac, obtén tu IP local WiFi:
ipconfig getifaddr en0

# En celular: http://192.168.x.x:8890/control_remoto.html
```

---

## Flujo completo de un partido

### 1. Antes del partido (30 min)

**Checklist:**
- [ ] OBS abierto
- [ ] `bash iniciar_stream.sh` en ejecución
- [ ] `uv run setup_obs.py` completó (sources configuradas)
- [ ] Panel abierto en `http://localhost:8890/control_remoto.html`
- [ ] Status bar muestra punto **verde** (conectado)
- [ ] Tailscale activo si necesitas control remoto

**Configurar equipos:**
1. Toca "⚙ Configurar Equipos & Plantilla"
2. Rellena:
   - Equipo Local: `PROVEEDORA ROBLES`
   - Equipo Visitante: `HERMANOS OSORIO`
3. Agrega jugadores locales (número y nombre)
4. Presiona **Guardar Equipos y Plantilla**

**Escenas en OBS:**
1. Coloca Browser Source "intro.html" en la escena principal
2. Coloca Browser Source "marcador.html" (esquina superior)
3. Deja "evento_jugador.html" con visibility desactivada (se muestra solo cuando hay evento)

---

### 2. Intro / Countdown (5 min antes)

**En el panel:**
1. Tab **📺 Escenas**
2. Escribir minutos (ej: 5)
3. Presiona **▶️ Iniciar Countdown**

**En OBS:**
- La pantalla de intro muestra un countdown visual desde 5:00 hasta 0:00
- Automáticamente se detiene

---

### 3. Kickoff / Comienzo del partido

**En el panel:**
1. Tab **⏱ Tiempo**
2. Presiona **▶️ Iniciar** (o atajo Espacio)

**El reloj comienza a correr** en todos los overlays de OBS.

---

### 4. Durante el primer tiempo (45 min)

**Goles:**
- Toca chip del goleador → Presiona Gol Local (o `G`)
- El marcador en OBS sube automáticamente
- Aparece banner "GOL" en el overlay de evento

**Tarjetas:**
- Selecciona jugador → Presiona tarjeta (Y/R/Azul)
- Aparece en el overlay de evento unos segundos

**Cambios:**
- Selecciona/escribe salida y entrada
- Presiona Registrar Cambio
- Aparece "↓SALE ↑ENTRA" en overlay

**Reloj:**
- Pause con ⏸️ o Espacio si hay pausa
- Resume con ▶️ o Espacio
- Mantén actualizado si hay diferencia

---

### 5. Medio Tiempo (antes de 45')

**Aviso previo:**
1. Tab **⏱ Tiempo**
2. Presiona **➡️ 2do Tiempo (45')**

**El reloj salta a 45:00** y dice "2do Tiempo"

**Pantalla de descanso:**
1. Tab **📺 Escenas**
2. Llena textos de medio tiempo (opcional)
3. Presiona **Badge Medio Tiempo**

**En OBS:**
- Aparece "MEDIO TIEMPO" en grande sobre el marcador
- Manda a una escena de pausa visual

**Cambios tácticos:** Usa tab **📋 Alineación** para mostrar la nueva formación (opcional).

---

### 6. Segundo tiempo (90 min)

Mismo flujo que primer tiempo.
- Presiona ▶️ Iniciar para retomar el reloj
- Goles, tarjetas, cambios igual

**A los 90' o cuando termina:**
1. Presiona ⏸️ Pausar
2. (Opcional) Presiona **➡️ 2do Tiempo (45')** nuevamente si hay tiempo extra

---

### 7. Si hay penales (Semifinal)

**Procedimiento:**
1. Tab **⚡ Penales** (si existe en escenas futuras)
2. Configura: **3 o 5 kicks** por equipo
3. Operación:
   - Cada slot es: ○ (pendiente) → ⚽ (gol, verde) → ✕ (fallo, rojo)
   - Toca para marcar gol/fallo
   - Automáticamente avanza al siguiente

**Overlays:**
- Pantalla de penales con dos columnas (local | visitante)
- Visual clara de goles y fallos

---

### 8. Final del partido

**Acciones:**
1. Tab **⏱ Tiempo** → **Reset Total** (limpia todo para el próximo partido)
2. Tab **🎙 Entrevista** → **Limpiar Todo** (si la usaste)
3. Detén `bash iniciar_stream.sh` cuando termines
4. Cierra OBS

---

## Troubleshooting rápido

| Problema | Solución |
|----------|----------|
| **Punto rojo en status bar** | WS desconectado. Verifica que `ws_relay.py` corre. Si no, ejecuta `bash iniciar_stream.sh` de nuevo. |
| **Marcador no sube** | Verifica que "marcador.html" está en la escena de OBS. Recarga con F5 la Browser Source. |
| **Evento no aparece** | "evento_jugador.html" debe estar en OBS con visibility ON. Si está OFF, el evento ocurre pero no se ve. |
| **Hotkeys no funcionan** | ¿Tienes un campo de texto enfocado? Escribe en el panel → hotkeys bloqueados. Presiona Escape y prueba de nuevo. |
| **Tailscale no funciona** | ¿Tailscale está "Connected"? ¿IP es 100.112.130.14? Prueba WiFi local con `ipconfig getifaddr en0`. |
| **setup_obs.py falla** | ¿OBS está abierto? ¿Password correcto en .env? Mira el mensaje de error. Si dice "collection not found", crea manualmente en OBS. |
| **Reloj se desincroniza** | El minuto auto-fill puede no ser exacto. Usa "Fijar minuto" (tab Tiempo) para sincronizar manualmente. |
| **Chip no aparece en lista** | Ejecuta "Guardar Equipos y Plantilla" en setup. Los chips se cargan desde la plantilla. |

---

## Notas finales

### Seguridad
- Token `***REMOVED-TOKEN***` solo se envía si conectas desde una IP remota
- Localhost no necesita token (es local)
- Tailscale es privada y encriptada

### Idempotencia
- Correr `bash iniciar_stream.sh` N veces no causa problema
- `setup_obs.py` refresca sources si ya existen
- Es seguro re-ejecutar comandos

### Backup
- Plantilla se guarda en sesión (sessionStorage)
- Historial de eventos se persiste durante la sesión
- Al recargar la página, todo se reinicia

### Contacto
Si algo falla, revisa:
1. **CLAUDE.md** — configuración técnica del perfil
2. **profile.json** — source of truth para equipos, puertos, tokens
3. Logs de OBS WebSocket (verificar password)

---

**Última actualización:** 2026-06-02  
**Versión:** 1.0  
**Estado:** Listo para Semifinal de Ida PROVEEDORA ROBLES vs HERMANOS OSORIO
