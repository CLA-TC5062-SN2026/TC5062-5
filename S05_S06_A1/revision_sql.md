# Revisión de `esquema_bd.sql`

Revisión de la primera versión del script (32 tablas, 2 vistas, 40 índices, 22 disparadores) contra `diagrama_clases_equipo.puml`, `openapi_equipo.yaml` y `SRS_equipo.md` v2.0, hecha antes de dárselo al equipo para ejecutarlo. La versión corregida es la que está en `esquema_bd.sql` (32 tablas, 2 vistas, **46 índices, 26 disparadores**).

Método: comparé el DDL con el diagrama mediante un script (clases ↔ tablas, atributos ↔ columnas, enums ↔ `CHECK`), revisé a mano cada asociación, y ejecuté el script en SQLite 3.45 con `PRAGMA foreign_keys=ON` junto con 45 inserciones inválidas que deben fallar.

## 1. Resultado por pregunta

| Pregunta | Resultado |
|---|---|
| ¿Están todas las entidades del diagrama? | **Sí.** Las 32 clases concretas y abstractas tienen tabla, salvo `Propietario` (objeto de valor 1..1), que vive en las columnas `unidad.propietario_*`. `Responsable` (interfaz) se materializa con las dos FK del reporte. Las 19 enumeraciones son `CHECK`. Sin diferencias (script). |
| ¿Están todos los atributos? | **Sí.** Ningún atributo persistente del diagrama falta como columna (script). Los derivados (`/etiqueta`, `/detenido`, `/montoCosto`, …) no se persisten a propósito; `/etiqueta` y `/reaperturas` salen de vistas. Columnas añadidas que no están en el diagrama: los discriminadores (`rol`, `tipo`) y sus constantes, `cambio_parametro.id` y `reporte`/`adjunto` sin id propio (ver §2, C-17). |
| ¿Las FK reflejan relaciones y cardinalidad? | **Sí, sin errores de tabla ni de cardinalidad.** Se revisaron las 41 asociaciones y composiciones. Se confirmó que 0..1 es columna nullable, 1 es `NOT NULL`, 0..1↔0..1 (`anulaCosto`) es `UNIQUE`, 0..5 y 0..1 de adjuntos se controlan con disparador e índice único, y la composición no usa `CASCADE` (RNF-07). Lo que faltaba eran **índices en varias FK** (C-15, C-16) y **reglas de negocio ligadas a las relaciones** (C-1 a C-8). |
| ¿Los tipos son coherentes con el API? | **Sí.** `piso`→INTEGER, `monto`/`valor`→NUMERIC, `tamanoBytes`→INTEGER, booleanos→0/1, UUID/fechas→TEXT. Lo que no se cumplía era la **validación de formato y longitud** que el API sí declara (C-9 a C-12). |
| ¿Faltan restricciones de negocio? | **Sí, 8 reglas del SRS no estaban** (C-1 a C-8) más 4 de calidad de datos (C-9 a C-12). Todas corregidas. |

## 2. Correcciones realizadas

### Reglas de negocio que faltaban

| # | Hallazgo | Fuente | Corrección |
|---|---|---|---|
| C-1 | `reporte` no impedía `fecha_captura < fecha_aviso`. (En mi primera versión había escrito un `CHECK` que siempre era verdadero y lo quité sin sustituirlo.) | RF-03, RF-04-AC-1 | `CHECK (fecha_captura >= fecha_aviso)`. |
| C-2 | Un reporte podía estar `Asignado`, `EnProceso`, `Terminado` o `Cerrado` sin prioridad ni responsable. | RF-06 (ambos obligatorios al asignar) | `CHECK` sobre `estado` que exige `prioridad` y uno de los dos responsables. `Cancelado` y `Unido` quedan libres. |
| C-3 | Se podía registrar un reporte sin subtipo en una categoría que define subtipos. | RD-01, RF-03 | Disparadores `trg_reporte_subtipo_ins/upd`. (La FK compuesta ya impedía un subtipo de otra categoría.) |
| C-4 | `parte_afectada` podía ir en un área común y `referencia` en una unidad. | RD-13 | Disparadores `trg_reporte_rd13_ins/upd`. |
| C-5 | Una Auxiliar podía tener varias delegaciones abiertas a la vez. | RF-21 (habilitar/deshabilitar) | Índice único parcial `ux_delegacion_vigente` (`habilitada=1 AND fecha_fin IS NULL`). |
| C-6 | `parametro.unidad` podía contradecir la clave (p. ej. `plazoConfirmacionHoras` en `dias`). | RF-27 | `CHECK` que liga el sufijo de la clave con la unidad; `minimoRecurrencia`→`reportes`. |
| C-7 | `Reclasificacion` y `Correccion` podían guardarse sin decir qué campo cambió ni el valor nuevo; un `cambio_estado` podía ir de un estado al mismo. | D7 del diagrama, RNF-07 | `CHECK` en `entrada_historial` (`campo` y `valor_nuevo` obligatorios) y en `cambio_estado` (`anterior <> nuevo`). |
| C-8 | Un correo `Enviado` podía tener 0 intentos y sin fecha de intento. | RF-11, `EmailDelivery` | `CHECK (estado <> 'Enviado' OR (intentos >= 1 AND fecha_ultimo_intento IS NOT NULL))`. |

