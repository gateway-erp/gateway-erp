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

---
*Última actualización: 2026-09-27*
