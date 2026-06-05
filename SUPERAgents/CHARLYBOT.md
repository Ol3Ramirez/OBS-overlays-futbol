# CHARLYBOT — Protocolo de Orquestación Multi-MCP
> OLE Session Intelligence | v2.1 | 2026-06-04
> Validado por: AI Engineering Agent + MCP Explorer + Advanced Protocols Architect

---

## LAS 3 LEYES DE CHARLYBOT (refinadas)

```
LEY 1 — CHARLYBOT nunca usa un MCP solo EN TAREAS COMPLEJAS.
        Regla rápida: ¿La respuesta requiere conectar puntos de múltiples fuentes?
        → SÍ → usa ≥2 MCPs
        → NO → herramientas nativas (Read/Write/Bash/Glob) son suficientes

        Nativas son suficientes cuando:
          - Leer/editar un archivo local → Read/Write
          - Ejecutar comando PowerShell → Bash
          - Listar archivos → Glob
          - Explorar un directorio conocido → Read

        Requiere ≥2 MCPs cuando:
          - URL externa → Playwright + Chrome DevTools
          - Análisis histórico → SQLite + Sequential Thinking
          - Escritura con librería → Context7 + Filesystem
          - Automatización que cruza capas (visual + red + datos) → COMBO-X

LEY 2 — Sequential Thinking cierra análisis complejos.
        ¿Cuándo exactamente? Cuando el output requiere decisión o síntesis,
        no cuando solo se extrae o transforma un dato puntual.

LEY 3 — Tres capas de persistencia, tres propósitos distintos:
        Memory MCP → grafo de entidades dinámicas (live context, tokens, sesiones)
        SQLite     → datos estructurados históricos (pagos, métricas, logs)
        MEMORY.md  → reglas y decisiones arquitectónicas del protocolo CHARLYBOT
        Archivos .md → documentación larga plazo por proyecto (SAT, FPV, etc.)
```

---

## 1. STACK ACTIVO OLE (2026-06-04)

| # | MCP | Rol en CHARLYBOT | Estado |
|---|-----|-----------------|--------|
| 1 | **context7** | Documentación de librerías en tiempo real | ✅ Activo |
| 2 | **filesystem** | Acceso a archivos fuera del CWD | ✅ Activo |
| 3 | **playwright** | Browser automation + DOM + red | ✅ Activo |
| 4 | **chrome-devtools** | Debug profundo + performance + APIs | ✅ Activo |
| 5 | **sqlite** | DB local: pagos, métricas, logs | ✅ Activo |
| 6 | **git** | Operaciones git sin terminal | ✅ Activo |
| 7 | **memory** | Grafo de conocimiento persistente | ✅ Activo |
| 8 | **sequential-thinking** | Síntesis y decisiones complejas | ✅ Activo |
| 9 | **windows-system** | Diagnóstico de sistema Windows | ✅ Activo |

### MCPs pendientes de instalar
| MCP | Paquete | Caso de uso OLE | Prioridad |
|-----|---------|-----------------|-----------|
| `youtube-transcript` | `ergut/youtube-transcript-mcp` | FPV tutoriales: 500ms vs 45s Playwright | 🔴 ALTA |
| `google-sheets` | `@modelcontextprotocol/server-google-sheets` | Sync SQLite ↔ tracker de pagos en Sheets OLE | 🔴 ALTA |
| `server-fetch` | `@modelcontextprotocol/server-fetch` | Precios AliExpress/Banggood sin overhead Playwright | 🔴 ALTA |
| `github` | `@modelcontextprotocol/server-github` | Investigación repos WISP, buscar código, crear PRs | 🟡 MEDIA |
| `brave-search` | `@modelcontextprotocol/server-brave-search` | Búsqueda web ligera (mejor que Tavily, sin costo) | 🟡 MEDIA |
| `stealth-browser` | `vibheksoni/stealth-browser-mcp` | Facebook sin detección — diferir a julio | 🟡 MEDIA |

**Comandos de instalación (Windows, cmd /c wrapper obligatorio):**
```powershell
# YouTube Transcript
claude mcp add --transport stdio --scope user youtube-transcript -- cmd /c npx -y ergut/youtube-transcript-mcp

# Brave Search
claude mcp add --transport stdio --scope user brave-search -- cmd /c npx -y @modelcontextprotocol/server-brave-search

# GitHub
claude mcp add --transport stdio --scope user github -- cmd /c npx -y @modelcontextprotocol/server-github
```

