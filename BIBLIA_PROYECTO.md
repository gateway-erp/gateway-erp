# Biblia del Proyecto — Sistema de Gestión Integral Gateway

Documento vivo donde se registra, módulo por módulo, todo lo que se va desarrollando. Al finalizar el proyecto, esta biblia sirve de base para armar el diagrama de flujo completo y la presentación de funcionalidades del software.

---

## Idea general
Sistema web propio para Gateway que reemplaza y centraliza herramientas dispersas (Word, Excel, correos). ERP/CRM simplificado orientado a empresas de servicios de seguridad electrónica. Accesible desde cualquier PC, tablet o celular sin instalación.

---

## Módulos planificados
| Módulo | Descripción | Estado |
|---|---|---|
| Presupuestos | Crear PDF, historial, pipeline kanban | **LIVE en producción** |
| OC + Factura + Cobro | Enganche al presupuesto vía pipeline | **LIVE en producción** |
| Agenda / Calendario | Mantenimientos, trabajos, asignación a técnicos, envío diario | **LIVE en producción** |
| Facturación AFIP | Integración con AFIP, alertas fiscales | Planificado |
| Layout Cámaras | Ya desarrollado — integrar como módulo del sistema | Hecho (externo) |

---

## Stack tecnológico
- **Backend**: Python 3.11 / FastAPI — hosteado en **Render** (free plan, auto-deploy desde GitHub)
- **Base de datos**: **Google Sheets** vía Service Account (`gateway-erp-bot@gateway-erp-504713.iam.gserviceaccount.com`). Planilla: `Gateway_ERP-Basededatos` (ID: `1dGgARZE2Ow-4yibOX6IM1mNd6VOLSmrPS1F4SceYrYI`)
- **Almacenamiento de archivos**: **Google Drive** — PDFs subidos automáticamente a estructura por cliente (`Clientes/C-XXXX - Nombre/Presupuestos|OC|Facturas|OP/`). El filesystem de Render es efímero; Drive es la persistencia real.
- **PDF**: ReportLab para presupuestos. pymupdf instalado (pendiente auto-extracción)
- **Frontend**: HTML + JS vanilla + CSS propio (tema navy/gris oscuro, responsive)
- **Cotización USD**: API dolarapi.com — `oficial` = billete (minorista), `mayorista` = divisa. Cache 30 min.
- **URL producción**: `https://gestion.gateway.com.ar` (CNAME → gateway-erp.onrender.com)
- **GitHub**: `gateway-erp/gateway-erp` (privado) — push a master = deploy automático
- **Autenticación**: pendiente (Google Login)
- **Diseño modular**: cada módulo con su propia lógica y permisos para poder delegar accesos por rol

---

## Estimación
4 a 6 meses, módulo por módulo, arrancando por **Presupuestos**.

---

## Registro por módulo

### Presupuestos
**Estado: LIVE en producción (gestion.gateway.com.ar) — 2026-08-13**

#### Problemas del proceso anterior (Word) que resuelve
1. Diseño se corrría al escribir → plantilla fija generada desde código
2. Tablas no simétricas → ídem
3. Sumas manuales → cálculo automático (base imponible, IVA, total)
4. IVA no precargado → por ítem, default 21%
5. Sin ítems precargados → autocompletado por aprendizaje pasivo
6. Conversión manual Word→PDF → el sistema genera el PDF directo
7. Siempre quedan hojas de más → plantilla ajustada al contenido
8. Numeración no automática → correlativo automático
9. Todas las cuentas manuales → automático
10. Conversión USD/ARS manual → cotización vía API (pendiente conectar), conversor auxiliar siempre visible

#### Flujo de carga (orden definido)
1. Fecha → validez automática (+1 mes, editable)
2. Ref. presupuesto (descripción corta, aparece en el nombre del PDF)
3. Cliente (búsqueda por nombre o código, autocompleta datos; o nuevo cliente)
4. Ítems (descripción con autocompletado de anteriores, precio unitario, cantidad, IVA)
5. Generar PDF

#### Numeración
- Formato: `PR` + año 2 dígitos + mes → `PR2607-0001`
- Reinicio mensual (26 = año 2026, 07 = julio)

#### Estructura de datos
- **Clientes**: código correlativo simple (`C-0001`), nombre, CUIT (opcional), dirección, ciudad. Buscable por código o nombre parcial.
- **Ítems sugeridos**: aprendizaje pasivo — se guardan automáticamente al cargar un presupuesto. No es catálogo administrado. Campos: descripción, precio unitario, % IVA.
- **Presupuestos**: número (auto), ref. corta, fecha, fecha validez, cliente, moneda (ARS/USD), condiciones de pago, líneas de ítem, estado (generado/enviado/aprobado/rechazado).

#### PDF generado
- Diseño igual al Word original de Gateway (mismo logo, grilla, campos)
- El PDF de salida NO muestra campo Incoterm (eliminado)
- Pie de página siempre fijo al fondo de la hoja (condiciones de pago + caja firma + totales)
- Caja firma y bloque de totales tienen la misma altura
- Nombre del archivo: `PR2607-0001 - Notebook LENOVO.pdf`
- Logo extraído del PDF original y guardado en `assets/logo_gateway_0.png`

#### Moneda y cotización
- Selector ARS / USD en el formulario
- Conversor auxiliar permanente en el sidebar (USD ↔ ARS) — no se extrapola al presupuesto, solo es herramienta de apoyo
- Cotización: placeholder manual por ahora. **Pendiente**: conectar API del dólar (el usuario va a indicar la fuente)

#### Archivos del módulo
```
Software-gestion/
  main.py                        ← Backend FastAPI (rutas, lógica, endpoints API)
  start.py                       ← Entrypoint que lee PORT del env (para hosting)
  presupuestos/
    generar_pdf.py               ← Generación de PDF con ReportLab
    output/                      ← PDFs generados
  templates/
    nuevo_presupuesto.html       ← Formulario web (HTML + JS vanilla)
  static/
    style.css                    ← Estilos (diseño navy/gris, responsive)
    logo.png                     ← Logo Gateway
  assets/
    logo_gateway_0.png           ← Logo extraído del PDF original
  data/                          ← Base de datos temporal en JSON (migrar a Sheets)
    clientes.json
    items_sugeridos.json
    historial.json
    counters.json
  .venv/                         ← Entorno virtual Python 3.14
  .claude/launch.json            ← Config servidor dev local (puerto 8000, autoPort)
```

