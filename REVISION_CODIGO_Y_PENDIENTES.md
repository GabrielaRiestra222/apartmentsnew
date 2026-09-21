# Revisión del código y tareas pendientes

Fecha: 21 de septiembre de 2026.

El proyecto tiene una base funcional de gestión, pero todavía mezcla módulos conectados a Django con pantallas de demostración. La limpieza de estilo está aplicada y verificada. Durante la revisión aparecieron cambios concurrentes en el workspace. El estado actualizado de esos cambios se distingue abajo de los hallazgos iniciales; no todos siguen abiertos ni todos están completamente cerrados.

## Alcance y comprobaciones

Revisión transversal del backend Django, CRM/CMS (`../SaaS Property Management Dashboard`), landing (`../ApartmentsLanding`) y frontend de demostración (`frontend/`). Lectura de los flujos de autenticación, propiedades, reservas, pagos, calendario, mantenimiento, contabilidad, integraciones, chatbot y publicación. Se revisaron también configuración, rutas, dependencias y pruebas.

- Sintaxis Python: 182 archivos analizados, incluidas migraciones, sin errores.
- Django: 10 tests correctos tras mi limpieza; 27 correctos en la última ejecución, después de incorporar el estado concurrente del workspace. Los dos añadidos por esta revisión cubren compatibilidad de metadatos y edición de propiedades por administradores sin organización. Comando final: `USE_SQLITE=True DEBUG=True ./venv/bin/python manage.py test --noinput`. Sin `DEBUG=True`, la nueva redirección HTTPS provoca respuestas 301 y falla la suite: falta aislar la configuración de tests.
- Django: comprobación de configuración correcta; sin migraciones nuevas pendientes de generar.
- CRM: 20 tests correctos y compilación de producción correcta.
- Landing y frontend de demostración: compilaciones de producción correctas.
- Cinco comprobaciones adicionales sobre una base de datos de pruebas reprodujeron los problemas descritos como «reproducidos». No modificaron la base de datos local.
- El CRM genera un archivo JavaScript de unos 1,51 MB, 436 KB comprimido. Vite avisa de su tamaño. El frontend de demostración también supera el umbral de aviso.

Estas comprobaciones no equivalen a probar todas las pantallas en navegador. No se realizó una auditoría de proveedores externos, de infraestructura de producción ni de vulnerabilidades de dependencias. La compilación de Vite no sustituye a la comprobación de tipos TypeScript; durante la revisión se añadió TypeScript y un script `typecheck` desde otra edición. Se ejecutó `npm run typecheck` y falló: hay incompatibilidades entre esquemas de formularios y sus tipos, imports obsoletos, tipado de FAQ y declaraciones faltantes. Los builds correctos se obtuvieron antes de los últimos cambios concurrentes del CRM.

## Limpieza aplicada

El criterio ha sido que el código resulte directo y mantenible: nombres que expliquen su función, menos repetición y comentarios que aporten contexto. El estilo por sí solo no permite determinar quién escribió un archivo.

| Zona | Cambio aplicado | Motivo |
| --- | --- | --- |
| `properties/serializers.py` | Sustituidos 22 métodos iguales por `EquipmentValueField`, manteniendo declaraciones explícitas de cada campo. | Leer metadatos antiguos guardados como listas o valores simples desde un único sitio. Se conservan los valores por defecto. |
| `properties/views.py` | Eliminado `perform_update`, que solo repetía `serializer.save()`. Acortado el comentario sobre la organización. | Usar el comportamiento de DRF y quitar explicaciones históricas que ya no ayudan a leer el código. |
| `bookings/models.py`, `chatbot/views.py`, `users/views.py` | Quitados separadores decorativos, un emoji, comentarios que narraban cada paso y una nota de un cambio anterior. | Dejar que nombres y estructura expliquen el flujo. |
| `integrations/views.py` | Eliminados dos imports sin uso. | Reducir ruido. |
| CRM: `src/lib/apiError.ts` y hooks de propiedades/reservas | Centralizada la lectura de errores de API. | Evitar dos implementaciones y mostrar el mensaje de validación en propiedades en lugar del JSON completo. |
| Landing: `src/lib/calendar.ts` | Extraídas siete funciones de fechas y formato de `EditorialSections.tsx`. | Separar cálculos de calendario y JSX sin alterar su lógica. |
| `properties/tests.py` | Dos pruebas de regresión. | Proteger el contrato de la API y la conservación de la organización al editar. |