---

## 2. TABLA DE COMPATIBILIDAD — ¿Puedo ejecutar estos MCPs en paralelo?

> Hallazgo crítico del validador: Playwright + Chrome DevTools en paralelo tienen
> race conditions potenciales cuando ambos controlan el browser.

| MCP A | MCP B | Paralelo | Notas |
|-------|-------|----------|-------|
| Playwright | Chrome DevTools | ⚠️ CUIDADO | Para browser: Playwright PRIMERO, DevTools inspecciona después |
| Playwright | Filesystem | ✅ SÍ | Sin conflictos |
| Playwright | SQLite | ✅ SÍ | Sin conflictos |
| Chrome DevTools | SQLite | ✅ SÍ | Sin conflictos |
| Chrome DevTools | Sequential Thinking | ✅ SÍ | Sin conflictos |
| Memory MCP | SQLite | ✅ SÍ | Usar transacciones SQLite para consistencia |
| Context7 | Cualquiera | ✅ SÍ | Solo network, no afecta local |
| Windows System | Cualquiera | ✅ SÍ | Solo lectura, no interfiere |
| Git MCP | Filesystem | ⚠️ CUIDADO | Git DESPUÉS de cerrar cualquier archivo en edición |

**Regla:** Playwright y Chrome DevTools no compiten si Playwright navega/actúa PRIMERO y DevTools inspecciona el estado resultante.

---

## 3. CRITERIO — ¿Memory MCP, SQLite, o MEMORY.md?

| ¿Qué guardar? | Dónde | Ejemplo OLE |
|---------------|-------|-------------|
| Token/cookie de sesión activa | **Memory MCP** | Sesión Facebook logueada |
| Entidad con relaciones (proyecto ↔ pagos) | **Memory MCP** | iPhone strategy ↔ Banamex |
| Histórico numérico (métricas, pagos, logs) | **SQLite** | Todos los pagos desde 2024 |
| Resultado de análisis (para auditabilidad) | **SQLite** | Análisis fiscal junio 2026 |
| Regla del protocolo CHARLYBOT | **MEMORY.md** | Cómo usar COMBO-02 |
| Contexto de proyecto largo plazo | **Archivo .md dedicado** | SAT_Fiscal_v4.md, fpv-build.md |

---

## 4. COMBOS DE INTERACCIÓN OBLIGATORIA

---

### COMBO-01 — DUPLA WEB
**Cuándo:** Análisis o automatización de cualquier sitio web.

```
PASO 1 — Playwright (setup y navegación):
  browser_navigate([URL])
  browser_wait_for(...)    ← esperar render completo
  browser_network_requests() ← captura requests básica

PASO 2 — Chrome DevTools (inspección del estado resultante):
  list_network_requests()  ← timing + body detallado
  get_network_request(id)  ← JSON de APIs relevantes
  take_screenshot()        ← estado visual real

SÍNTESIS — Sequential Thinking:
  ¿Qué devuelven las APIs? ¿Hay tracking? ¿Acción recomendada?
```

**⚠️ Nota de compatibilidad:** No ejecutar browser_navigate de Playwright y navigate_page de DevTools al mismo tiempo. Playwright actúa, DevTools observa.

---

### COMBO-02 — DUPLA FACEBOOK (WIFI TLX)
**Cuándo:** Métricas, publicación o investigación en Facebook/Business Suite.

```
PRE-VERIFICACIÓN (siempre primero):
  Playwright: browser_navigate("https://www.facebook.com")
  Playwright: browser_snapshot()
  → Verificar que aparece nombre de usuario, NO formulario de login
  → Si hay login form → ejecutar PROTOCOLO QR (Sección 11)

PASO 1 — Cambiar contexto a página WIFITLX:
  Playwright: browser_navigate("https://www.facebook.com/WIFITLX")
  Playwright: browser_click([botón "Cambiar"])
  Señal éxito: título cambia a "(1) Facebook"

PASO 2 — Navegar a Insights:
  Playwright: browser_navigate(INSIGHTS_URL)
  Playwright: browser_wait_for(time=3)

PASO 3 — Capturar métricas:
  Playwright: browser_snapshot() + browser_take_screenshot()
  Chrome DevTools: list_network_requests(resourceTypes=["fetch","xhr"])
  Chrome DevTools: get_network_request(id) para requests a business.facebook.com/api/

PASO 4 — Persistir:
  SQLite: INSERT INTO wifi_tlx_metrics (fecha, visualizaciones, ...)

SÍNTESIS:
  Sequential Thinking: tendencia + acción concreta
```