#### Dependencias instaladas
```
fastapi, uvicorn, jinja2, python-multipart
reportlab, pillow
pymupdf
```

#### Decisiones de diseño del PDF
- Fondo: `#EEF0F4`, grilla `#B0B8C6`, alternancia filas gris claro `#E4E8EE`
- Logo: `Logo-Gateway.jpeg` (en raíz del proyecto), con fallback a `assets/logo_gateway_0.png`
- Dirección: Berutti 974, 2804 Campana
- IMPORTANTE: bloque de ancho completo con `<b>IMPORTANTE: </b>` inline en ReportLab
- Pie fijo: condiciones de pago + caja firma + totales (base + IVA por alícuota + total navy)

#### Cotización USD en el formulario
- Dos pestañas: Billete (minorista) y Divisa (mayorista)
- Al cambiar de pestaña se recalcula el conversor si tiene valor ingresado
- Boxes de compra/venta con fondo gris oscuro y borde para contraste

#### Archivos del módulo (estado actual)
```
main.py                    ← FastAPI: rutas, endpoints pipeline, lógica de negocio
db.py                      ← Toda la lógica de Sheets: clientes, items, historial, facturas
drive.py                   ← Integración Drive: subir_presupuesto(), subir_documento()
cotizacion.py              ← API dolarapi.com con cache 30 min
presupuestos/generar_pdf.py ← ReportLab PDF
templates/
  nuevo_presupuesto.html   ← Formulario de carga con autocomplete y conversor
  dashboard.html           ← Dashboard kanban (vista principal)
static/style.css           ← Estilos del formulario
Logo-Gateway.jpeg          ← Logo oficial (en raíz)
requirements.txt           ← Dependencias Python (incluye google-api-python-client)
runtime.txt                ← Python 3.11 (fuerza versión en Render)
```

---

### Pipeline Presupuesto → OC → Factura → Cobro
**Estado: LIVE en producción — 2026-08-13**

#### Flujo de estados
```
Enviado → Aprobado → Facturado → (cobrado 🟢 / pendiente cobro 🔴)
        ↘ Rechazado (colapsado al pie del kanban, conservado para reflotar)
```

- **Enviado**: estado inicial automático al generar el PDF
- **Aprobado**: cliente confirmó verbalmente o con OC formal. El operador registra N° OC, fecha, monto y opcionalmente sube el PDF de la OC.
- **Facturado**: se emite factura Gateway (puede haber N facturas por presupuesto — ej. insumos + mano de obra). El operador registra N° factura, fechas y opcionalmente sube el PDF.
- **Cobrado**: se registra la Orden de Pago del cliente, con retenciones desglosadas por tipo. El sistema calcula el monto neto automáticamente.

#### Vista kanban del dashboard
- 3 columnas: Enviados / Aprobados / Facturados
- Rechazados colapsados al pie (toggle)
- Dot verde 🟢 = todas las facturas del presupuesto cobradas; rojo 🔴 = alguna pendiente; gris = sin OP registrada
- Botón "Editar OC" en Aprobados para corregir datos sin cambiar de estado

#### Modelo de datos — hojas en Google Sheets

**Hoja `historial`** (presupuestos + datos OC):
```
numero | ref_cliente | fecha | fecha_validez | codigo_cliente |
moneda | condiciones_pago | cliente_nombre | archivo | estado | total | drive_link |
oc_numero | oc_fecha | oc_monto | oc_drive_link
```

**Hoja `facturas`** (N:1 con presupuesto — 1 fila por factura):
```
presupuesto_numero | fact_numero | fact_fecha | fact_vto_pago | fact_monto |
fact_drive_link | op_numero | op_fecha | op_monto_bruto |
ret_ganancias | ret_iibb | ret_seghigiene | ret_otros |
op_monto_neto | op_drive_link | ret_drive_link_1 | ret_drive_link_2 | cobro_ok
```

`op_monto_neto = op_monto_bruto - (ret_ganancias + ret_iibb + ret_seghigiene + ret_otros)`

#### Relaciones entre documentos
- 1 Presupuesto → 1 OC → N Facturas → cada Factura tiene 1 Orden de Pago (1:1)
- Si hay 2 facturas (insumos + mano de obra) → 2 filas en hoja facturas, cada una con su propia OP

#### Estructura de carpetas en Google Drive
```
Datos_Software_ERP/ (raíz: 14UwyCzQ0CvKF6vFQHEeqfWiHbs2PoMwI)
  └─ Clientes/
       └─ C-0001 - TOYOTA BOSHOKU/
            ├─ Presupuestos/        ← PDFs de presupuestos Gateway
            ├─ Ordenes de Compra/   ← PDFs de OC del cliente
            ├─ Facturas/            ← PDFs de facturas Gateway
            └─ Ordenes de Pago/     ← OP + Certs. Retención del cliente
```
Carpetas creadas automáticamente al subir cada documento. Los PDFs son públicos "anyone with link can view".

#### Endpoints del pipeline
```
POST /api/rechazar/{numero}    ← Cambia estado a "rechazado"
POST /api/aprobar/{numero}     ← Registra OC, cambia estado a "aprobado"
                                  Form: oc_numero, oc_fecha, oc_monto, archivo (PDF)
POST /api/facturar/{numero}    ← Registra factura, cambia estado a "facturado"
                                  Form: fact_numero, fact_fecha, fact_vto_pago, fact_monto, archivo
POST /api/cobrar/{numero}      ← Registra cobro en hoja facturas
                                  Form: fact_numero, op_numero, op_fecha, op_monto_bruto,
                                        ret_ganancias, ret_iibb, ret_seghigiene, ret_otros,
                                        archivo_op, archivo_ret1, archivo_ret2
GET  /api/facturas/{numero}    ← Lista facturas de un presupuesto
GET  /debug-error              ← Diagnóstico: cuenta historial y facturas en Sheets
```

#### Documentos reales analizados (para futura auto-extracción con pymupdf)
- **Toyota TBAR**: OC formato SAP (4500073819) con N° OC, fecha, monto claramente identificables
- **Toyota OP**: Orden de Pago Toyota (formato PDF estructurado)
- **Swetech**: OP con retenciones embebidas en el mismo PDF
- **Master Bus**: OP + Cert. Retención Ganancias + Cert. Retención IIBB (3 PDFs separados)
- **Facturas Gateway**: formato AFIP FCE MiPyMEs tipo A (COD 201) y Factura A (COD 01). N° OC embebida en descripción del ítem.

