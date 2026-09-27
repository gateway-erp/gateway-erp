# Pendientes — Sistema de Gestión Integral Gateway

---

## Módulo Presupuestos / Pipeline — pendientes técnicos

- [ ] **Auto-extracción de PDFs con pymupdf**: al subir una OC, factura u OP, que el sistema lea el PDF y pre-complete los campos del popup automáticamente. Formatos ya analizados: Toyota OC (SAP), Toyota OP, Swetech OP, Master Bus (3 PDFs), Facturas Gateway AFIP.
- [ ] **Vista LISTA** como alternativa al kanban — toggle en el dashboard para ver todos los presupuestos en tabla con filtros por estado, cliente, fecha.
- [ ] **Limpieza de filas vacías** en la hoja `clientes` de Sheets (códigos 2-10 generados durante debugging). Hacer manualmente desde Google Sheets.
- [ ] **Endpoint /debug-error**: sacar de producción una vez estabilizado (o dejarlo solo para IPs internas).

## Módulo Presupuestos — mejoras de UX pendientes

- [ ] Al aprobar un presupuesto sin adjuntar PDF de OC, el sistema avanza igualmente. Implementado "Editar OC" para corrección posterior — OK. Evaluar si agregar validación de campos mínimos (al menos N° OC).
- [ ] Regenerar PDF de presupuestos viejos (pre-Drive) y subirlos a Drive retroactivamente — los 12 de prueba de agosto 2026 están perdidos, no urgente.

## Pipeline — funcionalidades pendientes

- [ ] **Indicador de días sin respuesta** en cards Enviados — mostrar cuántos días pasaron desde la fecha del presupuesto para que el operador sepa qué hacer seguimiento.
- [ ] **Historial de acciones** por presupuesto — registro de cuándo cambió de estado y quién lo hizo (preparación para multi-usuario).
- [ ] **Notificación** cuando un presupuesto lleva N días sin respuesta (email o banner en dashboard).

## Decisiones de negocio (pendientes de definición)

- [ ] ¿El número de OC lo genera el sistema o lo ingresa el operador copiando el que manda el cliente? → **Confirmado**: lo ingresa el operador desde la OC del cliente.
- [ ] ¿Cuál es el límite mensual de facturación actual? (para configurar la alerta futura)
- [ ] ¿Facturación electrónica AFIP? (módulo más complejo, a decidir si entra en el alcance)
- [ ] ¿Los técnicos van a tener acceso al sistema para ver sus tareas asignadas, o solo lo ve el programador?
- [ ] ¿Los 15 mantenimientos mensuales tienen cliente/fecha/frecuencia definidos para precargarlos?

## Módulo Agenda de Mantenimientos — pendientes técnicos

- [ ] **Drag & drop en modo Manual**: por ahora Manual es "click en pendiente → elegir fecha/turno en modal". El usuario no confirmó si quiere además poder arrastrar cards directo sobre la grilla.
- [ ] Confirmar si los 6 mantenimientos cargados son la lista completa o falta agregar más (el usuario dijo que sí son todos, pero originalmente se habló de "15 mantenimientos mensuales" — revisar si esa cifra vieja sigue vigente).
- [ ] Evaluar si conviene integrar la vista de mantenimientos dentro del dashboard principal (agenda actual del dashboard es un calendario de texto libre aparte) en vez de página separada `/agenda`.
- [x] **Dos UIs de mantenimientos en paralelo — resuelto (paso 1/2)**: se decidió que `/agenda` es el único lugar para editar. Paso 1 hecho: el widget del dashboard (`#agenda-mant`) perdió toda capacidad de edición (se sacó el modal, `aClickVisita`/`mmSetTurno`/`mmCerrar`/`mmAccion` y el onclick de las cards) — ahora es solo informativo (nombre, cliente, estado por color).
- [ ] **Paso 2 pendiente**: el widget del dashboard debería linkear a `/agenda` (el título "Agenda Operativa" o un botón) en vez de no hacer nada al click.
- [ ] No usar tildes/ñ en nombres de parámetros de ruta de FastAPI (`{año}` nunca matcheaba en runtime aunque aparecía en el schema — usar `{anio}`, `{numero}`, etc.)
- [ ] No usar comas dentro de strings guardados en Sheets vía `USER_ENTERED` si el valor podría parecer numérico (Sheets locale es-AR las interpreta como separador de miles) — usar `;` o forzar texto con comilla inicial.

## Módulos nuevos — por arrancar

- [ ] **Autenticación Google Login**: control de acceso con roles (operador, facturación, etc.)

---

## Resueltos ✓

- [x] Hosting: Render free plan — `gestion.gateway.com.ar` live
- [x] Google Sheets como DB — Service Account configurado, todas las hojas activas
- [x] Google Drive como almacenamiento persistente — PDFs subidos automáticamente por cliente
- [x] API del dólar: dolarapi.com (oficial=billete, mayorista=divisa), cache 30 min
- [x] Pipeline completo Enviado→Aprobado→Facturado→Cobrado con popups y Drive upload
- [x] Kanban dashboard con dot verde/rojo para estado de cobro
- [x] Hojas Sheets: `historial` (+ columnas OC), `facturas` (nueva)
- [x] Editar OC desde cards Aprobados sin cambiar de estado
- [x] Módulo Agenda de Mantenimientos: vista semanal, modo Automático/Manual, auto-validación día a día, arrastre de pendientes entre meses, generador de mensaje WhatsApp — LIVE en `/agenda` (2026-09-27)
- [x] Navegación "volver al inicio" unificada en las 7 pantallas del sistema (logo + etiqueta "‹ Inicio")
- [x] Dashboard: scroll independiente por columna en vista-2 (agenda | presupuestos) — antes scrolleaba todo junto
- [x] Dashboard: modal propio para mantenimientos (reemplaza `prompt()` nativo) — fecha, turno, Realizado/Guardar/Desmarcar
- [x] `/agenda`: dropdown de WhatsApp arranca desde mañana; input de fecha del modal no permite fechas pasadas (`min=hoy`)
- [x] Scroll de vista-2 (definitivo): la altura fija no descontaba el alto de la barra de post-its — ahora se calcula por JS y se recalcula en cada cambio
- [x] Layout de mantenimientos del dashboard: de columna angosta lateral a fila horizontal debajo del calendario, a todo el ancho
- [x] Etiqueta "Dashboard" unificada bajo el logo en las 7 pantallas (antes "‹ Inicio")
- [x] Limpiado dato corrupto: TBAR CCTV sem 1 tenía fecha "2016" guardada por error, quedaba siempre en verde
- [x] Nav tab que iba a "/" decía "Presupuestos", renombrado a "Dashboard" en las 6 pantallas
- [x] Etiqueta chica bajo el logo sacada del dashboard (redundante con el tab activo); se mantiene en las otras 6
- [x] Logo de Clientes y Nuevo Presupuesto usaba `logo.png` (fondo negro, desentonaba) — unificado a `logo-gateway.jpeg`

---
*Última actualización: 2026-09-27*