**URLs fijas WIFI TLX:**
```
INSIGHTS:   https://business.facebook.com/latest/insights/overview/?business_id=165940872083417&asset_id=1721540274827982
POSTS:      https://business.facebook.com/latest/posts?business_id=165940872083417&asset_id=1721540274827982
PLANIFICADOR: https://business.facebook.com/latest/content_calendar?business_id=165940872083417&asset_id=1721540274827982
```

**Si Facebook cambia la URL:** Buscar "Insights" en Business Suite home, capturar nueva URL, actualizar este documento.

---

### COMBO-03 — DUPLA CÓDIGO
**Cuándo:** Escribir código con cualquier librería externa.

```
SIEMPRE ANTES DE ESCRIBIR:
  Step 1: Context7 resolve-library-id(libraryName="[nombre]")
  Step 2: Context7 query-docs(libraryId=X, query="[API específico]")
  Step 3: Filesystem directory_tree("[ruta del proyecto]")

Si la librería no está en Context7:
  Fallback → WebSearch "[librería] changelog vX.X 2025"
  Fallback → GitHub search_code "[librería] example"
```

**Por qué:** Playwright-stealth v2.x cambió `stealth_async` → `Stealth().apply_stealth_async`. Sin Context7, escribes código de v1.x que no funciona.

---

### COMBO-04 — DUPLA DATOS
**Cuándo:** Análisis de pagos, métricas históricas, cualquier consulta a claude-data.db.

```
SQLite: query("[SELECT según necesidad]")
  → Datos crudos en array

Sequential Thinking:
  Paso 1: ¿Cuáles son urgentes?
  Paso 2: ¿Hay patrón?
  Paso 3: ¿Acción concreta?
```

**Base de datos:** `C:\Users\OLE\claude-data.db`

---

### COMBO-05 — DUPLA SISTEMA
**Cuándo:** CPU alto, proceso extraño, diagnóstico de rendimiento.

```
Windows System: process_manager(sort="cpu", limit=10)
Windows System: network(active_ports=true)
Windows System: performance()

Sequential Thinking:
  ¿Proceso X usando Y% es esperado? → ¿matar? → ¿configurar?
```

**Nota:** Algunos procesos del sistema pueden no ser visibles si no hay permisos de admin.

---

### COMBO-06 — TRÍO INVESTIGACIÓN
**Cuándo:** R&D de nueva tecnología, buscar implementaciones en GitHub.
**⚠️ Requiere GitHub MCP instalado** — si no está, usar solo Context7 + WebSearch.

```
PARALELO (no dependen entre sí):
  GitHub: search_repositories("[términos]")
  GitHub: search_code("[código] lang:[lenguaje]")
  Context7: resolve-library-id("[librería base]")
  Context7: query-docs(id, "[pregunta sobre API]")

SECUENCIAL (después):
  Filesystem: directory_tree("[repo clonado]")  ← si existe local
  Memory MCP: entity_create("repo:[nombre]", findings=[...])

SÍNTESIS:
  Sequential Thinking: patrón reutilizable + código validado
```

---

### COMBO-07 — INVESTIGACIÓN COMPARATIVA (Precios/Mercados)
**Cuándo:** Comparar precios de componentes en múltiples plataformas (AliExpress vs Banggood vs Amazon).

```
PARALELO:
  WebSearch: "[producto] precio AliExpress 2026"
  WebSearch: "[producto] precio Banggood 2026"

SECUENCIAL (verificar precio real):
  Playwright: browser_navigate([URL candidata 1])
  Playwright: browser_navigate([URL candidata 2])
  Chrome DevTools: get_network_request(id) → precio desde API de precios

COMPARACIÓN:
  SQLite: SELECT precio_historico FROM precios WHERE producto = "[X]"
  Sequential Thinking:
    ¿Cuál plataforma gana? ¿Hay cupón que cambia la decisión?
    ¿El envío a México altera cuál es más barato?
    ¿Comprar ahora o esperar sale?
```