#### PDFs en Render (filesystem efímero)
Los PDFs generados en `presupuestos/output/` se pierden con cada redeploy. La fuente de verdad es Google Drive. Los presupuestos generados a partir del 2026-08-06 tienen `drive_link` persistente. Los anteriores (de prueba) no tienen recuperación.

---

### Facturación AFIP
**Estado: planificado.**

- Facturas vinculadas a OC
- Alerta de límite mensual de facturación antes de emitir
- Cálculo estimado de Ingresos Brutos
- Proyección IVA compras vs. IVA ventas para planificación fiscal
- Integración AFIP a evaluar

---

### Agenda / Calendario
**Estado: LIVE en producción (gestion.gateway.com.ar/agenda) — 2026-09-27**

#### Qué resuelve
El operador tiene mantenimientos mensuales fijos (los que sostienen la facturación recurrente — CCTV, red de incendios, UPS, etc.) que **no se pueden posponer**, mezclados con trabajos random del día a día. Antes no había forma de que el sistema recuerde solo "te falta este mantenimiento", todo dependía de la memoria del operador.

#### Vista semanal (no mensual)
Se descartó la grilla de mes completo: el operador necesita ver "qué hice ayer y anteayer" junto con "qué viene", así que la vista principal es **la semana actual (lunes a viernes)**, con navegación `‹ semana anterior` / `Hoy` / `semana siguiente ›`. El mes se sincroniza solo tomando como referencia el miércoles de la semana visible (evita ambigüedad cuando la semana cruza de un mes a otro).

#### Dos modos: Automático / Manual (switch en el header)
- **Automático**: al abrir un mes vacío, ofrece completar todas las visitas del mes con fecha ya asignada (el lunes de la semana que le corresponde a cada mantenimiento según su patrón).
- **Manual**: el botón equivalente ("+ Generar pendientes del mes") crea los mismos registros pero **sin fecha** — quedan en la sección "Pendientes sin fecha asignada" y el operador los ubica día por día haciendo click en cada uno (abre el mismo modal que en modo automático: elegís fecha + turno).
- El modo se guarda en `localStorage` del navegador, no es global del sistema.

#### Auto-validación día a día
Si una visita quedó "pendiente" con fecha ya pasada y nadie la tocó (no la marcó realizada, vencida, ni la reprogramó), el sistema la da por **realizada automáticamente** al otro día. Usa comparación de fechas absolutas (`fecha_real < hoy`), así que no se rompe cuando una semana cruza de un mes a otro.

#### Arrastre entre meses (distinto de la auto-validación)
Solo lo que **nunca tuvo fecha asignada** (o quedó "vencido" sin resolver) viaja al mes siguiente, en una sección aparte ("↩ Arrastrados de meses anteriores"). No se confunde con la auto-validación: esa resuelve lo que sí se hizo pero no se marcó; el arrastre es para lo que genuinamente no se completó. Al resolverlo desde el mes nuevo, el registro se actualiza en su mes de origen — el historial por mes queda intacto en la Sheet, que funciona como backup natural (nada se borra nunca).

#### Generador de mensaje para WhatsApp
Selector de día (hoy + próximos 14 hábiles) + campo de nota libre → arma el texto agrupado por equipo técnico, listo para copiar y pegar al grupo:
```
📅 *MARTES 30/09/2026*

👷 *CAMILO + PABLO*
  • TBAR RED INCENDIOS (4hs)

📌 Recuerden llevar los insumos y pasar por mi casa
```

#### Mantenimientos precargados (seed fijo, 6 registros)
| Mantenimiento | Cliente | Hs/mes | Patrón semanal | Técnicos |
|---|---|---|---|---|
| TBAR CCTV | Toyota Boshoku | 32 | todas las semanas | Camilo + Pablo |
| TBAR RED INCENDIOS | Toyota Boshoku | 8 | semanas 2 y 4 | Camilo + Pablo |
| TBAR MTTO UPS | Toyota Boshoku | 4 | semanas 1 y 3 | Camilo + Pablo |
| TBAR SIST. INCENDIOS | Toyota Boshoku | 8 | semanas 1 y 3 | Camilo + Pablo |
| MCCAIN CCTV | McCain | 32 | semana 3 (2 visitas) | Camilo + Pablo |
| MASTER BUS | Master Bus | 8 | semanas 1 y 3 | Matías + Nacho |

Nombres de técnicos ficticios por pedido del usuario (discreción).

⚠️ **Las horas NO cierran matemáticamente entre `horas_plan` y (técnicos × horas reales × visitas) — es intencional, no arreglar.** Ejemplo: TBAR CCTV sí cierra (2 técnicos × 4hs media mañana × 4 visitas = 32hs). Pero RED INCENDIOS, UPS, SIST. INCENDIOS y MASTER BUS están facturados/contratados a un número de horas mensuales "de catálogo" que NO coincide con lo que realmente se trabaja en campo (2 técnicos × media mañana × 2 visitas = más horas reales que las contratadas). El operador confirmó esta discrepancia y pidió manejarla **basándose en la cantidad de visitas (`semanas_mes`), no en las horas** — las horas (`horas_plan`, `horas_visita`) son solo una etiqueta informativa que se muestra en la UI, ninguna lógica de programación depende de que ese número sea preciso. No intentar "corregir" `horas_visita` para que la cuenta cierre.

#### Modelo de datos — hojas en Google Sheets
**Hoja `mantenimientos`** (catálogo fijo, se siembra solo si falta):
```
id | nombre | cliente | horas_plan | semanas_mes | tecnicos | prioridad | horas_visita | semanas_pattern
```
`semanas_pattern` usa `;` como separador (ej. `1;2;3;4`), **nunca coma** — ver problema resuelto más abajo.

**Hoja `mant_visitas`** (una fila por visita programada, por mes):
```
mant_id | año | mes | semana | visita_num | fecha_real | estado | turno
```
`estado`: `pendiente` / `realizado` / `vencido`. `turno`: `mañana` / `tarde`.

**Hoja `agenda_celdas`** (trabajos libres/random, ya existía del calendario general):
```
año | mes | dia | turno | texto | color | negrita
```