Se conservaron los cambios previos del usuario. No se reescribieron componentes estándar de UI ni se renombraron modelos, rutas o campos para darles una apariencia distinta. Mi limpieza no añadió cambios de esquema ni migraciones de datos. Las nuevas migraciones de organización y contabilidad visibles al cierre pertenecen a los cambios concurrentes y requieren su propio control de despliegue.

## Estado actualizado de cambios concurrentes

Estos cambios aparecieron durante la revisión y no se atribuyen a la limpieza anterior. La suite actual de Django pasa con configuración de desarrollo, pero todavía falta validar el recorrido completo en navegador y la configuración de producción.

| Hallazgo inicial | Estado observado al cierre | Qué falta |
| --- | --- | --- |
| Catálogo interno anónimo | Se añadió `IsAuthenticated`; existe test de regresión. | Validar todos los consumidores y el despliegue. |
| Precio y capacidad manipulables | El serializer público calcula tarifa base + limpieza y valida publicación, capacidad, estancia y solapes. | Bloqueos de calendario, tarifas/ descuentos, atomicidad y concurrencia. |
| Reserva en apartamento ajeno | Se añadió validación de apartamento y filtros de organización en varios módulos. | Revisar todas las relaciones de escritura y permisos OWNER; una comprobación de organización no sustituye a comprobar propiedad. |
| Metadatos públicos | Se retiraron varios campos superiores y el nombre del huésped del iCal. | `equipment` sigue publicado sin filtrar; proteger feed con token. |
| Webhook n8n abierto | Se exige secreto con comparación segura; se añadieron límites a contacto, reservas y chat. | Destinos salientes, repetición, configuración de caché compartida y límites bajo carga. |
| Cancelación | Se liberan bloques y se anulan movimientos mediante `is_void`. | Cambios de fecha/importe, limpieza ya iniciada y consistencia de informes. |
| Contacto e inbox | Se añadió `/api/contact/`, envío desde landing e inbox conectado a registros con selección y guardado de respuestas. | Confirmar flujo extremo a extremo, paginación y entrega externa: guardar una respuesta no equivale a enviarla al huésped. |
| TypeScript y configuración | Se añadieron `typecheck`, variables de URL, caché y nuevas migraciones de organización. | `typecheck` falla; validar migraciones y configuración en un entorno limpio. |

Los cinco hallazgos reproducidos que siguen describen el estado inicial, anterior a estas correcciones. La columna «Qué falta» es la referencia para el cierre actual.

## Hallazgos iniciales de prioridad 0 y cierre requerido

### 1. Catálogo interno accesible sin iniciar sesión — reproducido

**Evidencia:** `properties/views.py`, `PropertyViewSet`; `common/permissions.py`, `IsAuthenticatedOrReadOnlyForProperties`.

`GET /api/properties/` permite acceso anónimo y devuelve también propiedades sin publicar usando el serializer del CRM. La existencia de `/api/public/properties/` no protege esta segunda vía.

**Cierre:** exigir autenticación en las rutas internas y probar que listado y detalle anónimos quedan denegados. La landing debe consumir exclusivamente la API pública.

### 2. Reservas públicas sin validación suficiente — reproducido

**Evidencia:** `integrations/serializers.py`, `PublicBookingSerializer`; `integrations/views.py`, `public_booking`.

El servidor acepta `total` y `deposit_percent` enviados por el navegador. Solo valida el orden de las fechas; crea la reserva directamente sin ejecutar `Booking.clean()`. En pruebas se pudieron crear dos reservas solapadas sobre un borrador, para 99 huéspedes y con precio de 0,01.

**Cierre:** calcular el precio en servidor; exigir propiedad activa y publicada; validar capacidad, estancia mínima, fechas, descuentos y porcentaje de señal; comprobar reservas y bloqueos; guardar reserva y pago en una transacción. Añadir protección contra reservas simultáneas sobre el mismo apartamento. No basta con validar en React.