---

## 5. RITUAL DE SESIÓN (optimizado — lazy loading)

### Cold Start obligatorio (~5s)
```
ToolSearch filesystem     → operaciones de archivos
ToolSearch sqlite         → tracker de pagos (siempre relevante)
python tracker.py pendientes  → ver qué vence
```

### Lazy Loading (cargar cuando se necesita)
```
Al navegar una URL:
  ToolSearch playwright
  ToolSearch chrome-devtools

Al escribir código con librería:
  ToolSearch context7

Al analizar datos históricos o decisión compleja:
  ToolSearch sequential-thinking

Al sesión long-running / guardar entidades:
  ToolSearch memory

Al problema de sistema:
  ToolSearch windows-system

Al trabajo con git / repos:
  ToolSearch git
```

### Cierre de sesión (obligatorio para análisis complejos)
```
Sequential Thinking:
  "Sintetiza todo lo hecho en esta sesión:
   - ¿Qué descubriste?
   - ¿Qué cambió?
   - ¿Cuál es el próximo paso concreto?"
```

---

## 6. WORKFLOWS DIARIOS POR PROYECTO

### WIFI TLX — Métricas + Publicación
**Trigger:** "revisa WIFI TLX", "métricas de la página", "publica en grupos"
→ Usar **COMBO-02**. Si sesión expirada → **PROTOCOLO QR** (Sección 11).

Templates: `A:\OLE\Documents\MY CLAUDE CODE\projects\wifi-tlx-content\html\`
Grupos objetivo: Ventas Tlaxiaco (54.7k) → mercado libre (42.7k) → Tlaxiaco comunidad (12.7k)

### SAT Fiscal — Declaraciones
**Trigger:** "SAT", "declaración", "ISR", "IVA", "RESICO", "Olegario", "RARO"
→ Leer contexto SAT, luego **COMBO-04** (SQLite historial + Sequential Thinking fiscal).

### FPV Drone — Investigación + Precios
**Trigger:** "FPV", "drone", "componentes", "AliExpress FPV"
→ **COMBO-07** (comparación de precios). Archivo maestro: `fpv-drone-build.md`.

### Pagos — Tracker
**Trigger:** "pagos", "qué vence", "pague X"
→ **COMBO-04** (SQLite + Sequential). DB: `C:\Users\OLE\claude-data.db`.

### Desarrollo — Código
**Trigger:** cualquier tarea de código
→ Siempre **COMBO-03** primero. Testing → **COMBO-01**. Commits → Git MCP.

---

## 7. PROTOCOLO SIMULACION — Capas de Abstracción

### Las 6 capas y sus MCPs

| Capa | MCP | Pregunta |
|------|-----|----------|
| **Visual** | Chrome DevTools `take_screenshot` | ¿Qué ve el usuario? |
| **Red** | Playwright `browser_network_requests` | ¿Qué requests HTTP ocurren? |
| **Datos** | Chrome DevTools `get_network_request` | ¿Qué contiene el JSON? |
| **DOM** | Playwright `browser_snapshot` | ¿Qué elementos existen? |
| **Performance** | Chrome DevTools `performance_start_trace` | ¿Cuánto tarda? LCP/INP/CLS |
| **Síntesis** | Sequential Thinking | ¿Qué significa? ¿Acción? |

### Orden de ejecución

```
PARALELO (sin dependencias):
  Capa Visual (Chrome DevTools) + Capa Red (Playwright)

SECUENCIAL (después de tener IDs y estructura):
  Capa Datos (usa IDs de la Red) + Capa DOM (usa estructura de Visual)

ÚLTIMO:
  Síntesis (usa output de todas las anteriores)
```

### Prompt plantilla SIMULACION

```
Analiza [URL] con el protocolo de capas CHARLYBOT.

PARALELO:
  Visual (Chrome DevTools): navigate_page + take_screenshot
  Red (Playwright): browser_navigate + browser_network_requests(fetch/xhr)

SECUENCIAL:
  Datos (Chrome DevTools): get_network_request para APIs relevantes
  DOM (Playwright): browser_snapshot

SÍNTESIS (Sequential Thinking):
  ¿Qué es? ¿Datos reales vs visibles? ¿Tracking? ¿Acción concreta?
