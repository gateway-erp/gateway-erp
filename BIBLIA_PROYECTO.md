# Biblia del Proyecto — Sistema de Gestión Integral Gateway

Documento vivo donde se registra, módulo por módulo, todo lo que se va desarrollando. Al finalizar el proyecto, esta biblia sirve de base para armar el diagrama de flujo completo y la presentación de funcionalidades del software.

---

## Idea general
Sistema web propio para Gateway que reemplaza y centraliza herramientas dispersas (Word, Excel, correos). ERP/CRM simplificado orientado a empresas de servicios de seguridad electrónica. Accesible desde cualquier PC, tablet o celular sin instalación.

---

## Módulos planificados
| Módulo | Descripción | Estado |
|---|---|---|
| Presupuestos | Crear, enviar y hacer seguimiento de presupuestos | En desarrollo |
| Órdenes de Compra | Vinculadas a presupuestos, handoff a facturación con alertas | Planificado |
| Facturación | Emisión, historial, alertas de límite, proyección fiscal | Planificado |
| Agenda / Calendario | Mantenimientos, trabajos, asignación a técnicos, envío diario | Planificado |
| Layout Cámaras | Ya desarrollado — integrar como módulo del sistema | Hecho (externo) |

---

## Stack tecnológico
- **Backend**: Python (FastAPI)
- **Base de datos**: Google Sheets vía API con Service Account (suite Google ya en uso, acceso remoto, cero costo adicional)
- **Frontend**: Web app responsive — misma interfaz en PC, tablet y celular. Sin instalación, sin actualizaciones manuales.
- **Autenticación**: Google Login
- **Hosting**: A definir — confirmar si hosting actual de gateway.com.ar es VPS o compartido. Si es compartido, usar servicio aparte (Render/Railway/Fly.io capa gratuita)
- **Diseño modular**: cada módulo con su propia lógica y permisos para poder delegar accesos por rol (programador, operador de facturación, técnico)

---

## Estimación
4 a 6 meses, módulo por módulo, arrancando por **Presupuestos**.

---

## Registro por módulo

### Presupuestos
**Estado: funcional en local — pendiente conexión Google Sheets y hosting.**

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

#### Próximo paso del módulo
Conectar Google Sheets como base de datos vía Service Account (reemplaza los JSON de `data/`). Pasos para el usuario:
1. Ir a console.cloud.google.com → crear proyecto "Gateway ERP"
2. Activar Google Sheets API y Google Drive API
3. Crear Service Account (IAM & Admin → Service Accounts)
4. Generar clave JSON y compartirla
5. Compartir los Sheets con el email de la service account

---

### Órdenes de Compra (OC)
**Estado: planificado.**

Cadena completa:
`Email de pedido → Presupuesto → Aprobación → OC → Trabajo realizado → Factura`

- OC vinculada al presupuesto aprobado (número propio de OC del cliente)
- Panel del programador: OC activas, pendientes de facturar, facturadas
- Handoff sin emails: el programador marca OC lista → aparece en bandeja del operador de facturación
- Alertas bidireccionales entre programador y operador
- Bandeja de OC pendientes + historial de facturadas

---

### Facturación
**Estado: planificado.**

- Facturas vinculadas a OC
- Historial por cliente y período
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
