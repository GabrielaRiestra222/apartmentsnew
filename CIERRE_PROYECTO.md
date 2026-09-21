# Cierre del proyecto CMS + CRM + Catalogo premium

## Objetivo

Cerrar una plataforma de apartamentos con tres superficies claras:

- Catalogo publico premium para mostrar apartamentos publicados.
- CRM operativo para clientes, reservas, pagos, calendario, limpieza y mantenimiento.
- CMS/admin para editar apartamentos, fotos, amenities, FAQ e integraciones.

## Estado actual del backend

El backend Django ya tiene una base amplia:

- Propiedades publicas y privadas: `properties`.
- Clientes y reservas: `clients`, `bookings`.
- Pagos y contabilidad: `payments`, `accounting`.
- Calendario, limpieza y mantenimiento: `property_calendar`, `cleaning`, `maintenance`.
- FAQ, chatbot e integraciones: `faq`, `chatbot`, `integrations`.
- Autenticacion JWT y admin Django.

## Cierre minimo para entregar

1. Catalogo publico
   - Listado publico con solo apartamentos `is_published=True`.
   - Detalle publico por `slug`.
   - Galeria con imagen principal, amenities, reglas, distribucion, camas y datos turisticos.
   - CTA claro: consulta, WhatsApp, formulario o reserva segun decision comercial.

2. CMS de apartamentos
   - Crear/editar apartamentos desde admin o panel.
   - Subida real de imagenes a `MEDIA_ROOT` o storage externo.
   - Orden de imagenes y seleccion de imagen principal.
   - Estado editorial: borrador/publicado/activo.

3. CRM operativo
   - Pipeline basico de reservas: pendiente, confirmada, cancelada.
   - Ficha de cliente con documento, telefono, nacionalidad y notas.
   - Pagos asociados y saldo pendiente.
   - Calendario por apartamento para evitar solapes.

4. Produccion
   - `DEBUG=False`.
   - PostgreSQL configurado por variables de entorno.
   - `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` y `CORS_ALLOWED_ORIGINS` con dominios finales.
   - Media files servidos por storage persistente si no se despliega en servidor con disco persistente.
   - Backups de base de datos y media.

## Prioridades recomendadas

### Fase 1: estabilizar backend

- Completar tests criticos de propiedades, reservas y permisos.
- Revisar multi-organizacion para que usuarios no vean datos de otra organizacion.
- Cambiar storage de media a S3, Cloudflare R2 o disco persistente segun hosting final.
- Revisar endpoints publicos para no exponer datos internos.

### Fase 2: cerrar experiencia premium

- Definir frontend definitivo: Next.js/React separado o templates Django.
- Crear home/listado/detalle con assets reales de los apartamentos.
- Preparar SEO: slugs, titulos, descriptions, Open Graph, sitemap y robots.
- Optimizar imagenes: WebP/AVIF, thumbnails y lazy loading.

### Fase 3: CRM y operacion diaria

- Dashboard: ocupacion, ingresos, reservas proximas, limpiezas y mantenimiento pendiente.
- Vistas filtrables por fecha, apartamento, estado y canal.
- Export CSV para reservas, clientes y contabilidad.
- Auditoria basica de cambios importantes.

## Checklist de salida

- `python manage.py check` sin errores.
- `python manage.py test` con tests criticos pasando.
- Migraciones aplicadas en entorno limpio.
- Admin creado y acceso verificado.
- Apartamentos reales cargados con fotos optimizadas.
- Dominio final conectado.
- HTTPS activo.
- Variables de entorno documentadas.
- Backups probados.

## Decisiones pendientes

- Hosting final del backend: VPS, Render, Railway, Fly, Heroku, Vercel solo demo o similar.
- Hosting frontend: Vercel, Cloudflare Pages, Netlify o servidor propio.
- Storage de imagenes: local persistente, S3 o Cloudflare R2.
- Canal comercial principal: formulario, WhatsApp, motor de reservas o integracion externa.
- Idiomas del catalogo: ES, EN, PT u otros.

## Estado de seguridad y limitaciones conocidas

Cerrado en el backend (con tests en `properties/tests.py` y `common/tests.py`):

- Clientes, agencias, equipo e inbox pertenecen a una organización; el dashboard también se filtra por ella.
- Cancelar una reserva anula sus movimientos contables (`is_void`) en lugar de borrarlos, y reactivarla los recupera.

- Catálogo interno solo con sesión; el público solo muestra apartamentos publicados y sin datos internos.
- Reserva pública: el servidor calcula el precio, valida capacidad, estancia mínima y solapes, y limita las peticiones.
- Aislamiento por organización en propiedades, reservas, pagos, contabilidad, calendario, limpieza, mantenimiento e integraciones. Los propietarios (OWNER) no acceden a integraciones ni inbox.
- Webhook de n8n cerrado sin `N8N_INBOUND_SECRET`; chatbot público, contacto y reserva pública con límite de peticiones.
- Feed iCal sin nombres de huéspedes. Refresh tokens JWT invalidados tras rotarse.
- HTTPS forzado, HSTS y cabeceras seguras cuando `DEBUG=False`.

Limitaciones que se declaran a propósito:

- Los webhooks de automatización y sus eventos son de configuración global, no de una organización concreta; solo el staff accede a ellos.
- Los datos que entran sin usuario (formulario de contacto y chatbot de la web) se asignan a la organización de la propiedad consultada o, si no hay ninguna, a la primera organización.
- El inbox registra las respuestas pero no envía el email.
- Sin `REDIS_URL`, el límite de peticiones usa la tabla `django_cache` de la base de datos: es compartido entre instancias pero más lento que Redis.

Variables de entorno de producción: `SECRET_KEY` (larga y aleatoria), `DB_*`, `N8N_INBOUND_SECRET`, `CRM_BASE_URL`, `BOOTSTRAP_TOKEN`, `ANTHROPIC_API_KEY`.
Tras desplegar hay que ejecutar migraciones con `/api/system/bootstrap/`: crean las tablas de `token_blacklist` y de la caché, y añaden `organization` a clientes, agencias, equipo e inbox (los datos existentes se asignan a su organización) e `is_void` a contabilidad.