#### Endpoints
```
GET  /agenda                              ← página completa
GET  /api/agenda/{anio}/{mes}             ← trae mantenimientos + visitas + celdas + arrastrados
                                             (auto-valida día a día antes de devolver)
POST /api/agenda/celda                    ← guarda texto libre de un día
POST /api/agenda/visita                   ← asigna/edita fecha, turno o estado de una visita
POST /api/agenda/auto-fill/{anio}/{mes}   ← genera visitas del mes
                                             ?asignar_fecha=true  → modo Automático
                                             ?asignar_fecha=false → modo Manual (sin fecha)
```
Nota: el parámetro de path se llama `anio` (no `año`) — ver problema resuelto.

#### Navegación unificada
Las 7 pantallas del sistema (Presupuestos, Nuevo Presupuesto, Matrices, Matriz, Clientes, Remitos, Agenda) usan el mismo patrón para volver al inicio: logo clickeable con etiqueta `‹ Inicio` visible debajo (no solo al pasar el mouse), consistente en todas.

#### Problemas resueltos durante el desarrollo (dejar registrado — no repetir)
1. **Ruta con "ñ" nunca matcheaba** (`/api/agenda/{año}/{mes}` devolvía 404 aunque aparecía en el schema de OpenAPI). FastAPI/Starlette listaban la ruta pero el router nunca la resolvía en runtime. Se renombró el parámetro a `{anio}` (ASCII) en todas las rutas con path params — evitar `ñ`/tildes en nombres de parámetros de ruta en este proyecto.
2. **Google Sheets corrompía `semanas_pattern`**: al escribir `"1,2,3,4"` con `value_input_option=USER_ENTERED`, Sheets lo interpretaba como el número `1234` (locale es-AR usa coma como separador de miles). Fix: separador `;` en vez de `,`, más comilla inicial forzada (`'1;2;3;4`) al escribir para garantizar texto plano, con reparación automática de filas ya corrompidas en cada carga.
3. **Cuota de lecturas de Google Sheets agotada (429)**: `_ws()` reabría la planilla completa (`open_by_key`, ~1 request) y releía encabezados en **cada** llamada. Una sola carga de `/agenda` hacía ~21 llamadas a la API; tocar "Completar mes" sumaba otra tanda y volaba el límite por minuto. Fix: spreadsheet cacheado a nivel de proceso, verificación de encabezados una sola vez por hoja, y `cargar_agenda_completa()` que consolida las 4 lecturas separadas de `mant_visitas` (auto-validar x2 + visitas + arrastrados) en 1 sola. Bajó de ~21 a ~3 llamadas por carga de página. `auto_fill_mes` también pasó de N escrituras individuales a un solo `append_rows()` en batch.

#### Ajustes de UX posteriores (2026-09-27, misma noche)
Hechos en otra sesión de Claude Code sobre el mismo directorio (commits `8ff40d5` y `f673759`), documentados acá para que quede todo junto:

- **Dashboard, vista 2 columnas (agenda + presupuestos)**: antes scrolleaba como una sola página larga. Ahora `#page-root.vista-2` tiene altura fija (`calc(100vh - 64px)`) y cada columna scrollea de forma independiente (`overflow-y: auto` propia). Se sacó el `position: sticky` de la agenda. `setVista()` bloquea el scroll del body al entrar en vista-2 y lo libera al salir.
- **Dashboard tiene su propio widget de mantenimientos** (`#agenda-mant`, dentro de la agenda operativa del dashboard — distinto de la página `/agenda`). Al hacer click en una semana abría un `prompt()` nativo feo y sin control de estado. Se reemplazó por un modal propio (mismo patrón que el de `/agenda`): fecha, turno, botones Realizado / Guardar fecha / Desmarcar / Cancelar. Funciones nuevas en `dashboard.html`: `aClickVisita()`, `mmSetTurno()`, `mmCerrar()`, `mmAccion()`.
- **`/agenda` — generador de WhatsApp**: el dropdown de días empezaba desde hoy; ahora empieza desde mañana (no tiene sentido mandar el mensaje del día para "hoy" a esta altura de la jornada).
- **`/agenda` — modal de fecha**: el input `type="date"` ahora tiene `min` = hoy, no deja seleccionar fechas pasadas al asignar una visita.

⚠️ **Nota de arquitectura que quedó pendiente de resolver**: el dashboard tiene su propio mini-calendario de mantenimientos (`#agenda-mant`) que ahora también tiene modal de edición, en paralelo a la página `/agenda` completa. Son dos UIs distintas escribiendo sobre las mismas hojas (`mantenimientos`, `mant_visitas`). Falta decidir si conviene unificarlas o si el dashboard queda como vista rápida y `/agenda` como la vista completa a propósito.

#### Segunda vuelta de fixes (2026-09-27, mismo día)
1. **El scroll de vista-2 seguía roto**: la altura fija `calc(100vh - 64px)` de `#page-root.vista-2` no descontaba el alto de la barra de post-its (`#notas-bar`) cuando está visible. Con post-its activos, el contenido total superaba el viewport y la parte baja de "Mantenimientos del mes" quedaba inalcanzable — bloquear solo `body.style.overflow` no evita el scroll de documento si el contenido real es más alto que lo calculado. Fix: `ajustarAlturaVista2()` mide el alto real por JS (topbar + notas-bar si está visible) y fija la altura de `#page-root` de forma inline, recalculando en `renderNotas()`, `ocultarNotas()` y `resize`. También se bloquea `overflow` en `<html>`, no solo en `<body>`.
2. **Layout de mantenimientos del dashboard cambiado a horizontal**: antes era una columna angosta (270px) al costado del calendario con su propio scroll interno — competía con el scroll del contenedor y era parte del problema del punto 1. Ahora `.agenda-body` es columna (calendario arriba a todo el ancho, mantenimientos abajo), y `.agenda-mant` es una fila flex-wrap donde cada card mide 260px fijo y pasa a la siguiente fila si no entra. Un solo scroll vertical para todo el bloque de agenda, mucho más simple.
3. **Dato corrupto en Sheets**: la visita de TBAR CCTV semana 1 (sept. 2026) tenía guardada `fecha_real: "2016-09-28"` (año mal tipeado, probablemente al probar el modal nuevo) con `estado: "realizado"` — por eso aparecía siempre en verde sin importar qué mes se recargara. Reseteada a `pendiente` sin fecha vía `POST /api/agenda/visita`. Si vuelve a pasar algo similar: revisar `fecha_real` de las visitas directamente contra `GET /api/agenda/{año}/{mes}`, ese campo es la fuente de verdad de lo que se ve en pantalla.
4. **Etiqueta bajo el logo**: pasa de "‹ Inicio" a "Dashboard" en las 7 pantallas, incluyendo el propio dashboard (ahí no lleva a ningún lado nuevo, pero funciona como indicador de "estás acá"). Corrección posterior: el tab del nav que iba a "/" decía "Presupuestos" — se renombró a "Dashboard" y se sacó la etiqueta chica redundante del dashboard mismo (queda solo en las otras 6 pantallas).

