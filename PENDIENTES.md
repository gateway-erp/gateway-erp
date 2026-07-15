# Pendientes — Sistema de Gestión Integral Gateway

---

## Técnicos (a resolver antes de continuar desarrollo)

- [ ] **Google Sheets como DB**: el usuario tiene que crear el proyecto en Google Cloud, activar las APIs, generar la Service Account y pasar la clave JSON. Ver pasos en BIBLIA_PROYECTO.md → sección "Próximo paso del módulo Presupuestos".
- [ ] **API del dólar**: el usuario va a indicar de qué fuente traer la cotización USD/ARS.
- [ ] **Hosting**: confirmar si gateway.com.ar es VPS con acceso root o hosting compartido (cPanel). Define dónde corre el backend Python.

## Decisiones de negocio (pendientes de definición)

- [ ] ¿El número de OC lo genera el sistema o lo ingresa el cliente en la OC que manda?
- [ ] ¿Cuál es el límite mensual de facturación actual? (para configurar la alerta)
- [ ] ¿Facturación electrónica AFIP? (módulo más complejo, a decidir si entra en el alcance)
- [ ] ¿Los técnicos van a tener acceso al sistema para ver sus tareas asignadas, o solo lo ve el programador?
- [ ] ¿Los 15 mantenimientos mensuales tienen cliente/fecha/frecuencia definidos para precargarlos?

---
*Última actualización: 2026-07-10*