```

---

## 8. PROMPT TEMPLATES RÁPIDOS

### Análisis URL
```
Aplica COMBO-01 DUPLA WEB a [URL].
Playwright navega primero. Chrome DevTools inspecciona después.
Síntesis con Sequential Thinking al final.
```

### Investigación GitHub
```
Aplica COMBO-06 TRÍO INVESTIGACIÓN (GitHub disponible: SÍ/NO).
Target: [tecnología/librería]
Extraer: patrón reutilizable para stack TypeScript/Python de OLE.
```

### Debugging app local
```
App en localhost:[PORT] tiene error: [descripción]
COMBO-01 debugging mode:
  Chrome DevTools list_console_messages(type=error)
  performance_start_trace → reproduce → analyze
  Context7 para buscar fix correcto
  Git MCP para el commit final
```

### Métricas WIFI TLX
```
Ejecuta COMBO-02 DUPLA FACEBOOK.
Page ID: 1721540274827982 | Business ID: 165940872083417
Guardar resultado en SQLite tabla wifi_tlx_metrics.
Comparar con semana anterior.
```

---

## 9. TABLA DE DECISIÓN — ¿QUÉ COMBO?

| Necesito... | COMBO | MCPs requeridos |
|-------------|-------|-----------------|
| Analizar URL / sitio web | COMBO-01 | Playwright → DevTools → Sequential |
| Métricas Facebook WIFI TLX | COMBO-02 | Playwright + DevTools + SQLite |
| Código con librería externa | COMBO-03 | Context7 + Filesystem |
| Análisis de pagos / histórico | COMBO-04 | SQLite + Sequential |
| CPU alto / proceso extraño | COMBO-05 | Windows System + Sequential |
| Investigar repos GitHub | COMBO-06 | GitHub* + Context7 + Sequential |
| Precios AliExpress/Banggood | COMBO-07 | WebSearch + Playwright + SQLite |
| Video YouTube FPV | COMBO-08 (pendiente) | YouTube Transcript* + Sequential |
| Debug app en localhost | Protocolo D | DevTools + Context7 + Git |
| Sesión Facebook persistente | Protocolo B | Playwright + Memory MCP |
| Monitoreo sistema predictivo | Protocolo C | Windows System + SQLite + Sequential |

*Requiere MCP instalado.

---

## 10. PROTOCOLOS AVANZADOS — Interacciones no obvias

### PROTOCOLO A — Grafo-DB-Decisión
**MCPs:** Memory + SQLite + Sequential Thinking
**Cuándo:** Análisis que requiere histórico + patrón + decisión (ej: planning fiscal, forecast de pagos)

```
1. Memory MCP: entity_search("[contexto previo]") → entidades relacionadas
2. SQLite: SELECT datos_historicos WHERE periodo >= -6_meses
3. Sequential Thinking:
     Paso 1: Agrupar por entidad
     Paso 2: Calcular varianza y tendencia
     Paso 3: Detectar ciclo o patrón
     Paso 4: Recomendar acción
4. Memory MCP: entity_create("[InsightNuevo]", properties={patrón, confianza})
5. SQLite: INSERT INTO insights (descripcion, fecha, confianza)
```

**Output:** Regla derivada guardada en Memory + dato en SQLite + recomendación al usuario.

---

### PROTOCOLO B — Sesión Persistente entre conversaciones
**MCPs:** Playwright + Memory MCP
**Cuándo:** Facebook Business Suite requiere login QR cada vez → guardar sesión.

```
SETUP (sesión inicial, una sola vez):
  1. Playwright: browser_navigate("facebook.com") → login QR
  2. Playwright: browser_evaluate("document.cookie")
     ← browser_cookies() NO existe — validado Context7 (Playwright MCP v1 score 82.1)
  3. Memory MCP: entity_create("FacebookSession_WIFITLX", {
       cookies: [resultado de browser_evaluate],
       page_id: "1721540274827982",
       valid_until: now() + 30 days
     })

RESTAURACIÓN (sesiones posteriores):
  1. Memory MCP: entity_search("FacebookSession_WIFITLX")
  2. Si vigente: Playwright: set_cookies([...]) + navigate(insights_url)
  3. Chrome DevTools: take_screenshot() → verificar logged-in
  4. Si expirada (>30 días): volver a setup con QR
