# Matriz de trazabilidad requerimientos–implementación — ReportaYa

**Equipo 5 · TC5062 · S11-A1 · Parte 2**

| Campo | Valor |
|---|---|
| Requerimientos | `S03_A1/SRS_equipo.md` v2.0: 27 RF (RF-01 a RF-27), 161 criterios de aceptación `RF-XX-AC-Y` |
| Historias de usuario | `S03_A1/ajustes_backlog.md`: es el backlog completo de S03-A1 (el que la actividad llama `backlog_completo.md`), con 44 historias (HU-01 a HU-44) |
| Contrato del API | `backend/openapi_equipo.yaml` v1.1.0 (68 operaciones). Deriva de `S05_S06_A1/openapi_equipo.yaml` v1.0.0; los cambios están en `info.description` |
| Implementación revisada | `backend/` y `frontend/` de la rama `s11-correcciones`, prefijo del API `/api/v1` |
| Pruebas | **TR**: `backend/tests/test_reglas.py`, 125 casos, uno o más por criterio, con el reloj fijado (RNF-10), **125 de 125 en verde** (con `test_almacen`, `test_correo` y `test_respaldo`: 134 de 134) · **TC**: `backend/tests/test_contrato.py`, **68 de 68 operaciones, 1,058 verificaciones, 0 fallos** · **E2E**: recorrido en Chrome con Playwright de los cuatro roles, más las pruebas de RNF-01, 03, 04, 09 y 11 (secciones 4 y 5) |

## 1. Cómo leer la matriz

- **Endpoint:** ruta del contrato v1.1.0 que implementa el RF, sin el prefijo `/api/v1`.
- **Prueba:** casos de `test_reglas.py` (TR, por su nombre: `test_rf06_ac3_…` prueba RF-06-AC-3), sección de `test_contrato.py` (TC § …) o recorrido de interfaz (E2E).
- **Estado** (criterio aplicado a los criterios de aceptación del SRS):
  - **Completo:** todos los criterios del RF se cumplen y tienen prueba.
  - **Parcial:** se cumple al menos un criterio, pero falta alguno o alguno se incumple.
  - **No implementado:** ningún criterio del RF se cumple.

## 2. Resumen

| Estado | RF | Cantidad |
|---|---|---|
| Completo | RF-01 a RF-27 | **27** |
| Parcial | — | 0 |
| No implementado | — | 0 |

La versión anterior de esta matriz (revisión del 25/11/2026 sobre `main`, commit `383f4a0`) tenía **0 completos, 17 parciales y 10 sin implementar**. Faltaban el flujo de estados, la activación de cuentas, los avisos y el tablero, y el control de acceso por registro tenía la falla H-1 de S09-A1. Este documento refleja el sistema después de las correcciones de S11-A1.

Lo que **no** está resuelto no son RF, sino requerimientos no funcionales. Está en la sección 5 y no se oculta.

## 3. Matriz