### 3. Permisos de propietario y organización incompletos — reproducido parcialmente

**Evidencia:** `common/permissions.py`, `OwnerScopedQuerysetMixin`; serializers con relaciones globales; vistas de calendario, imágenes, clientes e integraciones; `chatbot/views.py`, `AdminChatbotMessageView`.

El mixin limita consultas en algunos módulos, pero no valida las relaciones recibidas al crear o cambiar registros. Se reprodujo que un propietario puede crear una reserva sobre un apartamento que no le pertenece. Otras vistas solo exigen autenticación, sin limitar registros por propietario. El asistente interno filtra por organización, pero no por la cartera del propietario. Tampoco existe aislamiento general entre organizaciones para managers.

**Cierre:** definir una matriz ADMIN/MANAGER/OWNER; filtrar lectura y relaciones de escritura con la misma política; cubrir listados, detalles, POST, PATCH, DELETE y acciones. Decidir explícitamente si habrá varias organizaciones independientes o un único operador.

### 4. Datos internos en respuestas públicas — reproducido

**Evidencia:** `properties/serializers.py`, `PublicPropertySerializer`; `integrations/views.py`, `property_ical_export`.

La respuesta pública incluye propietario, referencias internas y el JSON completo de `equipment`. Quitar únicamente los campos superiores no basta porque seguirían dentro de ese JSON. El iCal es anónimo, utiliza IDs de propiedad y contiene el nombre del huésped en `SUMMARY`; el token de exportación del modelo no se comprueba.

**Cierre:** definir una lista explícita de datos publicables, filtrar también JSON y recursos anidados y proteger el feed con token revocable. Los calendarios externos deberían indicar ocupación sin incluir nombres de huéspedes.

### 5. Entrada de automatizaciones sin autenticación — detectado por lectura

**Evidencia:** `integrations/views.py`, `n8n_inbound`.

Cualquier visitante puede insertar eventos. Además, las URLs configurables de webhooks e iCal se descargan desde el servidor sin controles visibles de destinos o redirecciones. Esto requiere revisar acceso a direcciones internas y limitar tamaño de respuesta.

**Cierre:** autenticar la entrada, comprobar firma y repetición de mensajes, restringir gestión de conectores y controlar destinos salientes. Añadir límites de petición a reservas y chats públicos; actualmente no hay throttling configurado en DRF.

## Prioridad 1: terminar la operación real

Las filas de contacto, inbox y cancelación recogen el hallazgo inicial; han recibido avances concurrentes descritos en la tabla anterior. El criterio de cierre completo sigue siendo válido.