#### Tercera vuelta — unificación dashboard/agenda y generador WhatsApp con equipos (2026-09-27/28)

**Decisión de arquitectura**: el dashboard **no edita nada** — es solo informativo (nombre, cliente, cantidad real de visitas, circulitos de estado). Toda la edición de mantenimientos vive únicamente en `/agenda`. Se sacó el modal de mantenimiento del dashboard (`mant-overlay`, `aClickVisita`/`mmSetTurno`/`mmCerrar`/`mmAccion`) y el onclick de las cards. **Pendiente**: falta que el widget del dashboard linkee a `/agenda` al hacer click (paso 2 de 2).

**Fix — cards mostraban 4 semanas fijas**: el dashboard pintaba siempre "Sem 1..4" aunque la mayoría de los mantenimientos tienen 2 visitas/mes reales, y encima `aVisitas` se indexaba solo por `mantId-semana` (sin `visita_num`), así que MCCAIN (2 visitas en la misma semana) perdía una por colisión. Fix: `aVisitasEsperadas(m)` calcula la cantidad real y en qué semanas caen a partir de `semanas_pattern` (mismo cálculo que `auto_fill_mes` del backend), las cards muestran "Visita 1..N" en vez de "Sem 1..4".

**Fix — colores de estado no coincidían entre dashboard y `/agenda`**: cada página tenía su propia heurística de color (el dashboard adivinaba según "semana actual del mes"; `/agenda` pintaba ámbar a cualquier cosa no realizado/vencido). Unificado en los dos lugares con una sola regla: **verde=realizado, ámbar=programado (tiene fecha asignada), rojo=vencido o sin programar todavía**. Funciones `aEstadoVisual()` (dashboard) y `estadoVisual()` (agenda) — misma lógica, no se puede compartir código entre templates así que están duplicadas a propósito, mantenerlas en sync si se toca una.

**Feature — generador de WhatsApp con equipos manuales**: rediseño completo del panel "Mensaje para el grupo" en `/agenda`. Caso real del operador: puede haber **2 equipos trabajando el mismo día** (ej. MCCAIN se lleva un equipo entero a una zona lejana, el otro equipo queda trabajando en la zona habitual; los fines de semana también puede pasar). Diseño:
- Cada equipo es un bloque independiente con 4 checkboxes (Camilo/Pablo/Matías/Nacho) — el operador elige a mano quién va, sin depender de la asignación fija (`tecnicos`) del mantenimiento.
- Tareas por equipo, agregadas de dos formas: **"+ Desde pendientes"** (selector con TODOS los pendientes del sistema, no solo los de ese día — un click asigna la fecha del día elegido automáticamente) o **texto libre** (para trabajos que no son mantenimientos).
- Al asignar una tarea pendiente vía este selector, la visita pasa a tener `fecha_real` = el día elegido, queda en estado "pendiente" (se ve ámbar/"próximo"). La auto-validación existente (`cargar_agenda_completa`) la pasa sola a "realizado" cuando el sistema detecta que la fecha ya pasó y nadie la tocó — no hace falta lógica nueva para esto.
- Sacar una tarea del mensaje (✕) vuelve a vaciar su `fecha_real` — no queda una asignación huérfana en la Sheet.
- Al cambiar el día seleccionado, los equipos se auto-completan según lo que ya esté programado ese día (agrupado por el campo `tecnicos` de cada mantenimiento), y desde ahí son editables — no hay que armar todo de cero si ya había algo cargado.
- Funciones nuevas en `agenda.html`: `wsPoblarDesdeDia()`, `wsAgregarEquipo()`, `wsQuitarEquipo()`, `wsToggleTecnico()`, `wsAgregarTareaPendiente()`, `wsQuitarTarea()`, `wsAgregarLibre()`, `renderWsEquipos()`, `wsPendientesPool()`.
- Probado en vivo: 2 equipos el mismo día (Camilo+Pablo con un mantenimiento real, Matías+Nacho con texto libre) generan el mensaje agrupado correctamente.

**Ajustes posteriores al generador de WhatsApp (2026-09-28):**
- **Turno por tarea, no por equipo**: el mismo equipo puede hacer una tarea a la mañana y otra a la tarde (ej. Camilo+Pablo con un mantenimiento a la mañana y otro trabajo distinto a la tarde). Cada tarea tiene su propio toggle ☀️/🌙, no el equipo entero. Función `wsSetTareaTurno(idx, tIdx, turno)`.
- **Botón "+ Agregar" explícito para texto libre**: el Enter-only no era descubrible. Se agregó un botón visible al lado del input (el Enter sigue funcionando).
- **Botón "✓ Confirmar tareas"**: antes cada tarea elegida desde pendientes se guardaba sola en el momento de elegirla, sin instancia de revisión — confuso, no quedaba claro qué había impactado en el calendario. Ahora armar el mensaje (equipos, tareas, turnos) queda todo en memoria (campo `confirmado:false` en cada tarea-mantenimiento) hasta apretar "Confirmar tareas", que recién ahí guarda todo en la Sheet de una vez y refresca grilla/pendientes/resumen. Las tareas sin confirmar se marcan con borde ámbar + etiqueta "sin confirmar". Cambiar el turno de una tarea ya confirmada la vuelve a marcar `confirmado:false` (necesita reconfirmarse para persistir el cambio).
- **Formato del mensaje**: cada línea de tarea va en negrita+cursiva (`_*texto*_`) para resaltar, y el turno se muestra como emoji + etiqueta chica (`☀️ _T-Mañana_` / `🌙 _T-Tarde_`) en vez de ir solo el ícono.

