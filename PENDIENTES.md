# Pendientes — Sistema de Gestión Integral Gateway

---

## Técnicos (a resolver antes de continuar desarrollo)

- [ ] **Google Sheets como DB — EN CURSO, retomar desde la compu donde está logueada la cuenta de Google que se va a usar.** Contexto (2026-07-29): el usuario quiere migrar de los JSON locales a una cuenta de Gmail como base de datos real, porque ahí ya vive información importante de la empresa ("el alma de los archivos"). Quedaron 2 preguntas sin responder antes de empezar a implementar:
  1. ¿Qué cuenta de Gmail/Google se usa? (opciones charladas: `aplicacionesgateway@gmail.com` — la misma usada para los commits de git —, otra cuenta puntual, o crear una cuenta nueva dedicada)
  2. Los presupuestos ya existentes que el usuario menciona — ¿están hoy en una planilla de Google Sheets ya armada (se conecta directo), en archivos sueltos Word/PDF/Excel (hay que pensar cómo migrarlos), o es otra cosa?
  Una vez respondidas, seguir con los pasos ya anotados: crear proyecto en Google Cloud, activar Sheets API + Drive API, crear Service Account, generar clave JSON, compartir el/los Sheets con el email de la service account. Ver también BIBLIA_PROYECTO.md → sección "Próximo paso del módulo Presupuestos".
- [ ] **API del dólar**: el usuario va a indicar de qué fuente traer la cotización USD/ARS.
- [x] ~~**Hosting**: confirmar si gateway.com.ar es VPS con acceso root o hosting compartido.~~ Resuelto 2026-07-28: es hosting compartido (Ferozo/DonWeb, Linux, Plesk), sin root. Ver BIBLIA_PROYECTO.md → Stack tecnológico.
- [x] ~~**Servicio externo para el backend**: elegir servicio y definir cómo se conecta gateway.com.ar.~~ Resuelto 2026-07-29: se eligió **Render** (plan free). Deploy funcionando en `https://gateway-erp.onrender.com`, repo en GitHub (`gateway-erp/gateway-erp`) conectado con auto-deploy en cada push a `master`. Dominio propio en curso: `gestion.gateway.com.ar` (CNAME → `gateway-erp.onrender.com` ya cargado en la zona DNS de Ferozo, propagando). Limitación conocida: sin disco persistente en el plan free — los datos no sobreviven reinicios, de ahí la urgencia de migrar a Sheets.

## Decisiones de negocio (pendientes de definición)

- [ ] ¿El número de OC lo genera el sistema o lo ingresa el cliente en la OC que manda?
- [ ] ¿Cuál es el límite mensual de facturación actual? (para configurar la alerta)
- [ ] ¿Facturación electrónica AFIP? (módulo más complejo, a decidir si entra en el alcance)
- [ ] ¿Los técnicos van a tener acceso al sistema para ver sus tareas asignadas, o solo lo ve el programador?
- [ ] ¿Los 15 mantenimientos mensuales tienen cliente/fecha/frecuencia definidos para precargarlos?

---
*Última actualización: 2026-07-29*