```

**Beneficio:** Elimina el QR login en cada sesión de trabajo.

---

### PROTOCOLO C — Sistema Predictivo
**MCPs:** Windows System + SQLite + Sequential Thinking
**Cuándo:** Diagnóstico proactivo de rendimiento o post-incidente.

```
SETUP INICIAL:
  1. Windows System: process_manager() × 5 snapshots (1/minuto)
  2. SQLite: INSERT INTO system_baseline (proc, cpu_avg, ram_avg, date)
     para cada proceso → baseline establecido

LOOP DE MONITOREO:
  Cada 10 segundos:
    1. Windows System: process_manager()
    2. SQLite: SELECT baseline WHERE proc = [X]
    3. Si delta > 50% del baseline:
         Sequential Thinking:
           "Proceso X subió de Y% a Z%. ¿Es esperado? ¿Acción?"
         SQLite: INSERT INTO anomaly_log (timestamp, proc, delta, analysis)
    4. Si confianza > 0.8: alertar al usuario
```

**Output:** Log histórico en SQLite + alerta con análisis y opciones (kill/reiniciar/ignorar).

---

### PROTOCOLO D — Debug-Fix Loop
**MCPs:** Chrome DevTools + Context7 + Git
**Cuándo:** App local en localhost tiene error — desde detección hasta commit.

```
1. DETECCIÓN (Chrome DevTools):
   list_console_messages(type="error")
   → Identifica: "Error in login.ts:47 — Cannot read 'email' of undefined"

2. DIAGNÓSTICO (Chrome DevTools + Sequential):
   performance_start_trace()
   → Reproduce error vía Playwright o manual
   performance_stop_trace()
   get_network_request(id) → API /user devuelve 500

3. BUSCAR FIX (Context7):
   resolve-library-id("zod") → query-docs("null safety TypeScript")
   → Pattern: z.object({...}).safeParse(data)

4. APLICAR FIX (Filesystem):
   Read(login.ts línea 40-55) → inyectar safeParse + fallback → Write

5. VERIFICACIÓN (Chrome DevTools):
   navigate_page(localhost) → list_console_messages()
   → ¿Error desapareció? ✅ → commit | ❌ → volver a paso 2

6. COMMIT (Git MCP):
   git_status() → git_diff() → git_add("login.ts")
   git_commit("fix(auth): null safety for userData parsing\n\nPrevent crash...")
```

**Output:** Bug resuelto + commit convencional con mensaje de por qué.

---

## 11. PROTOCOLOS DE ERROR — Fallbacks por escenario

### Facebook: Sesión expirada (COMBO-02)
```
Síntoma: browser_snapshot muestra formulario de login o QR request
Causa: Sesión expiró (>24h o cambio de IP)
Fix:
  1. Memory MCP: entity_search("FacebookSession_WIFITLX")
     → Si existe sesión reciente: intentar set_cookies y recargar
     → Si expirada: protocolo QR completo
  2. Playwright: browser_navigate("facebook.com") → tomar screenshot del QR
  3. Usuario escanea QR con app Facebook
  4. Playwright: wait_for(time=5) → verificar login
  5. Guardar nueva sesión (Protocolo B)
```

### Chrome DevTools: Tab cerrada / Target closed
```
Síntoma: Error "Target closed" o "No targets available"
Causa: Chrome cerró la pestaña o se reinició el proceso
Fix:
  1. Chrome DevTools: list_targets() → ver qué tabs existen
  2. Si hay tabs: navigate_page([tab existente])
  3. Si no hay tabs: abrir Chrome manualmente → relanzar combo
  4. Si hubo datos parciales: SQLite INSERT con estado="parcial"
```

### Playwright: Request timeout
```
Síntoma: browser_wait_for devuelve timeout, página no cargó
Causa: Sitio lento, red limitada, o anti-bot
Fix:
  1. Reintentar con browser_navigate + wait_for(time=10)
  2. Si sigue fallando: usar WebSearch para obtener datos públicos
  3. Registrar: SQLite INSERT INTO blocked_sites (url, timestamp, reason)