#### Bug grave — semana que cruza de mes perdía datos (2026-09-28)
El usuario preguntó 4 cosas de arquitectura que destaparon este bug: **la vista semanal solo pedía datos de UN mes** (`syncMes()` usa el mes del miércoles de la semana visible), así que cuando la semana tenía días de dos meses (ej. mié 30/09 a vie 2/10), los días del mes "siguiente" (jueves y viernes, ya en octubre) se mostraban vacíos aunque tuvieran mantenimientos o texto libre guardado — porque esos datos nunca se pedían al servidor. Con fecha real 2026-09-28, la semana actual cruzaba justo este límite, así que se pudo reproducir y confirmar el fix en vivo.

**Fix (agenda.html):**
- `cargar()` ahora arma la lista de todos los `{año,mes}` que toca la semana visible y pide `/api/agenda/{año}/{mes}` para cada uno con `Promise.all`, mergeando `visitas`/`celdas` de todos los meses involucrados. `mants` sale del primer fetch (catálogo, es igual en todos los meses). `arrastrados` sale del fetch del mes MÁS TARDÍO de los combos (como su definición es "todo lo anterior a este mes", ya cubre a los meses anteriores del combo).
- `doAutoFill()` ya no reemplaza `visitas` entero — solo la porción del mes que autocompletó, para no pisar los datos del otro mes ya mergeados.
- `saveVisita()` reescrito para matchear siempre por clave completa (`mant_id+año+mes+semana+visita_num`) en vez de asumir que todo pertenece al "mes actual" — evita que dos meses con el mismo número de semana (1-4, se repite cada mes) se confundan entre sí.
- `renderResumen()` y `renderPendientes()` filtran explícitamente `visitas` al mes "principal" (`año`/`mes` global) antes de calcular — son widgets de resumen MENSUAL, no deben mezclar datos de 2 meses aunque la semana los cruce.
- `guardarLibre()` ahora compara año (no solo día+mes) al buscar la celda en el array local — antes el día 30 de un mes podía confundirse con el día 30 de otro.
- `wsPendientesPool()`: usaba el año/mes global para TODAS las entradas de `visitas` en vez del propio de cada registro (bug latente, quedaba enmascarado cuando solo había 1 mes cargado). Al mergear 2 meses, esto causaba que el mismo pendiente apareciera duplicado en el selector "+ Desde pendientes" (una vez vía `visitas`, otra vía `arrastrados`, con años/meses mezclados). Fix: usar `v.año`/`v.mes` de cada registro + un solo `Set` de deduplicación compartido entre ambas fuentes.

**Fix (db.py):**
- Un "arrastrado" deja de considerarse tal apenas tiene `fecha_real` asignada — antes el filtro solo miraba `año/mes` + `estado`, así que algo recién programado para el mes siguiente seguía apareciendo como "arrastrado sin resolver" aunque ya estuviera agendado.
- Sacado código muerto: `auto_validar_visitas()` y `load_pendientes_arrastrados()` como funciones standalone — ya estaban inlineadas dentro de `cargar_agenda_completa()` desde el fix de cuota de Sheets, estas versiones sueltas no se llamaban desde ningún lado.

#### Gap real — texto libre del generador de WhatsApp no se guardaba en ningún lado
El usuario cargó una tarea de texto libre en el generador de WhatsApp y no la vio reflejada en el calendario — tenía razón, ese texto nunca se persistía, solo vivía en el mensaje compuesto en memoria del navegador. Fix: al apretar "Confirmar tareas", el texto libre de cada equipo se concatena y se agrega al campo "trabajo libre" del día elegido (mismo campo que la grilla semanal ya mostraba), así queda visible ahí y sobrevive a un reload. Limitación conocida y aceptada: si luego se saca esa tarea del compositor, NO se revierte el texto ya agregado a la celda (el campo es un blob de texto libre por día, no itemizado) — el operador puede editarlo directamente en la grilla si hace falta sacar algo.

⚠️ **Aclaración importante de esta sesión**: hay DOS calendarios de texto libre distintos en el sistema y es fácil confundirlos:
1. El calendario general del **dashboard** (celdas M/T por día, tabla mensual) — siempre fue editable directamente ahí, nunca estuvo en el alcance de "todo se edita solo en /agenda". Es una función de notas libres sin relación con mantenimientos.
2. El campo "trabajo libre" por día dentro de **`/agenda`** (grilla semanal) — es el que alimenta el generador de WhatsApp y donde ahora también aterriza el texto libre confirmado desde el compositor de equipos.
Ambos escriben a la misma hoja `agenda_celdas`, pero currently no está unificada la experiencia entre uno y otro — quedó como posible ítem a evaluar más adelante si generan confusión.

#### Bug grave #2 — mantenimiento reprogramado a OTRO mes era invisible en ese mes (2026-10-02)
Variante más amplia del bug de semana-cruzando-mes: el usuario reprogramó un mantenimiento de septiembre para el **5 de octubre** (vía el generador de WhatsApp, un mes de diferencia, no solo una semana). La fila sigue "perteneciendo" a septiembre en la Sheet (año/mes de origen, por diseño — ver más abajo), pero el dashboard al mirar **octubre completo** nunca la encontraba, porque `cargar_agenda_completa(año,mes)` filtraba estrictamente por año/mes de la fila, sin mirar nunca a dónde apunta realmente `fecha_real`.

**Fix (db.py → `cargar_agenda_completa`):** además de las filas nativas del mes pedido, ahora también se incluyen filas de **otro mes de origen** cuya `fecha_real` caiga dentro del mes pedido. No se mueve la fila físicamente (seguiría bookkeeped en septiembre) — solo se la incluye también en la respuesta cuando se pide octubre, para que cualquier vista mensual (dashboard, resumen de `/agenda`) la vea donde realmente va a pasar. Afecta a ambas pantallas porque comparten el mismo endpoint.

⚠️ **Limitación conocida y aceptada**: si más adelante se corre "Completar mes" sobre el mes DESTINO (octubre, en este ejemplo) y ese mismo slot (mant_id + semana) todavía no tiene una fila nativa de octubre, el auto-fill va a crear una fila nueva nativa para octubre en esa semana — quedando dos filas "compitiendo" conceptualmente por el mismo slot (la movida desde septiembre + la nativa de octubre). Es un caso borde poco frecuente (requiere reprogramar manualmente Y DESPUÉS auto-completar el mismo mes); no se resolvió para no arriesgar colisiones de datos al mover filas físicamente entre meses.