| RF | Requerimiento | Historias | Endpoint implementado | Prueba | Estado | Justificación |
|---|---|---|---|---|---|---|
| **RF-01** | Autenticación por rol | HU-01 | `POST /auth/login`, `GET /auth/me`; control por rol en todas las rutas (`security.autorizar`) | TR `test_rf01_*`, `test_rnf06_*` · TC § Autenticación y cuentas · E2E 1–6 | Completo | Sesión con rol y unidad (AC-1); 401 con el mismo mensaje sin revelar qué falló (AC-2); el residente y el vigilante reciben 403 al asignar o cerrar (AC-3, AC-4). RNF-06: bcrypt, bloqueo de 15 min tras 5 intentos y sesión que vence tras 30 min de **inactividad** (token renovado en `X-Token-Renovado`). |
| **RF-02** | Padrón | HU-02, HU-03, HU-04, HU-16 | `GET`/`POST /units`, `GET`/`PATCH /units/{unitId}`, `/common-areas…`, `GET`/`POST /users`, `GET`/`PATCH /users/{userId}`, `/users/{userId}/unit-links`, `/external-providers…`, `GET /assignees` | TR `test_rf02_*`, `test_no_hay_registro_publico` · TC § Unidades, Usuarios · E2E 5 | Completo | Alta en «Pendiente de activación» **con envío del enlace** (AC-1, AC-4, AC-8); «El correo ya está registrado» (AC-2); los desactivados no entran (AC-3); «El correo del propietario es obligatorio» y «El piso es obligatorio» (AC-5, AC-6); proveedor «Sin acceso al sistema» (AC-7). **Se eliminó el registro público** `POST /auth/register` (EX-08). |
| **RF-03** | Alta por el residente | HU-10, HU-12, HU-13, HU-14 | `POST /reports` | TR `test_rf03_*` · TC § Reportes · E2E 1 | Completo | Los 10 criterios, con los mensajes del SRS. Se corrigió AC-4 (unidad ajena → 422). En la interfaz se conservan los datos si hay un error (AC-5, verificado en E2E) y se piden fotos antes de enviar sin ellas (AC-7). HU-14 depende de RNF-11, diferido (sección 5). |
| **RF-04** | Captura por terceros | HU-15, HU-16 | `POST /reports` (medio, fecha de aviso, reportante o nombre de referencia) | TR `test_rf04_*` · TC § Reportes | Completo | Los 9 criterios. Se corrigió AC-7: Vigilancia solo ve lo que registró. AC-3: el residente indicado lo ve en su lista y recibe el aviso de alta. |
| **RF-05** | Fotografías y video | HU-11 | `POST /reports` (etapa «Alta»), `POST /reports/{folio}/completions` («Evidencia»), `GET /reports/{folio}/files`, `GET /reports/{folio}/files/{fileId}`, `DELETE …/files/{fileId}` → 403 | TR `test_rf05_*`, `test_rf08_ac3_*` · TC § Flujo de estados | Completo | 0–5 fotos en el alta, 1–5 por ciclo en la evidencia; video MP4 de 50 MB; cada archivo se valida por separado con los mensajes del SRS (AC-1 a AC-6). Nadie borra fotos, ni la Administración (AC-7). Las fotos se descargan con sesión y según la matriz 2.3 (RD-08). |
| **RF-06** | Prioridad, asignación y reclasificación | HU-20, HU-21, HU-22 | `POST /reports/{folio}/assignments`, `PATCH /reports/{folio}/classification`, `GET /assignees` | TR `test_rf06_*` · TC § Notas…, § Flujo · E2E 2 | Completo | Los 10 criterios. Asignación con prioridad obligatoria, responsable, ubicación de origen, responsabilidad y responsable del costo. Reclasificación sin cambiar el estado, con valor anterior y nuevo en el historial. Al proveedor sin acceso no se le avisa (AC-10). |
| **RF-07** | Flujo de estados | HU-24, HU-26, HU-31 | `POST /reports/{folio}/cycles`, `…/completions`, `…/closures`, `…/cancellations`, `…/reopenings`, `…/merges`; tabla de transiciones en `app/reglas.py` | TR `test_rf07_*` · TC § Flujo, § Cancelación · E2E 3 | Completo | Solo las transiciones de la tabla del SRS; las demás responden 409 «Transición no permitida» (AC-2, AC-3, AC-7). El otro Mantenimiento recibe 404 (AC-4). Cancelación con motivo o «Ya se resolvió» (AC-5, AC-6, AC-9). El historial registra el registro hecho en nombre del proveedor sin acceso (AC-10). |
| **RF-08** | Terminado con evidencia | HU-25, HU-26, HU-40 | `POST /reports/{folio}/completions` (multipart) | TR `test_rf08_*` · TC § Flujo · E2E 3 | Completo | De 1 a 5 fotos por ciclo, separadas de las del alta (AC-1, AC-3); sin fotos → 422 (AC-2, AC-6). La excepción RD-09 marca «Terminado sin evidencia fotográfica» (AC-4, AC-5). Lo pendiente queda en el historial (AC-7). |
| **RF-09** | Confirmación y cierre | HU-35, HU-36 | `POST /reports/{folio}/resident-responses`, `POST /reports/{folio}/closures`, `POST /reports/{folio}/reopenings` | TR `test_rf09_*`, `test_rf27_ac4_*` · TC § Flujo · E2E 4, 5 | Completo | Una respuesta por ciclo dentro del plazo configurable. Cierre solo con «Ya quedó», plazo vencido, área común o reportante sin cuenta. Mensajes exactos: «Esperando confirmación del residente hasta el 25/09/2026 10:00» y «El plazo para responder terminó». Reapertura con ciclo nuevo (AC-5). |
| **RF-10** | Consulta del residente | HU-32 | `GET /reports`, `GET /reports/{folio}`, `GET /reports/{folio}/history` | TR `test_rf10_*`, `test_rnf05_*` · TC § Visibilidad por rol · E2E 4 | Completo | **Corrige H-1.** Ve solo su unidad desde su vinculación, lo que reportó y las áreas comunes (AC-1, AC-4). Otra unidad → 404 (AC-2). Las áreas comunes salen sin datos del reportante (AC-3). Ve «Unido a» (AC-5) y el motivo de detención (AC-6). Nunca recibe notas, monto, propietario ni responsable. |
| **RF-11** | Avisos | HU-33, HU-34 | Generados por cada transición (`app/notificaciones.py`); `GET /notifications`, `PATCH /notifications/{notificationId}`, `GET /email-deliveries` | TR `test_rf11_*` · TC § Avisos · E2E 5 | Completo | Aviso en el sistema y correo según la tabla de RF-11. Al propietario no residente solo le llega correo (AC-2). En áreas comunes no se avisa a propietarios (AC-3). Si el correo falla, el cambio se guarda y hay 3 intentos cada 10 min antes de «Fallido» (AC-4). En proceso no avisa al residente (AC-7). Reportante sin cuenta → aviso a la Administración (AC-8). Constancia en el historial. **El correo es simulado** (decisión del equipo, sección 5). |
| **RF-12** | Historial y búsqueda | HU-39, HU-40 | `GET /reports` (filtros exclusivos de la Administración), `GET /reports/{folio}`, `GET /reports/{folio}/history` | TR `test_rf12_*`, `test_rf06_ac2_*` · TC § Reportes · E2E 2 | Completo | Filtros combinables con rango inclusivo y orden descendente (AC-1); búsqueda por ubicación de origen (AC-2); fotos por etapa y ciclo e historial completo (AC-3); texto (AC-4). **Se corrigió AC-5:** la búsqueda del residente responde 403. |
| **RF-13** | Tablero | HU-41, HU-42, HU-43 | `GET /metrics` | TR `test_rf13_*`, `test_rf27_ac1_*` · TC § Tablero · E2E 5 | Completo | Por estado y categoría; promedios y cumplimiento por prioridad en dos bloques (AC-1: 70 min / 67 % y 22 h / 67 %; AC-7); recurrencia con ventana de 90 días que excluye cancelados (AC-2, AC-3); vencidos cuentan como incumplidos (AC-4); tiempo detenido (AC-5: 48 h); adopción (AC-6: 60 %). El Residente recibe 403 (AC-8). |
| **RF-14** | Activación y recuperación | HU-05, HU-06 | `POST /account-activations`, `POST /password-reset-requests`, `POST /password-resets`, `POST /users/{userId}/activation-links`; `scripts/init_db.py --admin-correo` | TR `test_rf14_*` · TC § Autenticación y cuentas | Completo | Enlace de un solo uso que vence en 72 h (AC-1) con el mensaje «El enlace venció; pida uno nuevo a la Administración» (AC-2). Recuperación con respuesta uniforme y vigencia de 1 h (AC-3). El comando de arranque crea el primer Administrador y le envía el enlace (AC-4). Solo se guarda el hash del token. |
| **RF-15** | Notas y visita | HU-27 | `GET`/`POST /reports/{folio}/notes`, `PUT`/`DELETE /reports/{folio}/visit` | TR `test_rf15_*`, `test_rnf05_*`, `test_rf11_ac7_*` · TC § Notas… | Completo | Nota interna de 1 a 500 caracteres sin cambiar el estado (AC-1). Visita visible para el residente, con aviso (AC-2). **Se corrigió AC-3:** el residente no recibe las notas. |
| **RF-16** | Lista de Mantenimiento | HU-23 | `GET /reports` con sesión de Mantenimiento (filtro y orden del servidor) | TR `test_rf16_*` · E2E 3 | Completo | Solo sus asignados en Asignado o En proceso, por prioridad y luego del aviso más antiguo al más reciente (AC-1, AC-2, AC-3). Muestra «Sin autorización de acceso: coordinar con la Administración» (AC-4). |
| **RF-17** | Duplicados | HU-17, HU-18 | `POST /reports` (marca `posibleDuplicado` y avisa), `GET /reports/possible-duplicates`, `POST /reports/{folio}/merges`, `DELETE /reports/{folio}/duplicate-flag` | TR `test_rf17_*` · TC § Cancelación y duplicados | Completo | Marca sin impedir el alta y aviso a la Administración (AC-1). Independiente (AC-2) y unión del más reciente (AC-3). Al cerrar el principal se avisa a los residentes de los unidos (AC-4). Otro piso (AC-5) o un cerrado (AC-6) no se marcan. |
| **RF-18** | Detenida | HU-28 | `POST /reports/{folio}/holds`, `PATCH /reports/{folio}/holds/{holdId}` | TR `test_rf18_*`, `test_rf13_ac5_*` · TC § Notas… | Completo | Marca sin cambiar el estado (AC-1); «Indique el motivo de la detención» (AC-2); reanudar (AC-3); en Terminado → 409 (AC-4); aviso al residente (AC-5). |
| **RF-19** | Persistencia y reapertura | HU-37 | `GET`/`POST /reports/{folio}/persistence-indications`, `POST /reports/{folio}/reopenings` | TR `test_rf19_*` · TC § Persistencia | Completo | Solo el residente reportante y dentro del plazo configurable (AC-1, AC-4: «El plazo para reabrir terminó»). Sigue Cerrado hasta que la Administración decide (AC-2). Reapertura con ciclo nuevo y comentario obligatorio (AC-3, AC-5). |
| **RF-20** | Costo y pagador | HU-29 | `GET`/`POST /reports/{folio}/costs` | TR `test_rf20_*`, `test_rnf05_*` · TC § Notas… | Completo | Monto opcional y pagador (AC-1, AC-2); «El monto no puede ser negativo» (AC-3); la corrección anula y conserva la anterior (AC-4). **Se corrigió AC-5:** el residente ve el pagador, no el monto. |
| **RF-21** | Delegación a la Auxiliar | HU-08 | `GET`/`POST /delegations`, `PATCH /delegations/{delegationId}`; `reglas.exigir_gestion` en asignar, reclasificar, cerrar, reabrir y unir | TR `test_rf21_*` · TC § Delegaciones | Completo | **La delegación ya tiene efecto:** sin delegación vigente la Auxiliar recibe 403 (AC-2, AC-3, AC-5); con ella asigna y el historial queda a su nombre (AC-1, AC-4). Nunca modifica parámetros (RF-27-AC-3). |
| **RF-22** | Reporte estancado | HU-38 | Tarea periódica (`notificaciones.revisar_estancados`, cada 60 s) | TR `test_rf22_*` | Completo | Aviso a la Administración al superar el umbral de su prioridad (AC-1), una sola vez hasta el siguiente cambio de estado (AC-2). Los detenidos no cuentan (AC-3). El umbral se puede configurar (AC-4). |
| **RF-23** | Exportación del tablero | HU-44 | `GET /metrics` con `Accept: application/pdf` | TR `test_rf23_*` · TC § Tablero · E2E 5 | Completo | PDF con periodo, tiempos, cumplimiento, recurrencia y adopción (AC-1). Las cifras salen del mismo cálculo que la pantalla, y la prueba lo verifica dentro del PDF (AC-2, RNF-16). El Residente recibe 403 (AC-3). |
| **RF-24** | Identificación del propietario | HU-07 | Padrón (`/units`); `propietario` en `GET /reports/{folio}` solo para la Administración | TR `test_rf24_*`, `test_rnf05_*` | Completo | No se pide al inquilino (AC-1: el contrato no tiene esos campos en el alta). La Administración ve nombre y correo (AC-2). **Se corrigió AC-3:** el inquilino no los ve. |
| **RF-25** | Garantía | HU-30 | `POST /reports/{folio}/completions` (`garantiaVencimiento`), `PUT /reports/{folio}/warranty` | TR `test_rf25_*` · TC § Flujo | Completo | Marca con vencimiento (AC-1, AC-3); «La fecha de vencimiento no puede ser pasada» (AC-2). |
| **RF-26** | Corrección por el residente | HU-19 | `PATCH /reports/{folio}` | TR `test_rf26_*` · TC § Reportes | Completo | Versiones con valor anterior y nuevo (AC-1, AC-2); recalcula la sugerida (AC-5). **Se corrigieron AC-3 y AC-4:** desde Asignado responde 409 «Transición no permitida», y el reporte ajeno, 404. |
| **RF-27** | Parámetros | HU-09 | `GET /parameters`, `PUT /parameters/{clave}`, `GET /parameters/{clave}/changes` | TR `test_rf27_*`, `test_rf21_*` · TC § Parámetros | Completo | El tablero usa el valor nuevo y la bitácora guarda valor anterior, nuevo, usuario y fecha (AC-1). «El valor debe ser mayor que cero» (AC-2). La Auxiliar recibe 403 (AC-3). El plazo de confirmación configurable aplica al ciclo siguiente (AC-4). Todos los parámetros los consume alguna regla. |