```

### Context7: Librería no encontrada
```
Síntoma: resolve-library-id devuelve null o "not found"
Causa: Librería muy nueva o con nombre diferente
Fix:
  1. Buscar en GitHub: search_repositories("[nombre librería]")
  2. Leer README directamente con Filesystem o GitHub get_file_contents
  3. Usar WebSearch: "[librería] API docs [versión]"
```

---

## 12. EXPANSIÓN — Agregar nuevos MCPs

### Proceso de instalación (Windows, cmd /c obligatorio)
```powershell
# stdio → requiere cmd /c wrapper
claude mcp add --transport stdio --scope user [NOMBRE] -- cmd /c npx -y [PAQUETE]

# HTTP → conecta a URL directamente (sin cmd /c)
claude mcp add --transport http --scope user [NOMBRE] -- [URL]

# Verificar después:
# 1. Cerrar y abrir Claude Code
# 2. ToolSearch [nombre] → debe aparecer schema
# 3. Probar con una llamada simple
```

### Template para documentar nuevo MCP
```markdown
### MCP-XX — [Nombre]
Paquete: [npm o repo]
Tipo: stdio / HTTP

Qué hace para OLE:
  [descripción específica, no genérica]

Se combina con:
  [qué MCP complementa y por qué]

COMBO asignado: COMBO-XX o Protocolo X

Casos de uso OLE:
  - [trigger 1]
  - [trigger 2]

Cuándo NO usar:
  [casos que parecen de este MCP pero no lo son]
```

---

## 13. REGISTRO CHARLYBOT — Aprendizaje continuo

> **Límite de tamaño: máximo 5 entradas activas.**
> Al llegar a 6 → mover la más antigua a `agentes/CHARLYBOT_archive.md`.
> Razón: este archivo se lee en cada sesión con MCPs — el registro crece y colapsa el context window.

### Plantilla de entrada
```
### [FECHA] — [NOMBRE DE TAREA]
COMBO USADO: [COMBO-XX o Protocolo X]
AJUSTE AL PROTOCOLO: [qué cambió respecto al template]
QUÉ FUNCIONÓ: [hallazgo concreto]
QUÉ NO FUNCIONÓ: [bloqueo o error]
LECCIÓN: [regla para la próxima vez]
ACTUALIZA SECCIÓN: [número de sección]
```

---

### 2026-06-04 — Creación y validación de CHARLYBOT v2.0

```
TAREA: Unificar MCP_TOOLS_GUIDE.md + DUPLA_METRICS_GUIDE.md + validación 3 agentes
AGENTES EJECUTADOS:
  - AI Engineering Validator → 6.5/10, identificó race condition Playwright+DevTools
  - MCP Explorer → Google Sheets + server-fetch como candidatos ALTA prioridad
  - Advanced Protocols Architect → Protocolos A, B, C, D diseñados

CAMBIOS VS v1.0:
  - Race condition documentada (Playwright → ENTONCES → DevTools, no paralelo)
  - LEY 1 refinada con heurística clara
  - LEY 3 con criterio explícito Memory vs SQLite vs MEMORY.md
  - COMBO-06 marcado como condicional (requiere GitHub)
  - COMBO-07 especializado en comparación de precios (no genérico)
  - Ritual cambiado a lazy loading
  - Sección 2: Tabla de compatibilidad
  - Sección 3: Criterio de persistencia
  - Sección 10: Protocolos avanzados A, B, C, D
  - Sección 11: Protocolos de error
  - Stack: Google Sheets + server-fetch agregados como ALTA prioridad
```

---

## FUENTES

| Documento | Ruta | Versión |
|-----------|------|---------|
| MCP_TOOLS_GUIDE.md (MELI) | `A:\OLE\Documents\MY CLAUDE CODE\projects\meli-affiliate-intel\MCP_TOOLS_GUIDE.md` | v6.0 |
| DUPLA_METRICS_GUIDE.md (WIFI TLX) | `A:\OLE\Documents\MY CLAUDE CODE\projects\wifi-tlx-content\DUPLA_METRICS_GUIDE.md` | 2026-06-03 |
| Windows MCP Rules | `C:\Users\OLE\.claude\rules\windows\mcps-windows.md` | — |
| SQLite DB | `C:\Users\OLE\claude-data.db` | — |

---

*CHARLYBOT v2.1 | Actualizado: 2026-06-04 | Handoff v2 compliant, registro con límite de 5 entradas*