#### Fix — grilla semanal de `/agenda` pasa de 5 a 7 días
Solo mostraba lunes a viernes. El operador normalmente también tiene trabajo sábados y domingos, y esos días eran completamente invisibles — ni se veían tareas cargadas ahí ni había forma de cargar algo nuevo para un fin de semana. Ahora `weekDays()` devuelve 7 días (lun-dom), sábado/domingo se marcan con fondo distinto (`.is-finde`), y el selector de día del generador de WhatsApp ya no se salta el fin de semana.

⚠️ **Aclaración de negocio — las horas NO tienen que cerrar matemáticamente**: ver nota más arriba en la sección de mantenimientos precargados. La cantidad de visitas (`semanas_mes`) es la fuente de verdad para toda la programación; las horas son solo una etiqueta informativa.

#### Bug grave #3 — "Quitar" no funcionaba en visitas prestadas de otro mes (2026-10-03)
Efecto colateral del fix del bug #2 (visitas visibles en el mes destino aunque su bookkeeping sea de otro mes de origen): al abrir el modal de una de esas visitas "prestadas" y tocar cualquier acción (Guardar fecha, Marcar realizado/vencido, Quitar), `accion()` guardaba usando el año/mes de la vista ACTUAL (el mes que se está mirando), no el año/mes real de la fila. Resultado: creaba una fila nueva en el mes equivocado con los datos del cambio, mientras la fila original (con su fecha_real vieja) quedaba intacta — el botón "Quitar" visualmente no hacía nada.

**Fix:** `abrirModal()` ahora guarda el año/mes real de la visita encontrada en una variable `modalOrigen`, y `accion()` la usa al llamar `saveVisita()` en vez de asumir el mes principal de la vista. Confirmado en vivo: se pudo quitar correctamente una visita de TBAR CCTV (origen septiembre) que estaba reprogramada para el 5/10.

#### Mensaje de WhatsApp con marco visual (2026-10-03)
Pedido estético: que el mensaje generado se destaque como algo distinto dentro del chat del grupo, no como un mensaje más. Primer intento: marco de líneas (`▬`) con emoji 📅 de fecha — descartado porque WhatsApp renderiza 📅 con un número superpuesto que se confundía con el día real. Versión final: marco de estrellas (`✦ ✦ ✦`), sin emoji de calendario, fecha en formato "MARTES 6 DE OCTUBRE", mucho más espaciado entre secciones ("que respire"), cada tarea en 2 líneas (nombre + turno aparte). WhatsApp no soporta recuadros reales (solo *negrita*, _cursiva_, ~tachado~, texto monoespaciado), esto es lo más parecido logrado con texto plano + unicode.

#### Generador de imagen "tipo cartel" para WhatsApp (2026-10-03)
El usuario propuso ir más allá del texto: generar una **imagen** con el mismo contenido pero con diseño propio, sin depender de cómo WhatsApp interpreta negrita/emojis. Implementado con `<canvas>` (oculto, `#ws-canvas`):

- Estilo "cartel": fondo claro, doble marco (navy + azul), logo de Gateway arriba, elegido por el usuario sobre la alternativa de mantener el tema navy oscuro de la app.
- Mismo contenido que el mensaje de texto (`wsBuildModel()` es compartido entre ambos generadores).
- **Grilla simétrica de 2 columnas para las tareas**: cada tarea es una tarjeta con borde propio; se acomodan de a 2 por fila bajo el chip (centrado) de cada equipo. Si hay un número impar de tareas, la última fila queda con una sola tarjeta sin forzar un espacio vacío dibujado al lado. Si hay más de un equipo en el día, el segundo bloque (chip + grilla de tareas) se agrega debajo del primero con la misma estructura — mantiene la simetría pedida por el usuario tras los primeros retoques visuales.
- Medición en 2 pasadas: `equiposLayout` (array con el layout de filas/tarjetas por equipo, incluyendo el wrap de texto y el alto de cada tarjeta) se calcula una sola vez y lo usan tanto la pasada de medir el alto total del canvas como la pasada de dibujo — evita que ambas pasadas se desincronicen si se edita una sin la otra.
- Exportación: `canvas.toBlob()` → intenta copiar directo al portapapeles con `navigator.clipboard.write([new ClipboardItem(...)])` (funciona en Chrome/Edge de escritorio con gesto de usuario); si falla, descarga el PNG como respaldo.
- Botón "🖼 Copiar como imagen" al lado de "📋 Copiar mensaje" — ambas opciones conviven, no se sacó la de texto.

**Ajuste de jerarquía del encabezado (2026-10-04)**: feedback del usuario sobre una captura de la imagen generada — quería que el día resaltara más que el título "AGENDA". Se invirtió el orden y el estilo entre ambas líneas (mismos dos estilos de letra que ya existían, solo intercambiados): la fecha pasó arriba usando el estilo grande/navy (800 24px) que antes tenía el título, y "AGENDA DEL DÍA" bajó usando el estilo chico/azul (700 16px) que antes tenía la fecha. También se cambió el emoji: antes era `🔧 AGENDA DEL DÍA` (llave sola al frente), ahora es `📅🔧 AGENDA DEL DÍA` (calendario primero, llave justo detrás) a pedido del usuario. Confirmado en vivo generando una imagen de prueba para el 5/10.

#### Fix: unificación de "texto libre" entre `/agenda` y el calendario del dashboard (2026-10-04)
Bug reportado por el usuario: una tarea de texto libre cargada desde el generador de WhatsApp (confirmada) no se reflejaba en el calendario "Agenda Operativa" del dashboard.

**Causa raíz:** la hoja `agenda_celdas` es compartida por ambas pantallas, pero usaban vocabularios de `turno` distintos para la misma idea de "nota del día":
- `/agenda` (vista semanal) guardaba todo bajo un único campo por día con `turno="libre"`.
- El dashboard (calendario M/T) sólo lee/escribe `turno="manana"` / `turno="tarde"`.

Como las claves nunca coincidían, el contenido de una pantalla era invisible en la otra aunque compartieran hoja.