## 4. Verificación de la interfaz (E2E)

Se hizo el 26/11/2026 con Chrome (headless) y Playwright, sobre los datos de `scripts/cargar_demo.py`. Celular de 390 px para Residente y Mantenimiento (RNF-01) y computadora para la Administración. Las capturas sirven para el README.

| Paso | Rol | Qué se verificó | Criterios |
|---|---|---|---|
| 1 | Residente | Alta con foto; con la descripción corta aparece el mensaje del SRS y los datos siguen en el formulario | RF-03-AC-2, AC-5 [UI], RF-05 |
| 2 | Administración | Búsqueda por texto, detalle y asignación a «Ramón Torres» | RF-12, RF-06-AC-1 |
| 3 | Mantenimiento | Lista de asignados por prioridad; iniciar; terminar sin foto (422) y con foto | RF-16, RF-07-AC-1, RF-08-AC-1, AC-2 |
| 4 | Residente | Confirma «Ya quedó»; la pantalla no muestra notas internas ni datos del propietario | RF-09-AC-1, RF-15-AC-3, RF-24-AC-3 |
| 5 | Administración | Cierre; historial; tablero y PDF; avisos y correos; alta de un usuario con enlace | RF-09, RF-12-AC-3, RF-13, RF-23, RF-11, RF-02-AC-1 |
| 6 | Vigilancia | El reporte de la residente responde «No se pudo abrir el reporte» (404); su lista solo tiene los suyos | RF-04-AC-7, RNF-05 |