### Calidad de datos y coherencia con el API

| # | Hallazgo | Corrección |
|---|---|---|
| C-9 | Las fechas eran `TEXT` libre. Las comparaciones (`fecha_fin >= fecha_inicio`, `vence_en > emitido_en`, `ORDER BY`) sólo son correctas si todas tienen el mismo formato. | `CHECK` en las 23 columnas de fecha-hora: patrón `YYYY-MM-DDTHH:MM:SSZ` y `julianday()` válido. `garantia_vencimiento` valida `date(x) = x`. |
| C-10 | Los UUID no tenían validación (el API declara `format: uuid`). | `CHECK (length(id) = 36)` en las 11 tablas con id UUID. |
| C-11 | El API exige `minLength: 1` en `nombre`/`especialidad`/`telefono` de proveedor y nombre del propietario, y `maxLength: 1000` en comentarios. | `CHECK` de no vacío en `proveedor_sin_acceso` y `unidad.propietario_nombre`; `entrada_historial.comentario <= 1000`; `adjunto.nombre` no vacío. |
| C-12 | `nombre_referencia` aceptaba cadenas en blanco, con lo que se burlaba la regla de RF-04 (sin reportante, la referencia es obligatoria). | `CHECK (nombre_referencia IS NULL OR length(trim(...)) > 0)`. |

### Índices

| # | Hallazgo | Corrección |
|---|---|---|
| C-13 | Sin cambios de fondo en los índices de búsqueda pedidos (`usuario.correo` único, `usuario.nombre`, unidad, proveedor, reporte). | Se confirmaron con `EXPLAIN QUERY PLAN`: la búsqueda por correo usa el índice único, por nombre usa `ix_usuario_nombre` y por estado usa `ix_reporte_estado_prio`. |
| C-14 | Faltaba el historial de vinculaciones por residente (el índice parcial sólo cubre la vigente). | `ix_vinculacion_residente`. |
| C-15 | FK sin índice usadas en joins: `reporte.ubicacion_origen_id`, `indicacion_persistencia.residente_id`, `cambio_estado.actua_en_nombre_de_id`, `confirmacion_residente.respondida_por`. | `ix_reporte_origen`, `ix_persist_residente`, `ix_cambio_estado_prov`, `ix_confirm_residente`. |

### Otros

| # | Hallazgo | Corrección |
|---|---|---|
| C-16 | Al preparar las correcciones se detectó que SQLite **acepta sin error constraints de tabla sin coma entre ellas**. Un comentario `--` seguido de una coma "tragada" no produce error, así que un archivo mal formado puede cargar igual. | Se revisó todo el DDL: ninguna coma separadora queda dentro de un comentario. |
| C-17 | Decisiones de modelado que conviene dejar explícitas. | `reporte` usa `folio` como PK (es el identificador del API); `ciclo_atencion` usa PK compuesta `(reporte_folio, numero)`; `cambio_parametro.id` es un entero autoincremental porque el diagrama no le da identidad. |

## 3. Lo que no se pudo imponer en SQL (queda en la aplicación)