| Pendiente | Evidencia e impacto | Criterio de cierre |
| --- | --- | --- |
| Enviar solicitudes de contacto | Landing: `ContactReservation` en `EditorialSections.tsx` solo valida y activa `submitted`; no envía ni guarda nada. | Persistir la solicitud y mostrar éxito solo tras la respuesta del servidor. Probar error y reintento. |
| Disponibilidad real en landing | `AvailabilityCalendar` usa apartamentos y precios fijos. No consulta ocupación. | Obtener calendario y cotización del backend, incluida la indisponibilidad por limpieza/mantenimiento/bloqueos según la regla acordada. |
| Retirar sustituciones de catálogo de ejemplo | `FeaturedApartments.tsx` y `ApartmentDetailPage.tsx` recurren a datos ficticios. Una ficha inexistente puede mostrar el primer apartamento de muestra. | Separar «sin resultados», «no encontrado» y «error». Reservar ejemplos para un modo demo explícito. |
| Inbox operativo | CRM: `UnifiedInbox.tsx` fabrica canales, mensajes y no leídos a partir de reservas. El envío y la selección de conversación no están conectados. | Leer `InboxMessage`, seleccionar hilo, guardar respuestas y conectar cada canal que se anuncie como disponible. |
| CMS editorial | CRM: `WebContentCMS.tsx` enlaza blog/guías y web pública a `/owners`. Las guías y textos viven en archivos de la landing. | Crear edición y publicación persistentes de contenidos o indicar qué contenido sigue gestionándose por código. Corregir destinos. |
| Cancelaciones y cambios de reserva | `bookings/signals.py` conserva el bloqueo y el ingreso al cancelar, reproducido en pruebas. La limpieza solo se crea una vez; no se reprograma si cambia la salida. | Definir transiciones y sincronizar calendario, limpieza, ingresos y comisiones al crear, modificar y cancelar. Cubrir cada transición con tests. |
| Integridad de escrituras | Reservas con señales, imágenes anidadas y reserva pública hacen varias escrituras sin una transacción explícita común. | Evitar registros parciales ante un fallo y hacer idempotentes las operaciones repetibles. |
| Pagos consistentes | `payments/models.py` cambia a PAID al cubrir el importe, pero no devuelve a PENDING si se corrige el pago a la baja. | Validar importes y recalcular estado en ambos sentidos. Definir devoluciones y cobros parciales. |
| Pasarela de cobro | `PaymentIntentViewSet` genera un enlace al CRM local; no crea una sesión en un proveedor. | Integrar el proveedor elegido en pruebas, confirmar cobros por webhook e impedir marcar pagos arbitrariamente desde el cliente. |
| Informes fiables | El dashboard pierde la última noche del mes por usar el último día como límite exclusivo. Informes y portal calculan totales sobre la primera página descargada; las noches incluyen canceladas. | Agregar en backend sobre el periodo completo; definir ocupación, ADR y RevPAR; probar fin de mes y más de una página. |
| Filtros de reservas | El hook manda estado, cliente y búsqueda, pero `BookingViewSet` solo implementa propiedad e intervalo de fechas. | Implementar y validar los filtros que ofrece la interfaz, con pruebas de resultados. |
| Actualización parcial de metadatos | `PropertySerializer.to_internal_value` puede reemplazar `equipment` al recibir un único campo adicional del CRM. | Una edición de ciudad debe conservar cocina, recursos y demás metadatos, salvo borrado explícito. |
| Actualización parcial de mantenimiento | `MaintenanceRequestSerializer` añade `cost=0` incluso si PATCH no incluye coste. | Cambiar solo los campos presentes; comprobar que modificar estado no borra el coste. |
| iCal robusto | El importador borra antes de terminar de validar; usa coincidencia parcial en notas; el exportador incluye reservas y sus bloques, duplicando ocupaciones. | Validar antes de reemplazar, usar identidad inequívoca, transacción, errores controlados y feeds sin duplicados. |
| Chatbot coherente | La página `/chatbot` usa reglas y retrasos simulados, mientras el widget llama al backend. El chat público guarda historial pero manda al modelo solo el último mensaje. | Unificar experiencia, acotar contexto e historial, manejar fallos del proveedor y aplicar los mismos permisos que el resto del CRM. |
| Conectores y cerraduras | Hay modelos y CRUD para proveedores, tarifas y códigos, pero eso no demuestra sincronización real. | Probar cada integración elegida con credenciales de prueba y distinguir claramente «configurado» de «conectado». |

## Prioridad 2: mantenimiento y entrega