No hubo errores de JavaScript. Las únicas entradas de la consola son las respuestas 422 y 404 que se provocaron a propósito.

**Mutación de control:** al reintroducir a propósito la falla H-1 en `app/visibilidad.py`, 10 pruebas de `test_reglas.py` fallan. Al revertirla, vuelven a pasar. Las pruebas detectan la regresión.

**Otras verificaciones con el navegador** (scripts en `frontend/e2e/`, detalle en el README):

| Script | Qué se verificó | Requerimiento |
|---|---|---|
| `sin_conexion.py` | Sobre la versión compilada: sin señal la app abre desde el service worker, la lista guardada se muestra con aviso, un alta con foto queda «Pendiente» y al volver la señal pasa a «Enviado» con folio, **una sola vez** aunque se reintente. Mantenimiento abre sin señal el detalle de un asignado ya cargado | RNF-11, RF-03, RF-08 |
| `subida_10mb.py` | Foto JPEG de 9.9 MB con la red limitada a 10 Mbit/s: registrada en 8.5 s | RNF-04 |
| `accesibilidad.py` | 48 pantallas con axe-core (4 roles, formularios abiertos y errores visibles), a 360 px y 1280 px: 0 infracciones WCAG 2.1 AA, texto base de 16 px, sin desplazamiento horizontal. Se corrigió la tabla del tablero, que no se podía enfocar con el teclado | RNF-09, RNF-01 |