- **Subclase obligatoria:** que cada fila de `entrada_historial` tenga su fila hija según `tipo` (igual para `aviso`, y para `usuario` con su subtabla de rol). SQLite no tiene restricciones diferidas entre tablas; se resuelve insertando madre e hija en una sola transacción.
- **Autorización de acceso:** `autoriza_acceso` es obligatoria sólo cuando la ubicación es la unidad del residente (RF-03), y el efecto de responder «No» (RD-06).
- **Folio consecutivo** `RY-######` (la tabla sólo valida el formato y la unicidad).
- **Ciclos:** numeración consecutiva, plazo de confirmación y mínimo 1 foto de evidencia al terminar (salvo RD-09).
- **Transiciones de estado y permisos por rol** (patrón State en la capa de dominio); que el reportante de una confirmación o de una indicación de persistencia sea el residente del reporte.
- **Formato exigido por las nuevas restricciones:** la API debe escribir fechas en UTC con sufijo `Z` y UUID de 36 caracteres. **Punto a confirmar:** el SRS (sección 1.3) dice que las fechas se «registran» en la zona horaria del condominio (`America/Mexico_City`). El esquema las guarda en UTC y la conversión se hace al mostrar, porque el API usa `date-time` y las comparaciones por texto exigen un formato uniforme. Si el equipo prefiere guardar hora local, hay que cambiar el patrón de C-9.

## 4. Verificación posterior a las correcciones

- El script carga sin errores; `PRAGMA foreign_key_check` e `integrity_check` limpios.
- 32/32 clases con tabla, 0 atributos faltantes, 0 enums distintos de los del API.
- 45 inserciones inválidas rechazadas, incluidas las de C-1 a C-12.

---

# Correcciones al código generado

Revisión de la Parte 2 (servicios CRUD en `reportaya_api/`, FastAPI + SQLite) contra `openapi_equipo.yaml`. Método: el script `tests/test_contrato.py` levanta flujos reales contra el servidor y, **en cada respuesta**, comprueba que (1) el código HTTP esté declarado para esa operación, (2) el cuerpo cumpla el schema del YAML y (3) estén los encabezados `Location`/`ETag` que el YAML declara. También compara el conjunto de rutas y métodos del servidor con el del YAML.

**Resultado final:** 46 de las 69 operaciones implementadas, 0 rutas que no estén en el YAML, 46/46 ejercitadas, 697 verificaciones y 0 fallos. Se confirmó la conexión a la BD con `GET /health` (`llavesForaneas: true`), y `PRAGMA integrity_check` y `foreign_key_check` quedaron limpios tras las pruebas.

## 1. Divergencias con el YAML encontradas y corregidas

| # | Hallazgo (primera versión del código) | Contrato | Corrección |
|---|---|---|---|
| G-1 | `GET /units/{unitId}` y `GET /reports/{folio}` con un id mal formado respondían **400**. | El YAML solo declara 200/401/403/404/500 en esos GET. | Un identificador de ruta mal formado responde **404** `NO_ENCONTRADO`, porque no puede existir. Se aplica a todos los GET por id (`main.py`). |
| G-2 | `POST /reports/{folio}/persistence-indications` con `comentario` de más de 1000 caracteres respondía **422**. | La operación no declara 422, y su schema fija `maxLength: 1000`. | Responde **400**. |
| G-3 | `DELETE /reports/{folio}/visit` fallaba con 422 (restricción de la BD). | Debe responder 204 (o 409). | Choque con la restricción C-7 de la primera revisión (una `Correccion` exige `valor_nuevo`). La cancelación se registra con `valor_nuevo = 'Cancelada'`. El manejador de `IntegrityError` evitó un 500, pero devolvía un 422 no declarado: por eso G-3 se detectó. |

## 2. Decisiones de interpretación (el YAML no las fija)