1. **Dividir pantallas grandes por responsabilidad.** `PropertyForm.tsx` tiene 1.574 líneas y `CalendarPage.tsx` 688. Separar secciones del formulario, esquema y conversión de payload; separar agenda, filtros y edición. Evitar sustituirlas por una capa genérica difícil de seguir.
2. **Consolidar autenticación.** Existe `src/hooks/useAuth.tsx` antiguo que importa `authApi`, una exportación inexistente, junto al hook utilizado en `src/lib/hooks/useAuth.ts`. Retirar la implementación obsoleta tras revisar sus imports. El hook activo hace `trim()` a la contraseña: debe conservarla exactamente como la introduce el usuario.
3. **Completar contratos de API.** La landing contempla numerosos formatos alternativos para imágenes; usa `is_primary` mientras Django entrega `is_main`. Tipar y documentar una respuesta estable. Evitar `fields = '__all__'` en contratos que contengan información sensible.
4. **Mejorar errores y carga.** Mantener mensajes comprensibles, estados vacíos y cancelación de peticiones. Revisar respuestas tardías de `useProperty` cuando cambia el ID. No mostrar datos de muestra para esconder un error.
5. **Reducir consultas repetidas.** El conteo de pagos pendientes filtra por reserva pese al prefetch; el catálogo público cuenta reservas por apartamento sin anotación; el chatbot calcula pagos sin prefetch. Medir consultas en listados antes de optimizar más.
6. **Completar pruebas por reglas de negocio.** Las 27 pruebas Django actuales y las 20 del CRM son insuficientes para los módulos existentes. Priorizar permisos, concurrencia, precio, cancelaciones, pagos, metadatos y PATCH. La landing no tiene un script de tests. Añadir después un recorrido de navegador completo.
7. **Dependencias reproducibles.** `requirements.txt` ya recibió límites superiores durante la revisión, pero no incluye Pillow, aunque hay un `ImageField`. Verificar instalación desde un entorno vacío y registrar versiones compatibles. No se actualizaron paquetes como parte de mi limpieza; otra edición cambió las dependencias del CRM durante la revisión.
8. **TypeScript, lint y CI.** Corregir los errores de la comprobación de tipos recién incorporada y acordar un formato coherente; ejecutar tests y builds en cada cambio. No se encontraron workflows de CI en los proyectos revisados.
9. **Carga inicial del CRM.** Las rutas importan todas las pantallas de forma anticipada. Dividir por rutas con importación diferida, especialmente informes, gráficos y formularios, y medir el resultado.
10. **URLs por entorno.** Se detectaron enlaces a `127.0.0.1:5174`, referencias a Downloads y textos de implementación en `ChannelManager.tsx`; otra edición está sustituyéndolos por configuración. Verificar los destinos finales en local y producción. La landing necesita API/media configuradas en producción: su proxy de Vite es solo local y `vercel.json` reescribe a `index.html`.
11. **Persistencia en producción.** La configuración permite SQLite en `/tmp` sobre Vercel, útil para demo pero no como base de datos compartida y duradera. Cerrar PostgreSQL, almacenamiento de imágenes, copias y restauración antes de operar con datos reales. No se comprobó la configuración del despliegue existente.
12. **Arranque y despliegue observables.** `config/wsgi.py` oculta excepciones del bootstrap. Registrar errores y separar migraciones del arranque habitual. Revisar el ciclo de vida de la cuenta QA y la sincronización de contraseña de administrador.
13. **Repositorio claro.** Hay tres frontends, dos proyectos hermanos y documentos/archivos sin seguimiento. Documentar cuál es la aplicación activa y cómo se entrega cada proyecto. `start-local.sh` asume puertos libres y carpetas hermanas; hacerlo configurable y comprobar disponibilidad.
14. **Contenido y navegación de la landing.** Verificar reseñas e imágenes de ejemplo, traducciones completas, enlaces de pie, estados 404 y preferencias de cookies. El banner guarda una elección, pero eso por sí solo no verifica cómo se comportan scripts de terceros. No se evaluó cumplimiento normativo.
15. **Validar archivos subidos.** El endpoint de imágenes confía en MIME declarado y extensión; la prueba actual sube bytes que no forman una imagen completa. Decodificar y validar contenido real, tamaño y dimensiones, y aplicar permisos sobre la propiedad de destino.

## Orden recomendado para cerrar

1. Permisos internos/públicos y aislamiento de propietarios.
2. Precio, disponibilidad, transacciones y concurrencia de reservas.
3. Cancelaciones, pagos, limpiezas y métricas.
4. Formulario de contacto, inbox y CMS editorial conectados.
5. Pruebas de navegador, instalación limpia y despliegue persistente.
6. Refactor de pantallas grandes, rendimiento y retirada de demos.

Una entrega funcional debería demostrar este recorrido: publicar un apartamento → verlo en la landing → solicitar o crear una reserva con precio del servidor → verla en el CRM → registrar el cobro → modificar/cancelar sin dejar bloqueos ni importes incorrectos → verificar que otro propietario no accede a esos datos.