## 5. Requerimientos no funcionales y decisiones

| Requerimiento | Estado | Evidencia |
|---|---|---|
| **RNF-01** · Desde 360 px, sin instalar nada | Cumplido en Chrome | `accesibilidad.py` a 360 px sin desplazamiento horizontal; PWA instalable desde el navegador. No se probó en Safari de iOS ni en un Android de gama básica |
| **RNF-02** · Alta con foto en 3 pantallas o menos | Cumplido | Inicio → «Nuevo reporte» → enviar (E2E 1); Mantenimiento termina desde el detalle (E2E 3). No se probó con usuarios de poca experiencia digital |
| **RNF-03** · p95 ≤ 2 s con 5,000 reportes y 20 usuarios | Cumplido | `scripts/prueba_carga.py`: 5,000 reportes, 20 usuarios concurrentes durante 75 s, API limitado a 1 núcleo. 5,605 peticiones sin errores; p95 de 0.29 a 0.36 s en RF-10, RF-12 y RF-16 y de 1.06 s en el tablero (RF-13). La primera medición encontró pausas de ~10 s: la tarea periódica corría dentro del bucle de eventos; se pasó a un hilo |
| **RNF-04** · Foto de 10 MB en 15 s a 10 Mbit/s | Cumplido | `subida_10mb.py`: 8.5 s |
| **RNF-05** · Acceso en el servidor | Cumplido | Matriz 2.3 en `app/visibilidad.py`; `test_rnf05_*` y la mutación de control |
| **RNF-06** · Contraseñas, HTTPS, sesión y bloqueo | Cumplido | bcrypt, 30 min de inactividad con renovación (`X-Token-Renovado`) y bloqueo de 15 min tras 5 intentos (`test_rnf06_*`). HTTPS lo ponen Caddy (Compose) o Render |
| **RNF-07** · Historial inalterable | Cumplido | Disparadores de solo inserción y `DELETE` → 403 |
| **RNF-08** · Almacenamiento intercambiable | Cumplido | `app/almacen.py`: una interfaz, `AlmacenLocal` y `AlmacenS3` (AWS, R2, MinIO), elegidas con `ALMACEN`. `test_almacen.py` corre alta, descarga y evidencia con S3 simulado (moto) |
| **RNF-09** · Contraste 4.5:1 y 16 px | Cumplido | `accesibilidad.py`: 0 infracciones en 48 pantallas |
| **RNF-10** · Reloj controlable | Cumplido | `app/reloj.py`; todas las pruebas de plazos lo fijan |
| **RNF-11** · Mala conectividad | Cumplido | Service worker, cola en IndexedDB con las fotos, reintento automático con `Idempotency-Key` y estados «Pendiente»/«Enviado» (`sin_conexion.py`; `test_rnf11_*` en el servidor) |
| **RNF-12** · Disponibilidad 99 % | Depende de la operación | Compose reinicia los contenedores (`restart: unless-stopped`) y el API tiene `/health`. El plan gratuito de Render no cumple 99 %: se duerme sin uso |
| **RNF-13** · Retención | Cumplido por diseño | Nada se borra: reportes y fotos son de solo inserción. No hay purga automática de fotos después de 1 año |
| **RNF-14** · Respaldo y recuperación | Cumplido | `scripts/respaldo.py`: copia diaria consistente con verificación de integridad, rotación de 14 y restauración; `test_respaldo.py` respalda, pierde datos y restaura. Servicio `respaldo` en Compose |
| **RNF-15** · Fotos compartidas con terceros | Cumplido | Bitácora de qué foto, con quién y cuándo (`POST /reports/{folio}/files/{fileId}/shares`, verificada en la prueba de contrato) |
| **RNF-16** · Integridad de las cifras | Cumplido | El PDF y el tablero salen del mismo cálculo (`test_rf13_*`, `test_rf23_*`) |
| **RNF-17** · Costo bajo | Cumplido | Un servidor pequeño con Compose (memoria máxima medida del API: 207 MB con 5,000 reportes) o la demo gratuita de Render; fotos en disco o en R2/S3 |
| **Correo** | Decisión: simulado por omisión | `CORREO_MODO=smtp` envía de verdad (`CorreoSMTP`, probado contra un servidor SMTP local en `test_correo.py`). Falta configurar el buzón real del condominio |
| **Base de datos** | Decisión: SQLite | La arquitectura de S05 proponía PostgreSQL. El equipo se quedó con SQLite: el volumen del condominio lo permite (RNF-03 cumplido con 5,000 reportes) y simplifica el respaldo. Un solo proceso escribe |
| **Complejidad** (flake8) | Resuelto | Las 10 funciones que superaban complejidad 10 se dividieron sin cambiar su comportamiento (las 134 pruebas y el contrato siguen en verde); `flake8 app scripts` termina sin hallazgos (S09-A1: 96) |