- **400 contra 422.** Se usa 400 para lo que no se puede interpretar: JSON inválido, tipo de dato incorrecto, campo desconocido y parámetro de consulta inválido (incluye enums en la URL). Se usa 422 para el valor de un campo del cuerpo que no cumple una regla (cadena vacía, valor fuera de un enum del cuerpo, correo sin formato).
- **Duplicados.** `POST /units`, `/common-areas` y `/users` no declaran 409, así que un duplicado (torre y número, nombre, correo) responde **422**. `POST /delegations` sí declara 409 y se usa cuando la Auxiliar ya tiene una delegación abierta.
- **Precedencia 404 → 409 → 422.** El cuerpo se recibe como JSON crudo y se valida después de comprobar que el recurso existe y que el estado lo permite. Así un cuerpo inválido sobre un reporte inexistente responde 404, no 422.
- **ETag.** Es un hash del JSON del recurso. Para el alta de un reporte se calcula sin `archivosRechazados`, de modo que el ETag del 201 sirva como `If-Match`.
- **Fechas.** La BD guarda UTC y la API responde en `America/Mexico_City` (`TIMEZONE`), según el contrato; acepta fechas con o sin zona. Los rangos `avisoDesde`/`avisoHasta` son por días completos del condominio.
- **Costos.** `montoCosto` y `pagador` del detalle salen del último costo **no anulado**. Una anulación conserva la entrada original (`anulada: true`).
- **Merge-patch.** `ubicacion` en `PATCH /reports/{folio}` reemplaza la ubicación completa; en `propietario` (unidades) sí se fusionan los campos enviados.
- **Visita.** El modelo de datos no tiene un tipo de historial «Visita». Fijar o cancelar la visita se registra como `Correccion` del campo `fechaVisita`. Conviene decidir si se agrega un tipo propio (afecta `TipoEntradaHistorial` en el YAML y en el diagrama de clases).
- **Parámetros.** `PUT /parameters/{clave}` y las delegaciones responden 403 si el actor no es Administrador. No es seguridad por rol: lo exige la FK `modificado_por → usuario_administracion` del esquema.

## 3. Divergencias conocidas que se dejan (fuera de alcance de esta entrega)

**No implementado por pertenecer a seguridad (siguiente actividad):** `POST/GET/DELETE /sessions`, `/account-activations`, `/password-reset-requests`, `/password-resets` y `/users/{userId}/activation-links`; los 401; los 403 por rol; la matriz de visibilidad 2.3 (campos que se ocultan según el rol, `mensajeAcceso`, alcance de la lista de reportes por rol). Quien actúa se toma de `X-Actor-Id` o del primer Administrador. Al crear un usuario no se emite el enlace de activación (RF-14).

**No implementado por ser reglas de negocio / flujo (siguiente actividad):** transiciones `assignments`, `classification`, `cycles`, `completions`, `resident-responses`, `closures`, `reopenings`, `cancellations`, `merges`, `duplicate-flag`; `warranty`; archivos (`files`, `shares`); `GET /metrics`. Para probar notas, detenciones y persistencia, la prueba deja el reporte en `Asignado`/`Cerrado` escribiendo directamente en la BD.

**Parcial:**
- `Idempotency-Key` se acepta pero **no se aplica** (RNF-11): el esquema no tiene tabla de idempotencia (está fuera del dominio del diagrama). Hace falta una tabla `idempotencia(clave, ruta, respuesta)` para cumplirlo.
- Las acciones no generan avisos ni correos (RF-11): eso lo hace el Worker por el outbox. `GET /notifications` y `/email-deliveries` leen lo que haya en la BD (el script de demo carga un aviso y un correo).
- El alta de un Residente no restringe su ubicación a su unidad o a un área común, ni rechaza con 403 sus campos de captura según su vinculación; sí rechaza los campos de captura cuando el actor es Residente.
- Los archivos del alta se guardan en `UPLOAD_DIR` y quedan registrados en `adjunto`, pero no hay endpoint de descarga.

## 4. Observaciones sobre el YAML (para corregir en la próxima revisión del contrato)

- `GET /delegations` declara el parámetro `vigente` pero ninguna respuesta 400, y `GET /common-areas` no declara paginación mientras que `GET /units` sí. Un `vigente` inválido responde 400 con el esquema `Error`.
- `POST /reports/{folio}/persistence-indications`, `POST /reports/{folio}/notes` y `PUT /reports/{folio}/visit` usan `type: object` en línea; conviene darles nombre en `components/schemas` (hoy no se pueden validar por `$ref`).
- Las operaciones que crean registros (`notes`, `costs`, `holds`, `persistence-indications`) aceptan `Idempotency-Key` pero no hay dónde guardarla (ver §3).

## 5. Cómo reproducir

```bash
cd reportaya_api
pip install -r requirements.txt && cp .env.example .env
python scripts/init_db.py --reset --demo
python -m app.main                      # otra terminal:
python tests/test_contrato.py           # requiere una BD recién creada con --reset --demo
```