**Fix (decisión del usuario, consultada antes de implementar):** se eliminó el campo único "libre" de `/agenda` y se reemplazó por dos campos por día (☀️ Mañana / 🌙 Tarde) que usan exactamente las mismas claves `manana`/`tarde` que ya usaba el dashboard. Cambios:
- `renderWeek()`: dos `<textarea>` por día en vez de uno, cada uno con su propio `onblur="guardarLibre(...,'manana'|'tarde',...)"`.
- `guardarLibre(dia, mes, año, turno, texto)` ahora recibe el turno como parámetro en vez de hardcodear `"libre"`.
- Nuevas funciones helper `celdaLibre(dia, mes, año, turno)` y `notasDelDia(dia, mes, año)` (combina mañana+tarde para el bloque "ADEMÁS" del mensaje/imagen de WhatsApp).
- `wsConfirmarTareas()`: las tareas de texto libre ahora se agrupan por su propio turno (mañana/tarde) y cada grupo se guarda en la celda correspondiente, no todo en "libre".
- **Migración de dato real**: había una nota ya confirmada en producción bajo `turno="libre"` (día 5/10, "Realizar las modificaciones en los Racks pedidas por Nestor") que habría quedado huérfana. Se migró manualmente a `turno="manana"` vía POST directo a `/api/agenda/celda` antes de deployar, y se vació la celda "libre" vieja. Confirmado en vivo: el texto aparece igual en `/agenda` (campo Mañana) y en el calendario del dashboard (celda M del día 5).

#### Corrección de modelo conceptual: "tarea de texto libre" ≠ "nota del día" (2026-10-04)
El fix anterior (unificar mañana/tarde) resolvió la sincronización pero mezcló dos conceptos que el usuario distingue claramente:
- **Texto libre** (lo que se agrega dentro de un equipo en el generador de WhatsApp, `+ Texto libre`) es una **tarea real para los técnicos**, al mismo nivel que un mantenimiento del catálogo.
- **Nota extra** (el campo de comentario general del generador, ej. "pasar por el depósito a buscar insumos") es un comentario, no una tarea.

Ninguna de las dos es lo mismo que el campo Mañana/Tarde de notas generales (que sigue existiendo, para uso manual directo del operador, sin relación con el generador de WhatsApp). Se separaron en celdas propias dentro de la misma hoja `agenda_celdas` (reutilizando el mecanismo genérico, sin tocar el schema):
- `turno="tareas_libres"`: JSON por día, `[{texto, equipo, turno}]`. En `/agenda` se renderiza como tarjeta propia (`.lcard`, estilo distinto al de un mantenimiento — borde punteado violeta — pero mismo peso visual, con ícono 📝). En el dashboard se muestra como un popup de solo texto (`title` nativo del navegador) al pasar el cursor sobre la celda M/T correspondiente — decisión explícita del usuario, dado el poco espacio disponible ahí.
- `turno="nota_extra"`: texto plano por día. En `/agenda` se muestra como un ícono 📌 en el encabezado del día, con el texto completo en el popup al pasar el cursor. Se persiste al perder foco (`wsGuardarNotaActual()`) y se precarga al volver a seleccionar ese día en el generador (`wsPoblarDesdeDia()`).

Helpers nuevos en `agenda.html`: `celdaTareasLibres()`, `guardarTareasLibres()`, `celdaNotaExtra()`, `guardarNotaExtra()`, `guardarCeldaRaw()` (función genérica de la que ahora derivan `guardarLibre()` y las dos anteriores).

#### Fix: el panel de carga de WhatsApp no se limpiaba al confirmar (2026-10-04)
Bug reportado por el usuario: después de "Confirmar tareas", el equipo recién cargado seguía apareciendo en el panel tal cual, sin distinguirse de uno nuevo — esto impedía en la práctica cargar un segundo equipo para el mismo día (ej. turno tarde/noche), porque no quedaba claro si se estaba editando el equipo ya confirmado o agregando uno nuevo, y los clicks en los chips de técnicos terminaban mezclando gente en el equipo equivocado.

**Fix:** al terminar `wsConfirmarTareas()`, en vez de dejar el array `wsEquipos` tal cual (con los ítems marcados `confirmado:true` en memoria), se vuelve a construir desde cero llamando a `wsPoblarDesdeDia(iso)` — la misma función que se usa al seleccionar el día por primera vez. Para que esto no "pierda" las tareas de texto libre ya confirmadas (que antes `wsPoblarDesdeDia` no leía, solo mantenimientos), se agregó `wsTecStr()`: normaliza cualquier lista de técnicos al orden canónico de `TECNICOS_ALL`, para que una tarea de mantenimiento y una de texto libre con el mismo equipo (guardadas con formatos de string distintos: `"Camilo,Pablo"` vs `"CAMILO + PABLO"`) caigan agrupadas en el mismo bloque. Resultado: tras confirmar, el panel muestra los equipos ya guardados (sin la marca "sin confirmar") y queda libre para sumar un equipo nuevo con "+ Agregar equipo" sin arrastrar estado del anterior. Confirmado en vivo con 2 equipos reales en el mismo día (Camilo+Pablo turno mañana, Matías+Nacho turno tarde).

#### Archivos del módulo
```
db.py                       ← funciones mantenimientos/visitas (líneas ~440-660 aprox.)
main.py                     ← rutas /agenda y /api/agenda/*
templates/agenda.html       ← página completa (vista semanal, modal, generador WS)
```

#### Pendiente / a definir
- Drag & drop de cards en modo Manual (el usuario no está seguro de quererlo — por ahora Manual es "click para asignar fecha", más simple)
- Decidir si el módulo se integra visualmente dentro del dashboard principal o queda como página separada (por ahora: separada, con nav propio)
- Falta cargar los 15 mantenimientos reales completos si hay más de los 6 iniciales (confirmado por el usuario: "son todos los que tenemos" — revisar si eso sigue siendo así)

---

### Presupuestos alta gama
**Estado: planificado.**

Versión extendida del módulo Presupuestos para trabajos grandes (instalaciones de cámaras en empresa, central de incendio nueva, cobertura de nuevo sector). Layout más detallado y profesional.

---

### Layout Cámaras (integración)
**Estado: planificado** — módulo ya desarrollado externamente, a incorporar.

---
*Última actualización: 2026-10-04 (tarea de texto libre separada de nota extra; panel de WhatsApp se limpia al confirmar)*
