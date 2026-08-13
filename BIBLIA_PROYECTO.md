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
| Agenda / Calendario | Mantenimientos, trabajos, asignación a técnicos, envío diario | Planificado |
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
**Estado: planificado.**

- Vista día / semana / mes
- 15 mantenimientos mensuales obligatorios precargados, se repiten automáticamente
- Recordatorio diario de mantenimientos pendientes al abrir
- Trabajos rápidos: el programador anota un pedido al vuelo → queda como tarea pendiente
- Envío automático del resumen del día siguiente; recordatorio si no se hizo; botón de envío
- Asignación de trabajos a técnicos
- Vista de pendientes sin asignar vs. programados

---

### Presupuestos alta gama
**Estado: planificado.**

Versión extendida del módulo Presupuestos para trabajos grandes (instalaciones de cámaras en empresa, central de incendio nueva, cobertura de nuevo sector). Layout más detallado y profesional.

---

### Layout Cámaras (integración)
**Estado: planificado** — módulo ya desarrollado externamente, a incorporar.

---
*Última actualización: 2026-07-10*
