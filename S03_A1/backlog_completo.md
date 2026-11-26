# Product Backlog — ReportaYa

| Campo | Valor |
|---|---|
| Actividad | S03-A1 · Product Backlog de SCRUM |
| Fuente de verdad | `SRS_equipo.md` (v2.0, 3 de octubre de 2026) |
| Documento de apoyo | `diferencias_SRS.md` |
| Contenido | 5 épicas, 15 historias de usuario (HU-01 a HU-15) |
| Fecha | 4 de octubre de 2026 |

Todos los identificadores `RF-XX`, `RF-XX-AC-Y`, `RNF-XX`, `RD-XX` y `EX-XX` son los de `SRS_equipo.md`, sin cambios. Los criterios de aceptación de cada historia resumen los del SRS; los umbrales, mensajes, estados, permisos y actores son los del SRS.

---

## 1. Objetivo del Product Backlog

Ordenar el trabajo para construir ReportaYa en historias de usuario que aporten valor a sus actores (Residente, Vigilancia, Mantenimiento y Administración) y que se puedan verificar contra los criterios de aceptación del SRS. El backlog prioriza el **alcance mínimo de 12 semanas** (R-04), que la sección 5, punto 15 de `SRS_equipo.md` define como **RF-01 a RF-16 y RF-27**. La sección 1.2 lo expresa de forma resumida: alta de reporte con fotos y ubicación, clasificación y asignación, seguimiento de estado, cierre con evidencia y tablero de tiempos e incidencias recurrentes.

## 2. Leyenda de prioridades del backlog

| Prioridad | Criterio |
|---|---|
| **Alta** | La historia implementa RF del alcance mínimo de 12 semanas (sección 5, punto 15: RF-01 a RF-16 y RF-27). Se debe entregar en las 12 semanas. |
| **Media** | La historia implementa un RF que el SRS asigna a la segunda fase, pero aporta valor de negocio inmediato o completa criterios del alcance mínimo que dependen de ella. Se trabaja después de las historias Alta si hay capacidad. |
| **Baja** | La historia implementa un RF de segunda fase sin dependencias del alcance mínimo. En esta versión del backlog no hay historias Baja (ver sección 8). |

## 3. Escala de Story Points

Se usa la escala de Fibonacci modificada **1, 2, 3, 5, 8, 13**. Los puntos son relativos: miden esfuerzo, complejidad e incertidumbre frente a las demás historias, no horas.

| SP | Referencia |
|---|---|
| 1 | Cambio trivial, sin reglas nuevas. |
| 2 | Regla simple sobre un dato existente. |
| 3 | Una función acotada, pocas reglas, reutiliza lo ya construido. |
| 5 | Función completa con varias validaciones o permisos por rol. |
| 8 | Varias reglas de negocio que interactúan (estados, archivos, tiempos o varios actores). |
| 13 | Máximo permitido: cálculos o flujos con muchos casos de borde. Una historia que superaría 13 se divide. |

## 4. Prioridad del backlog frente a prioridad de las incidencias

La **prioridad del backlog** (Alta, Media, Baja) indica el orden en que el equipo construye las historias. La **prioridad de una incidencia** (`Urgente`, `Normal`, `Menor`, RD-01) es un dato de cada reporte dentro del sistema, que la Administración decide (RF-06) y que se mide contra los tiempos objetivo de RD-02. No tienen relación: una historia Alta puede tratar sobre reportes `Menor`, y `Urgente` nunca es una prioridad del backlog.

---

## 5. Épicas

| Épica | Nombre | Qué cubre del SRS | Historias |
|---|---|---|---|
| **EP-01** | Acceso y padrón del condominio | RF-01, RF-02, RF-14 · RNF-05, RNF-06 · EX-08 | HU-01, HU-02 |
| **EP-02** | Registro de reportes | RF-03, RF-04, RF-05 (etapa «Alta») · RD-01, RD-13 · RNF-02, RNF-04, RNF-08. RF-17 (duplicados) se difiere a segunda fase. | HU-03, HU-04 |
| **EP-03** | Clasificación, asignación y atención | RF-06, RF-07 (`Reportado → Asignado → En proceso`, cancelación por la Administración), RF-15, RF-16, RF-18 · RD-01, RD-03, RD-06, RD-10 | HU-06, HU-07, HU-08 |
| **EP-04** | Seguimiento y cierre con evidencia | RF-07 (`Terminado`, `Cerrado`, cancelación por el residente, reapertura desde `Terminado`), RF-05 (etapa «Evidencia»), RF-08, RF-09, RF-10, RF-11 · RD-04, RD-05, RD-09 | HU-09, HU-10, HU-11, HU-12 |
| **EP-05** | Historial, tablero y parámetros | RF-12, RF-13, RF-23, RF-27 · RD-02, RD-14 · RNF-03, RNF-16 | HU-05, HU-13, HU-14, HU-15 |

## 6. Resumen del backlog

| ID | Épica | Actor | Resumen | SP | Prioridad | RF relacionados |
|---|---|---|---|---|---|---|
| HU-01 | EP-01 | Administración | Administrar el padrón: unidades, áreas comunes, usuarios y proveedores | 5 | Alta | RF-02 |
| HU-02 | EP-01 | Usuario con cuenta | Activar la cuenta, iniciar sesión por rol y recuperar la contraseña | 5 | Alta | RF-01, RF-14 |
| HU-03 | EP-02 | Residente | Reportar una falla con ubicación, fotos y video | 8 | Alta | RF-03, RF-05 |
| HU-04 | EP-02 | Administración / Vigilancia | Capturar un reporte recibido por otro medio | 5 | Alta | RF-04, RF-05 |
| HU-05 | EP-05 | Administración | Exportar el tablero a un archivo imprimible | 3 | Media | RF-23 |
| HU-06 | EP-03 | Administración | Clasificar, asignar, reclasificar o cancelar un reporte | 8 | Alta | RF-06, RF-07 |
| HU-07 | EP-03 | Mantenimiento | Ver asignados, iniciar la atención, notas y fecha de visita | 8 | Alta | RF-16, RF-07, RF-15 |
| HU-08 | EP-03 | Mantenimiento / Administración | Marcar un reporte como detenido y reanudarlo | 3 | Media | RF-18 |
| HU-09 | EP-04 | Mantenimiento | Marcar `Terminado` con evidencia fotográfica | 5 | Alta | RF-08, RF-05, RF-07 |
| HU-10 | EP-04 | Residente | Consultar el estado de mis reportes y cancelar uno ya resuelto | 5 | Alta | RF-10, RF-15, RF-07 |
| HU-11 | EP-04 | Residente reportante | Recibir avisos por correo y en el sistema | 8 | Alta | RF-11 |
| HU-12 | EP-04 | Administración | Cerrar o reabrir según la confirmación del residente | 8 | Alta | RF-09, RF-07 |
| HU-13 | EP-05 | Administrador | Ajustar objetivos, plazos y umbrales | 3 | Alta | RF-27 |
| HU-14 | EP-05 | Administración | Buscar reportes y consultar su historial completo | 5 | Alta | RF-12 |
| HU-15 | EP-05 | Administración | Consultar el tablero de tiempos, recurrencia y adopción | 13 | Alta | RF-13 |

**Distribución de Story Points:**

| Prioridad | Historias | Story Points |
|---|---|---|
| Alta | 13 | 86 |
| Media | 2 | 6 |
| Baja | 0 | 0 |
| **Total** | **15** | **92** |

---

## 7. Historias de usuario

### EP-01 · Acceso y padrón del condominio

#### HU-01 · Administrar el padrón del condominio

| Campo | Valor |
|---|---|
| Épica | EP-01 · Acceso y padrón del condominio |
| RF relacionados | RF-02 |
| RNF / RD aplicables | RNF-05, RD-07, EX-08 |
| Story Points | 5 |
| Prioridad | Alta |

**Historia.** Como Administración del condominio, quiero dar de alta, editar y desactivar unidades, áreas comunes, usuarios por rol y proveedores externos, para que cada reporte quede ligado a una ubicación y a personas reales del condominio y solo la Administración decida quién tiene cuenta.

**Criterios de aceptación:**

1. Al dar de alta un Residente con ocupación «Inquilino» vinculado a `B-502`, el usuario queda «Pendiente de activación» y se le envía el enlace de activación. *(RF-02-AC-1)*
2. Si ya existe un usuario con el mismo correo, el sistema responde 422 con «El correo ya está registrado» y no crea el usuario. *(RF-02-AC-2)*
3. Un usuario desactivado recibe 401 al iniciar sesión con su contraseña correcta, y sus reportes anteriores siguen visibles para la Administración. *(RF-02-AC-3)*
4. Al dar de alta «Bombas del Norte» con rol Mantenimiento, tipo «Proveedor externo», especialidad y teléfono, queda «Pendiente de activación», recibe el enlace y aparece en la lista de responsables. *(RF-02-AC-4)*
5. Una unidad sin correo del propietario se rechaza con 422 «El correo del propietario es obligatorio»; una unidad sin piso, con 422 «El piso es obligatorio». *(RF-02-AC-5, RF-02-AC-6)*
6. Al registrar «Elevadores del Centro» como proveedor sin acceso, no se crea cuenta ni se envía enlace, y aparece en la lista de responsables marcado «Sin acceso al sistema». *(RF-02-AC-7)*
7. Un usuario con rol Vigilancia queda «Pendiente de activación» y, una vez activo, solo ve las funciones de captura de RF-04. *(RF-02-AC-8)*
8. Nadie puede registrarse por su cuenta: toda cuenta la crea la Administración, y el propietario no residente no tiene cuenta. *(regla de RF-02; EX-08)*

**Justificación de Story Points (5).** Es la administración de cuatro entidades con validaciones de campos obligatorios y dos tipos de proveedor. No tiene flujo de estados ni cálculos; el envío del enlace reutiliza HU-02.

**Justificación de prioridad (Alta).** RF-02 está en el alcance mínimo (sección 5, punto 15). Sin padrón no hay unidades, áreas comunes, residentes ni responsables, por lo que ninguna otra historia se puede usar.

---

#### HU-02 · Activar la cuenta, iniciar sesión por rol y recuperar la contraseña

| Campo | Valor |
|---|---|
| Épica | EP-01 · Acceso y padrón del condominio |
| RF relacionados | RF-01, RF-14 |
| RNF / RD aplicables | RNF-05, RNF-06, RNF-10 |
| Story Points | 5 |
| Prioridad | Alta |

**Historia.** Como usuario con cuenta (Residente, Vigilancia, Mantenimiento o Administración), quiero activar mi cuenta con el enlace que recibo, iniciar sesión y recuperar mi contraseña si la olvido, para usar solo las funciones de mi rol sin depender de la Administración para entrar.

**Criterios de aceptación:**

1. Un Residente activo con contraseña válida inicia sesión y recibe una sesión que indica el rol Residente y la unidad `B-502`. *(RF-01-AC-1)*
2. Con una contraseña incorrecta, el sistema responde 401 con «Correo o contraseña incorrectos», sin indicar cuál de los dos falló. *(RF-01-AC-2)*
3. Si el inquilino de `B-502` intenta asignar el reporte `RY-000124`, el sistema responde 403 y el reporte no cambia. *(RF-01-AC-3)*
4. Si el Vigilante intenta cerrar o asignar el reporte `RY-000125` que registró, el sistema responde 403 y el reporte no cambia. *(RF-01-AC-4)*
5. Al abrir el enlace de activación dentro de las 72 horas y definir una contraseña válida, la cuenta pasa a «Activa» y el enlace deja de funcionar. *(RF-14-AC-1)*
6. Un enlace emitido el 20/09/2026 a las 10:00 y usado el 23/09/2026 a las 10:01 se rechaza con 422 «El enlace venció; pida uno nuevo a la Administración». *(RF-14-AC-2)*
7. Al pedir la recuperación se envía un enlace de un solo uso que vence en 1 hora; si el correo no existe, la respuesta es la misma. *(RF-14-AC-3)*
8. Con la base de datos sin usuarios, el comando de arranque crea el primer usuario con rol Administración y le envía el enlace de activación. *(RF-14-AC-4)*
9. Restricciones: contraseñas con hash con sal (bcrypt o Argon2) de al menos 8 caracteres, HTTPS, sesión que expira tras 30 minutos de inactividad y bloqueo de 15 minutos tras 5 intentos fallidos consecutivos. *(RNF-06)*

**Justificación de Story Points (5).** Incluye autenticación, control por rol, dos tipos de enlace de un solo uso con vencimiento y el comando de arranque. Son reglas conocidas y bien acotadas, pero con varios casos de seguridad que probar con el reloj controlable (RNF-10).

**Justificación de prioridad (Alta).** RF-01 y RF-14 están en el alcance mínimo. Toda historia depende de que cada actor entre con su rol, y la activación por enlace es la consecuencia de que solo la Administración cree cuentas (C-10).

---

### EP-02 · Registro de reportes

#### HU-03 · Reportar una falla con ubicación, fotos y video

| Campo | Valor |
|---|---|
| Épica | EP-02 · Registro de reportes |
| RF relacionados | RF-03, RF-05 |
| RNF / RD aplicables | RNF-01, RNF-02, RNF-04, RNF-07, RNF-08, RD-01, RD-13 |
| Story Points | 8 |
| Prioridad | Alta |

**Historia.** Como Residente, quiero reportar desde mi celular una falla de mi departamento o de un área común con su ubicación, fotos y, si hace falta, un video, para que quede registrada con folio y fecha de aviso y no se pierda como pasa con los mensajes de WhatsApp o la libreta.

**Criterios de aceptación:**

1. Si el último folio es `RY-000123`, al registrar un reporte válido el sistema crea `RY-000124` en `Reportado`, con fecha de aviso igual a la hora del sistema y medio de origen «Sistema». *(RF-03-AC-1)*
2. Una descripción de menos de 10 caracteres se rechaza con 422 «La descripción debe tener entre 10 y 1,000 caracteres» y no se crea el reporte. *(RF-03-AC-2)*
3. Si la ubicación es su unidad y no responde la autorización de acceso, el sistema responde 422 «Indique si autoriza el acceso a su departamento». *(RF-03-AC-3)*
4. Si intenta reportar en una unidad ajena (`A-301`), el sistema responde 422 «Solo puede reportar en su unidad o en áreas comunes». *(RF-03-AC-4)*
5. **[UI]** Si hay un error de validación, los datos capturados siguen en el formulario. *(RF-03-AC-5)*
6. Sin respuesta a «¿El problema es peligroso o está empeorando?», el sistema responde 422 «Indique si el problema es peligroso o está empeorando» y no crea el reporte. *(RF-03-AC-6)*
7. Sin fotografías, el reporte se crea; **[UI]** antes de enviar, la interfaz pide adjuntar fotografías. *(RF-03-AC-7)*
8. Con la parte afectada «Baño», el reporte queda con torre, piso, número de unidad y parte afectada. *(RF-03-AC-8)*
9. «Desde cuándo pasa», «si ya había pasado antes» y los horarios de acceso son opcionales; si se indican, quedan guardados. *(RF-03-AC-9)*
10. En una categoría con subtipo (por ejemplo, «Iluminación») sin subtipo, el sistema responde 422 «Indique el subtipo». *(RF-03-AC-10)*
11. Se aceptan de 0 a 5 fotos JPEG o PNG de hasta 10 MB en la etapa «Alta». Tres fotos de 4 MB quedan en esa etapa; un PDF se rechaza con «Formato no permitido: use JPEG o PNG» sin impedir el alta; una foto de 12 MB se rechaza con «La foto supera 10 MB»; 6 fotos se rechazan con 422 «Máximo 5 fotografías por etapa» y no se crea el reporte. *(RF-05-AC-1, RF-05-AC-2, RF-05-AC-3, RF-05-AC-4)*
12. Se acepta 1 video MP4 de hasta 50 MB (uno de 30 MB queda asociado y consultable); uno de 60 MB se rechaza con «El video supera 50 MB». *(RF-05-AC-5, RF-05-AC-6)*
13. Ningún usuario, ni la Administración, puede borrar una fotografía: el sistema responde 403. *(RF-05-AC-7)*
14. El sistema no le pide al inquilino datos del propietario. *(RF-24-AC-1, se cumple de forma transversal; ver sección 8)*
15. Restricciones: el registro con una foto se hace en máximo 3 pantallas desde que inicia sesión (RNF-02); una foto de 10 MB se sube en 15 segundos o menos a 10 Mbit/s (RNF-04); los archivos se guardan mediante la interfaz intercambiable de almacenamiento (RNF-08).

**Justificación de Story Points (8).** Combina un formulario con muchas validaciones condicionales (subtipo, autorización según la ubicación, peligro), la asignación de folio, la carga de archivos con validación individual y el almacenamiento intercambiable. No llega a 13 porque es un solo recurso y no tiene flujo de estados.

**Justificación de prioridad (Alta).** Es el primer elemento del alcance mínimo («alta de reporte con fotos y ubicación») y RF-03 y RF-05 están en la sección 5, punto 15. Además, sostiene el objetivo medible 1 del SRS (todo reporte con folio y fecha de aviso).

---

#### HU-04 · Capturar un reporte recibido por otro medio

| Campo | Valor |
|---|---|
| Épica | EP-02 · Registro de reportes |
| RF relacionados | RF-04, RF-05 |
| RNF / RD aplicables | RNF-05, EX-06 |
| Story Points | 5 |
| Prioridad | Alta |

**Historia.** Como Administración o Vigilancia, quiero capturar un reporte que llegó por WhatsApp, llamada, caseta, correo o en persona, indicando el medio y la fecha real del aviso, para que todo aviso quede en el registro único y sus tiempos se midan desde que el condominio se enteró.

**Criterios de aceptación:**

1. Se exigen los mismos campos obligatorios de RF-03, más el medio de origen («WhatsApp», «Llamada», «Caseta», «Correo» o «Presencial») y la fecha y hora de aviso; el sistema guarda siempre quién capturó. *(regla de RF-04)*
2. Un aviso del 20/09/2026 22:10 capturado el 21/09/2026 09:00 con medio «Caseta» queda con esa fecha de aviso, fecha de captura 21/09/2026 09:00 y medio «Caseta», y sus tiempos se calculan desde el 20/09/2026 22:10. *(RF-04-AC-1)*
3. Una fecha de aviso futura se rechaza con 422 «La fecha del aviso no puede ser futura». *(RF-04-AC-2)*
4. Si se indica como residente reportante al inquilino de `B-502`, el reporte aparece en su lista y él recibe el aviso de alta. *(RF-04-AC-3)*
5. Con ubicación `B-502` sin autorización de acceso, el sistema responde 422 «Indique si el ocupante autoriza el acceso». *(RF-04-AC-4)*
6. Cuando el Vigilante registra a nombre del residente de `A-301`, la Administración ve conservados al residente reportante y al Vigilante como quien capturó. *(RF-04-AC-5)*
7. Sin residente reportante y sin nombre de referencia, el sistema responde 422 «Indique el nombre de quien reporta». *(RF-04-AC-6)*
8. El Vigilante ve únicamente los reportes que él registró. *(RF-04-AC-7)*
9. Si el inquilino de `B-502` intenta usar la captura en nombre de terceros, el sistema responde 403. *(RF-04-AC-8)*
10. Sin respuesta a la pregunta de peligro, el sistema responde 422 «Indique si el problema es peligroso o está empeorando». *(RF-04-AC-9)*
11. Las fotos y el video siguen las mismas reglas de la etapa «Alta» que en HU-03. *(RF-05-AC-1 a RF-05-AC-6)*

**Justificación de Story Points (5).** Reutiliza el formulario y las validaciones de HU-03. Agrega el medio de origen, la fecha de aviso retroactiva, el reportante con o sin cuenta y la visibilidad restringida de Vigilancia.

**Justificación de prioridad (Alta).** RF-04 está en el alcance mínimo. Sin esta historia, los avisos por WhatsApp, caseta o llamada (el medio actual) no entran al registro único (objetivo 1) y no se puede medir la adopción del tablero (RF-13-AC-6).

---

### EP-03 · Clasificación, asignación y atención

#### HU-06 · Clasificar, asignar, reclasificar o cancelar un reporte

| Campo | Valor |
|---|---|
| Épica | EP-03 · Clasificación, asignación y atención |
| RF relacionados | RF-06, RF-07 |
| RNF / RD aplicables | RNF-07, RD-01, RD-03, RD-10 |
| Story Points | 8 |
| Prioridad | Alta |

**Historia.** Como Administración, quiero confirmar o cambiar la prioridad que sugiere el sistema, clasificar la responsabilidad y asignar cada reporte a un responsable, o cancelarlo con motivo, para que cada falla tenga dueño, prioridad y quién paga desde el principio.

**Criterios de aceptación:**

1. La prioridad sugerida sale de la categoría y el subtipo (RD-01): «Iluminación / Pasillo o área techada» sugiere «Normal»; «Iluminación / Jardín o exterior», «Menor»; «Plomería y fugas / Fuga activa», «Urgente»; y cualquier reporte con peligro «Sí», «Urgente». *(RF-06-AC-5, RF-06-AC-6, RF-06-AC-7)*
2. Si la Administración cambia la sugerida «Normal» a «Urgente», el reporte conserva «Urgente» y el historial registra el cambio; el sistema nunca la revierte. *(RF-06-AC-8)*
3. Al asignar `RY-000124` en `Reportado` con prioridad «Urgente» y responsable «Conserje», pasa a `Asignado`, aparece en la lista del Conserje y el historial registra usuario, fecha y hora. *(RF-06-AC-1)*
4. Sin prioridad, la asignación se rechaza con 422 «La prioridad es obligatoria» y el estado no cambia. *(RF-06-AC-3)*
5. Con ubicación observada `A-402`, la Administración puede registrar ubicación de origen `A-502` y responsable del costo «Propietario de A-502»; el reporte se encuentra por ambas ubicaciones. *(RF-06-AC-2)*
6. Reasignar un reporte `En proceso` del Conserje a «Bombas del Norte» no cambia el estado, lo saca de la lista del Conserje y el historial muestra «Responsable: Conserje → Bombas del Norte». La reasignación del responsable solo se permite en `Asignado` o `En proceso`. *(RF-06-AC-4)*
7. Reclasificar la responsabilidad de «Por determinar» a «Privada» registra la determinación, avisa al reportante y no cambia el estado. *(RF-06-AC-9)*
8. Asignar al proveedor sin acceso «Elevadores del Centro» deja el reporte en `Asignado` sin avisar a ningún usuario de Mantenimiento. *(RF-06-AC-10)*
9. Pasar de `Reportado` a `Terminado` se rechaza con 409 «Transición no permitida». *(RF-07-AC-2)*
10. Cancelar sin motivo se rechaza con 422 «El motivo es obligatorio»; con el motivo «Falsa alarma», el reporte pasa a `Cancelado`. *(RF-07-AC-5)*
11. Un reporte `Cancelado` no admite cambios de estado (409). *(RF-07-AC-3, parte `Cancelado`; la parte `Unido` depende de RF-17, diferido)*

**Justificación de Story Points (8).** Concentra varias reglas que interactúan: la prioridad sugerida según el catálogo y la respuesta de peligro, los campos obligatorios de la asignación, la reclasificación sin cambio de estado con límites por estado, el historial con valor anterior y nuevo, y la cancelación con motivo.

**Justificación de prioridad (Alta).** Es el elemento «clasificación y asignación» del alcance mínimo, y RF-06 y RF-07 están en la sección 5, punto 15. Sin asignación, Mantenimiento no recibe trabajo.

---

#### HU-07 · Ver mis asignados, iniciar la atención y registrar avance y visita

| Campo | Valor |
|---|---|
| Épica | EP-03 · Clasificación, asignación y atención |
| RF relacionados | RF-16, RF-07, RF-15 |
| RNF / RD aplicables | RNF-01, RNF-03, RNF-05, RNF-07, RD-06 |
| Story Points | 8 |
| Prioridad | Alta |

**Historia.** Como usuario de Mantenimiento (personal propio o proveedor externo con acceso), quiero ver mis reportes asignados ordenados por prioridad y antigüedad, con su ubicación y el acceso autorizado, iniciar la atención y dejar notas y la fecha de visita, para saber qué atender primero y dejar constancia del avance sin llamar a la Administración.

**Criterios de aceptación:**

1. La lista muestra solo mis reportes en `Asignado` o `En proceso`, con folio, prioridad, categoría, ubicación observada y de origen, detalle de ubicación, autorización y horarios de acceso, fecha programada, marca de detenido con su motivo y fotos del alta. *(regla de RF-16)*
2. Un «Urgente» con aviso del 22/09/2026 aparece antes que un «Normal» con aviso del 20/09/2026. *(RF-16-AC-1)*
3. A igual prioridad, el aviso del 18/09/2026 aparece antes que el del 21/09/2026. *(RF-16-AC-3)*
4. No aparecen los reportes asignados a otro responsable ni los míos ya `Cerrado`. *(RF-16-AC-2)*
5. Si el reporte tiene autorización de acceso «No», veo «Sin autorización de acceso: coordinar con la Administración». *(RF-16-AC-4)*
6. Al pasar `RY-000124` de `Asignado` a `En proceso`, el historial muestra «Asignado → En proceso», mi nombre, y la fecha y hora. *(RF-07-AC-1)*
7. Si otro usuario de Mantenimiento intenta pasar a `En proceso` un reporte que no es suyo, el sistema responde 404. *(RF-07-AC-4)*
8. Para un proveedor sin acceso, la Administración registra el paso a `En proceso` con comentario, y el historial muestra al usuario de la Administración y al proveedor. *(RF-07-AC-10)*
9. En `Asignado` o `En proceso`, el responsable o la Administración agregan notas internas de 1 a 500 caracteres, solo de inserción; la nota «Falta la pieza; llega el jueves» queda con autor y fecha y el estado no cambia. *(RF-15-AC-1)*
10. Cuando la Administración fija la visita para el 29/09/2026 a las 10:00, el inquilino de `B-502` ve esa fecha y recibe el aviso. *(RF-15-AC-2)*

**Justificación de Story Points (8).** Junta la lista con orden de dos niveles y visibilidad por asignación, la transición a `En proceso` con registro en nombre de un proveedor sin acceso, y las notas y la fecha de visita con distinta visibilidad por rol. Son varias reglas, pero sobre datos que ya existen.

**Justificación de prioridad (Alta).** RF-07, RF-15 y RF-16 están en el alcance mínimo. Es el inicio del «seguimiento de estado»: sin esta historia el reporte asignado no avanza.

---

#### HU-08 · Marcar un reporte como detenido y reanudarlo

| Campo | Valor |
|---|---|
| Épica | EP-03 · Clasificación, asignación y atención |
| RF relacionados | RF-18 |
| RNF / RD aplicables | RNF-07, EX-12 |
| Story Points | 3 |
| Prioridad | Media |

**Historia.** Como responsable asignado o Administración, quiero marcar como detenido un reporte con el motivo de la espera y reanudarlo cuando se destrabe, para que el residente sepa por qué no avanza y el tiempo de espera no se confunda con el de atención.

**Criterios de aceptación:**

1. Un reporte `Asignado` o `En proceso` se marca detenido con un motivo del catálogo («Acceso al departamento», «Espera de proveedor», «Espera de pieza», «Espera de autorización de gasto», «Otro» con texto). Detener no cambia el estado. *(regla de RF-18)*
2. Al marcar `RY-000124` (`En proceso`) detenido con «Espera de pieza», queda detenido con ese motivo, sigue `En proceso` y el historial registra fecha, hora y usuario. *(RF-18-AC-1)*
3. Sin motivo, el sistema responde 422 «Indique el motivo de la detención». *(RF-18-AC-2)*
4. El Conserje o la Administración lo reanudan; deja de estar detenido y el historial registra la reanudación. *(RF-18-AC-3)*
5. Un reporte `Terminado` no se puede marcar detenido: 409 «Transición no permitida». *(RF-18-AC-4)*
6. Al marcarlo detenido, el residente reportante recibe el aviso. *(RF-18-AC-5)*
7. «Espera de autorización de gasto» es solo un motivo; el sistema no gestiona cotizaciones ni autorizaciones. *(EX-12)*

**Justificación de Story Points (3).** Es una marca sobre el reporte, no un estado nuevo, con un catálogo fijo y dos acciones. Reutiliza el historial y los avisos ya construidos.

**Justificación de prioridad (Media).** RF-18 pertenece formalmente a la segunda fase (sección 5, punto 15). Se coloca arriba de la segunda fase porque criterios del alcance mínimo dependen parcialmente de la marca de detenido: el campo «marca de detenido» de la lista de RF-16 (HU-07), RF-10-AC-6 (HU-10) y RF-13-AC-5 (HU-15).

---

### EP-04 · Seguimiento y cierre con evidencia

#### HU-09 · Marcar un reporte como terminado con evidencia

| Campo | Valor |
|---|---|
| Épica | EP-04 · Seguimiento y cierre con evidencia |
| RF relacionados | RF-08, RF-05, RF-07 |
| RNF / RD aplicables | RNF-02, RNF-04, RNF-07, RD-04, RD-09 |
| Story Points | 5 |
| Prioridad | Alta |

**Historia.** Como usuario de Mantenimiento, quiero marcar como terminado un reporte adjuntando fotos del trabajo, sin estar obligado a escribir, para dejar evidencia de lo que hice y que la Administración la revise antes de cerrar.

**Criterios de aceptación:**

1. Solo el Mantenimiento asignado o la Administración pasan un reporte de `En proceso` a `Terminado`. Registrar `Terminado` nunca cierra el reporte. *(regla de RF-07 y RF-08)*
2. Con una foto y sin nota, `RY-000124` pasa a `Terminado` y la foto queda en la etapa «Evidencia», separada de las del alta. La nota es opcional, de hasta 1,000 caracteres. *(RF-08-AC-1)*
3. Sin fotografías, el sistema responde 422 «Adjunte al menos una foto del trabajo terminado» y el reporte sigue `En proceso`. *(RF-08-AC-2)*
4. Se aceptan de 1 a 5 fotos de evidencia por ciclo: un reporte reabierto con 5 fotos del primer ciclo acepta 2 nuevas, y el detalle muestra las evidencias agrupadas por ciclo. *(RF-08-AC-3)*
5. Para un proveedor sin acceso, la Administración puede marcar `Terminado` sin fotos con una justificación; el reporte queda marcado «Terminado sin evidencia fotográfica». Sin justificación, el sistema responde 422 «Escriba la justificación». *(RF-08-AC-4, RF-08-AC-5)*
6. La excepción no aplica al personal propio: sin fotos, aun con justificación, el sistema responde 422 «Adjunte al menos una foto del trabajo terminado». *(RF-08-AC-6)*
7. Si se atendió solo lo urgente, la descripción de lo pendiente queda en el historial y el reporte queda `Terminado`, sin cerrarse. *(RF-08-AC-7)*
8. Restricción: el personal de mantenimiento termina un reporte en un máximo de 3 pantallas o pasos. *(RNF-02)*

**Justificación de Story Points (5).** Reutiliza la carga de archivos de HU-03 en la etapa «Evidencia». Agrega el control por ciclo, la excepción para proveedores sin acceso con marca de auditoría y la atención parcial.

**Justificación de prioridad (Alta).** RF-05, RF-07 y RF-08 están en el alcance mínimo y forman la parte «con evidencia» del «cierre con evidencia». Cumple el objetivo medible 4 (cada terminado tiene evidencia).

---

#### HU-10 · Consultar el estado de mis reportes y cancelar uno ya resuelto

| Campo | Valor |
|---|---|
| Épica | EP-04 · Seguimiento y cierre con evidencia |
| RF relacionados | RF-10, RF-15, RF-07 |
| RNF / RD aplicables | RNF-03, RNF-05, RD-07, RD-08 |
| Story Points | 5 |
| Prioridad | Alta |

**Historia.** Como Residente, quiero consultar el estado, las fechas y la visita programada de mis reportes y de los de áreas comunes, y cancelar uno que ya se resolvió solo, para no tener que preguntar a la Administración y no dejar abierto algo que ya no hace falta atender.

**Criterios de aceptación:**

1. Veo los reportes de mi unidad con fecha de aviso igual o posterior a mi fecha de vinculación, los que yo reporté y todos los de áreas comunes, cada uno con folio, categoría, estado actual, fecha programada de visita y fecha de cada cambio de estado. Si reporté 2 en mi unidad y otros reportaron 3 de áreas comunes, recibo esos 5. *(RF-10-AC-1)*
2. Si pido por folio un reporte de `A-301`, el sistema responde 404. *(RF-10-AC-2)*
3. En un reporte de área común hecho por otro residente, veo categoría, descripción, estado y fechas, pero no el nombre ni la unidad de quien reportó. *(RF-10-AC-3)*
4. No veo un reporte de mi unidad hecho por un inquilino anterior antes de mi fecha de vinculación. *(RF-10-AC-4)*
5. Si mi reporte está detenido con «Espera de pieza», veo que está detenido y el motivo. *(RF-10-AC-6; requiere HU-08)*
6. Si mi reporte fue unido a `RY-000150`, veo «Unido a RY-000150» y el estado del principal. *(RF-10-AC-5; se verifica cuando se implemente RF-17, diferido a segunda fase)*
7. No veo las notas de avance internas. *(RF-15-AC-3)*
8. No veo el nombre ni el correo del propietario de mi unidad. *(RF-24-AC-3, se cumple de forma transversal; ver sección 8)*
9. Puedo cancelar un reporte que registré en `Reportado` o `Asignado` con el motivo «Ya se resolvió»: pasa a `Cancelado`, el historial guarda motivo y usuario, y se avisa a la Administración y al responsable. *(RF-07-AC-6)*
10. Si está `En proceso`, la cancelación se rechaza con 409 «Transición no permitida». *(RF-07-AC-7)*
11. Si intento cancelar un reporte de otro residente, el sistema responde 404. *(RF-07-AC-8)*
12. Con un motivo distinto de «Ya se resolvió», el sistema responde 422 «Solo puede cancelar un reporte que ya se resolvió». *(RF-07-AC-9)*

**Justificación de Story Points (5).** La consulta aplica reglas de visibilidad finas: fecha de vinculación, anonimato en áreas comunes y ocultamiento de notas y datos confidenciales. La cancelación agrega una transición con motivo fijo. No hay cálculos.

**Justificación de prioridad (Alta).** RF-07, RF-10 y RF-15 están en el alcance mínimo. Es la parte visible del «seguimiento de estado» para el residente y cumple el objetivo medible 2 (consultar el estado y la visita sin preguntar).

---

#### HU-11 · Recibir avisos de mis reportes

| Campo | Valor |
|---|---|
| Épica | EP-04 · Seguimiento y cierre con evidencia |
| RF relacionados | RF-11 |
| RNF / RD aplicables | RNF-07, RNF-10, RD-05, EX-06, EX-08, EX-10 |
| Story Points | 8 |
| Prioridad | Alta |

**Historia.** Como residente reportante, quiero recibir un correo y un aviso en el sistema cuando mi reporte cambia en los momentos que me importan, para enterarme sin tener que preguntar y sin recibir avisos de más.

**Criterios de aceptación:**

1. Al registrar un reporte, recibo un aviso en el sistema y un correo con el folio y la fecha de aviso, y la Administración recibe el aviso de reporte nuevo. *(RF-11-AC-1)*
2. Al pasar a `Asignado` un reporte de `B-502` cuyo propietario no vive en el condominio, el inquilino recibe aviso y correo; el propietario recibe solo un correo con el folio, el estado nuevo, la fecha y el responsable del costo. *(RF-11-AC-2)*
3. En un reporte de área común solo se avisa al residente que lo reportó; no se envía correo a ningún propietario. *(RF-11-AC-3)*
4. Si el servicio de correo no responde, el cambio se guarda y el aviso en el sistema se crea; tras 3 intentos con 10 minutos entre ellos, el correo aparece como «Fallido» para la Administración. *(RF-11-AC-4)*
5. Al asignar `RY-000124` al Conserje, este recibe un aviso y un correo con el folio y la prioridad. *(RF-11-AC-5)*
6. Si el inquilino cancela con «Ya se resolvió», el Conserje y la Administración reciben aviso y correo con el folio y el motivo. *(RF-11-AC-6)*
7. El paso a `En proceso` no genera ningún aviso al residente (tampoco las notas internas). *(RF-11-AC-7)*
8. Si el reportante es «Sin cuenta», al pasar a `Asignado` la Administración recibe un aviso para comunicarlo manualmente. *(RF-11-AC-8)*
9. El correo de `Terminado` informa que puedo responder «Ya quedó» o «Sigue fallando» hasta el vencimiento del plazo. *(RF-11-AC-9)*
10. Cada envío deja constancia (canal, fecha y hora) en el historial del reporte. *(regla de RF-11)*
11. Los eventos de RF-11 que dependen de funciones diferidas (unión de RF-17, reapertura de un cerrado de RF-19 y estancamiento de RF-22) se activan cuando esas funciones se implementen. *(nota de trazabilidad)*

**Justificación de Story Points (8).** Hay una tabla de eventos con destinatarios distintos (residente, propietario sin cuenta, Mantenimiento, Administración), dos canales, reintentos con reloj controlable, estado «Fallido» y la regla de no avisar en ciertos cambios. Depende de un servicio externo de correo.

**Justificación de prioridad (Alta).** RF-11 está en el alcance mínimo. Los avisos hacen que el «seguimiento de estado» llegue al residente y al propietario no residente (RD-05) sin crearles cuenta (EX-08).

---

#### HU-12 · Cerrar o reabrir según la confirmación del residente

| Campo | Valor |
|---|---|
| Épica | EP-04 · Seguimiento y cierre con evidencia |
| RF relacionados | RF-09, RF-07 |
| RNF / RD aplicables | RNF-07, RNF-10, RD-04 |
| Story Points | 8 |
| Prioridad | Alta |

**Historia.** Como Administración, quiero cerrar un reporte terminado solo cuando el residente confirmó, venció su plazo o no hay residente que confirme, y reabrirlo si sigue fallando, para que ningún reporte se dé por resuelto sin revisión y el residente tenga voz sobre la solución.

**Criterios de aceptación:**

1. Cuando el reporte pasa a `Terminado`, el residente reportante puede responder una vez por ciclo «Ya quedó» o «Sigue fallando» (con comentario obligatorio) dentro de 72 horas. El plazo se reinicia cada vez que vuelve a `Terminado` y es configurable (RF-27). *(regla de RF-09)*
2. Si pasó a `Terminado` el 22/09/2026 a las 10:00 y el inquilino responde «Ya quedó» a las 18:00, la respuesta se registra y la Administración puede cerrar. *(RF-09-AC-1)*
3. Sin respuesta, un intento de cierre el 22/09/2026 a las 20:00 se rechaza con 409 «Esperando confirmación del residente hasta el 25/09/2026 10:00». *(RF-09-AC-2)*
4. Una respuesta el 25/09/2026 a las 10:01 se rechaza con 409 «El plazo para responder terminó». *(RF-09-AC-3)*
5. Si respondió «Sigue fallando», cerrar sin comentario se rechaza con 422 «Escriba el motivo del cierre». *(RF-09-AC-4)*
6. Si respondió «Sigue fallando», la Administración puede reabrir con comentario: pasa a `En proceso` con el mismo folio, inicia un ciclo nuevo y conserva la respuesta en el historial. *(RF-09-AC-5; transición `Terminado → En proceso` de RF-07)*
7. Un reporte de área común se puede cerrar aunque haya pasado a `Terminado` hace 1 hora. *(RF-09-AC-6)*
8. Un reporte con reportante «Sin cuenta» se puede cerrar porque no hay residente que confirme. *(RF-09-AC-9)*
9. Si el Conserje o el inquilino intentan cerrar, el sistema responde 403 y el reporte sigue `Terminado`. Solo la Administración cierra. *(RF-09-AC-7, RF-09-AC-8; RD-04)*

**Justificación de Story Points (8).** Tiene un plazo dependiente del reloj que se reinicia por ciclo, cuatro condiciones alternativas de cierre, una respuesta única por ciclo y la reapertura con ciclo nuevo. Hay muchos casos de borde de tiempo que probar con RNF-10.

**Justificación de prioridad (Alta).** RF-07 y RF-09 están en el alcance mínimo. Completa el «cierre con evidencia» con la regla del equipo de que Mantenimiento termina y solo la Administración cierra (C-01).

---

### EP-05 · Historial, tablero y parámetros

#### HU-13 · Ajustar objetivos, plazos y umbrales

| Campo | Valor |
|---|---|
| Épica | EP-05 · Historial, tablero y parámetros |
| RF relacionados | RF-27 |
| RNF / RD aplicables | RNF-07, RD-02, RD-10 |
| Story Points | 3 |
| Prioridad | Alta |

**Historia.** Como Administrador, quiero consultar y modificar los objetivos de tiempo, los plazos y los umbrales del sistema, para ajustarlos a la realidad del condominio sin pedir un cambio de software.

**Criterios de aceptación:**

1. Se pueden consultar y modificar los parámetros con estos valores iniciales: objetivo de primera atención «Urgente» 1 h; resolución «Urgente» 24 h, «Normal» 72 h y «Menor» 168 h; umbral de estancamiento 2 h / 24 h / 72 h; plazo de confirmación del residente 72 h; plazo para reabrir un cerrado 30 días; ventana y mínimo de recurrencia 90 días y 3 reportes. *(regla de RF-27)*
2. Si el objetivo de resolución «Urgente» cambia de 24 a 12 horas, el tablero usa 12 horas en las consultas posteriores y el cambio queda registrado con valor anterior, nuevo, usuario y fecha. *(RF-27-AC-1)*
3. Un valor de tiempo menor o igual a cero se rechaza con 422 «El valor debe ser mayor que cero» y se conserva el vigente. *(RF-27-AC-2)*
4. Si la Auxiliar intenta modificar un parámetro, el sistema responde 403. *(RF-27-AC-3)*
5. Si el plazo de confirmación cambia a 96 horas, el plazo del ciclo de un reporte que pasa a `Terminado` después es de 96 horas. *(RF-27-AC-4)*
6. Los umbrales de estancamiento y el plazo de reapertura de un cerrado se pueden configurar, pero solo tienen efecto cuando se implementen RF-22 y RF-19 (segunda fase). *(nota de trazabilidad)*

**Justificación de Story Points (3).** Es un conjunto fijo de parámetros con validación de valor positivo, permiso exclusivo del Administrador y registro del cambio. El trabajo de usarlos está en las historias que los consumen.

**Justificación de prioridad (Alta).** RF-27 está en el alcance mínimo de la sección 5, punto 15. El tablero y el cierre lo necesitan porque sus objetivos y plazos no son constantes (C-06).

---

#### HU-14 · Buscar reportes y consultar su historial completo

| Campo | Valor |
|---|---|
| Épica | EP-05 · Historial, tablero y parámetros |
| RF relacionados | RF-12 |
| RNF / RD aplicables | RNF-03, RNF-05, RNF-07 |
| Story Points | 5 |
| Prioridad | Alta |

**Historia.** Como Administración, quiero buscar reportes combinando ubicación, categoría, estado, prioridad, responsable, medio de origen, rango de fechas y texto, y ver el detalle completo con fotos e historial, para responder con evidencia a los residentes y al comité.

**Criterios de aceptación:**

1. Los filtros se combinan libremente y los resultados se ordenan por fecha de aviso, de la más reciente a la más antigua. *(regla de RF-12)*
2. Con 4 reportes de «Bombas y cisterna» (15/12/2025, 01/01/2026, 30/06/2026 23:30 y 01/07/2026), el filtro del 01/01/2026 al 30/06/2026 devuelve exactamente 2: el del 30/06/2026 primero y el del 01/01/2026 después. El rango es inclusivo por días completos. *(RF-12-AC-1)*
3. Un reporte con ubicación observada `A-402` y de origen `A-502` aparece al buscar `A-502`. *(RF-12-AC-2)*
4. El detalle de un reporte cerrado con una reapertura muestra las fotos del alta y las de evidencia separadas por ciclo, y cada cambio de estado con usuario, fecha, hora y comentario. *(RF-12-AC-3)*
5. Buscar «gotera» devuelve todos los reportes que lo contienen y ninguno que no. *(RF-12-AC-4)*
6. Si un Residente intenta usar la búsqueda, el sistema responde 403. *(RF-12-AC-5)*
7. El detalle incluye qué pasó, dónde, cuándo, qué se hizo, quién lo hizo, fotos por etapa y ciclo, notas de avance e historial completo. El costo y el pagador se muestran cuando se implemente RF-20 (segunda fase). *(regla de RF-12)*

**Justificación de Story Points (5).** Incluye una búsqueda con ocho filtros combinables, búsqueda de texto y un detalle que reúne datos de varias historias. No tiene reglas de negocio nuevas, pero sí exige el rendimiento de RNF-03.

**Justificación de prioridad (Alta).** RF-12 está en el alcance mínimo. Da a la Administración la evidencia con fechas que hoy no tiene (problema descrito en 1.2).

---

#### HU-15 · Consultar el tablero de tiempos, incidencias recurrentes y adopción

| Campo | Valor |
|---|---|
| Épica | EP-05 · Historial, tablero y parámetros |
| RF relacionados | RF-13 |
| RNF / RD aplicables | RNF-03, RNF-10, RNF-16, RD-02, RD-14 |
| Story Points | 13 |
| Prioridad | Alta |

**Historia.** Como Administración, quiero consultar para un periodo los reportes por estado y categoría, los tiempos promedio y el cumplimiento por prioridad, las incidencias recurrentes, el tiempo detenido y la adopción, para medir el servicio contra los objetivos y detectar las fallas que se repiten.

**Criterios de aceptación:**

1. Para el rango de fechas de aviso elegido, el tablero muestra: reportes por estado y por categoría; tiempo promedio de primera atención y de resolución por prioridad; cumplimiento por prioridad para cada objetivo de RD-02, en dos bloques (personal propio y proveedores externos); incidencias recurrentes; tiempo detenido por reporte con sus motivos; y adopción. *(regla de RF-13)*
2. Los reportes `Cancelado` y `Unido` no cuentan en promedios, cumplimiento, recurrencia ni adopción; los porcentajes se redondean al entero; las reaperturas se muestran como dato aparte y no crean un reporte nuevo. *(regla de RF-13; RD-14)*
3. Con 3 reportes «Urgente» de personal propio en septiembre de 2026 (primera atención 30, 50 y 130 min; resolución 10, 20 y 36 h), el tablero muestra primera atención promedio de 70 min con 67 % de cumplimiento y resolución promedio de 22 h con 67 % de cumplimiento. *(RF-13-AC-1)*
4. Con fecha de consulta 03/10/2026 y 3 reportes de «Iluminación» en «Rampa del estacionamiento» (15/07, 15/08 y 20/09/2026), aparece «Iluminación — Rampa del estacionamiento» como incidencia recurrente con los 3 folios. *(RF-13-AC-2)*
5. Si uno de los 3 reportes está `Cancelado`, la combinación no aparece como recurrente. *(RF-13-AC-3)*
6. Un reporte «Normal» con aviso del 20/09/2026 10:00, sin `Terminado` a las 11:00 del 23/09/2026, cuenta como incumplido porque su objetivo de 72 horas venció el 23/09/2026 10:00. *(RF-13-AC-4)*
7. Un reporte detenido del 10/09/2026 09:00 al 12/09/2026 09:00 por «Espera de pieza» muestra 48 horas de tiempo detenido, por separado, con el motivo. *(RF-13-AC-5; requiere HU-08)*
8. Con 10 reportes en octubre de 2026, 6 con medio «Sistema» y 4 por WhatsApp, la adopción es 60 %. *(RF-13-AC-6)*
9. Los reportes asignados a «Bombas del Norte» aparecen en el bloque de proveedores externos y no en el de personal propio. *(RF-13-AC-7)*
10. Si un Residente solicita el tablero, el sistema responde 403. *(RF-13-AC-8)*
11. Restricción: las cifras coinciden con los registros de los que se calculan, y la consulta responde en 2 segundos o menos (percentil 95) con 5,000 reportes. *(RNF-16, RNF-03)*

**Justificación de Story Points (13).** Es la historia más compleja: seis indicadores, dos bloques de cumplimiento, reglas de cumplido, incumplido o fuera de cálculo según el vencimiento del objetivo, recurrencia con ventana deslizante y exclusiones, y tiempo detenido. Depende del reloj controlable y de los parámetros. Está en el máximo de la escala; dividirla separaría indicadores que la Administración consulta juntos.

**Justificación de prioridad (Alta).** RF-13 está en el alcance mínimo y es el elemento «tablero de tiempos e incidencias recurrentes». Cumple los objetivos medibles 3 y 5 del SRS (tiempo contra objetivo y adopción).

---

#### HU-05 · Exportar el tablero a un archivo imprimible

| Campo | Valor |
|---|---|
| Épica | EP-05 · Historial, tablero y parámetros |
| RF relacionados | RF-23 |
| RNF / RD aplicables | RNF-16, S-07 |
| Story Points | 3 |
| Prioridad | Media |

**Historia.** Como miembro de la Administración, quiero exportar el tablero de un periodo a un archivo imprimible, para presentar las métricas del condominio al comité o a la asamblea.

**Criterios de aceptación:**

1. Después de consultar el tablero del 01/09/2026 al 30/09/2026, al exportarlo el sistema genera un PDF con el periodo, el tiempo promedio de atención por prioridad, el cumplimiento y las incidencias recurrentes. El PDF incluye también la adopción. *(RF-23-AC-1; regla de RF-23)*
2. Si el tablero de septiembre muestra una resolución promedio «Urgente» de 22 horas, el PDF muestra las mismas cifras que la pantalla. *(RF-23-AC-2; RNF-16)*
3. Si un Residente solicita la exportación, el sistema responde 403. *(RF-23-AC-3)*

**Justificación de Story Points (3).** Reutiliza los cálculos de HU-15; solo agrega generar el PDF y el control de acceso. El riesgo principal (que las cifras coincidan) lo cubre usar el mismo cálculo.

**Justificación de prioridad (Media).** RF-23 pertenece formalmente a la segunda fase (sección 5, punto 15). Aporta valor de negocio porque permite presentar las métricas al comité y a la asamblea, y apoya el supuesto S-07 (el comité aprueba el gasto si se le presentan métricas). Depende de HU-15.

---

## 8. Trazabilidad

### 8.1 RF cubiertos por las 15 historias

| RF | Historias | Fase según la sección 5, punto 15 |
|---|---|---|
| RF-01 | HU-02 | Alcance mínimo |
| RF-02 | HU-01 | Alcance mínimo |
| RF-03 | HU-03 | Alcance mínimo |
| RF-04 | HU-04 | Alcance mínimo |
| RF-05 | HU-03, HU-04, HU-09 | Alcance mínimo |
| RF-06 | HU-06 | Alcance mínimo |
| RF-07 | HU-06, HU-07, HU-09, HU-10, HU-12 | Alcance mínimo |
| RF-08 | HU-09 | Alcance mínimo |
| RF-09 | HU-12 | Alcance mínimo |
| RF-10 | HU-10 | Alcance mínimo |
| RF-11 | HU-11 | Alcance mínimo |
| RF-12 | HU-14 | Alcance mínimo |
| RF-13 | HU-15 | Alcance mínimo |
| RF-14 | HU-02 | Alcance mínimo |
| RF-15 | HU-07, HU-10 | Alcance mínimo |
| RF-16 | HU-07 | Alcance mínimo |
| RF-27 | HU-13 | Alcance mínimo |
| RF-18 | HU-08 | Segunda fase (prioridad Media) |
| RF-23 | HU-05 | Segunda fase (prioridad Media) |

Los 17 RF del alcance mínimo (RF-01 a RF-16 y RF-27) tienen historia, todas con prioridad Alta. Se cubren 19 de los 27 RF.

**Reparto de los criterios de RF-07** (RF transversal): RF-07-AC-2, AC-3 y AC-5 en HU-06; RF-07-AC-1, AC-4 y AC-10 en HU-07; la transición `En proceso → Terminado` en HU-09; RF-07-AC-6 a AC-9 en HU-10; y la reapertura `Terminado → En proceso` en HU-12.

**Reparto de los criterios de RF-05** (RF transversal): RF-05-AC-1 a AC-7 en HU-03 (etapa «Alta») y en HU-04; la etapa «Evidencia» en HU-09.

### 8.2 RF diferidos a segunda fase (sin historia en este backlog)

| RF | Función | Observación |
|---|---|---|
| RF-17 | Detección y unión de reportes duplicados | Se difiere explícitamente a segunda fase. Mientras tanto, la Administración puede cancelar un duplicado con motivo (RF-07-AC-5). RF-10-AC-5 y la parte `Unido` de RF-07-AC-3 se verifican cuando se implemente. |
| RF-19 | El problema persiste y reapertura de un cerrado | La transición `Cerrado → En proceso` de RF-07 queda pendiente; la reapertura desde `Terminado` sí está en HU-12. |
| RF-20 | Costo y pagador | El «responsable del costo» de RF-06 (RD-03) sí está en HU-06; el monto y el pagador quedan pendientes. |
| RF-21 | Delegación temporal a la Auxiliar | Sin delegación, la Auxiliar no asigna, reclasifica ni cierra (RF-21-AC-2). En el alcance mínimo solo el Administrador gestiona. |
| RF-22 | Alerta de reporte estancado | Sus umbrales ya se configuran en HU-13. |
| RF-25 | Reparación con garantía | Afecta la retención de fotos de RNF-13. |
| RF-26 | Corrección del reporte por el residente | Mientras tanto, solo la Administración modifica los datos del reporte. |

### 8.3 RF sin historia independiente pero cubiertos transversalmente

| RF | Dónde se cubre | Alcance de la cobertura |
|---|---|---|
| RF-24 · Identificación del propietario | HU-03 (RF-24-AC-1: no se piden datos del propietario al inquilino) y HU-10 (RF-24-AC-3: el inquilino no ve los datos del propietario) | **Parcial.** Esos dos criterios ya los exigen la matriz de visibilidad 2.3 y RNF-05, que están en el alcance mínimo. RF-24-AC-2 (la Administración ve el nombre y el correo del propietario en el reporte) queda diferido con el resto de la segunda fase. |

RF-05, RF-07 y RF-15 tampoco tienen una historia propia, pero están en la tabla 8.1 porque sus criterios se reparten completos entre varias historias.

### 8.4 Requerimientos no funcionales

Los RNF no son historias: se aplican como restricciones en los criterios de las historias indicadas en la columna «RNF / RD aplicables». **RNF-11** (tolerancia a mala conectividad) no se asignó a ninguna historia. La sección 5, punto 15 difiere su «modalidad completa» a segunda fase sin definir una modalidad parcial para el alcance mínimo; el equipo debe decidirla en diseño, junto con la elección del frontend (sección 4 del SRS, C-17).

### 8.5 Verificación contra las exclusiones

Las 15 historias se revisaron contra EX-01 a EX-14 y ninguna las contradice. No hay cobros ni análisis de gasto (EX-01, EX-02), ni mantenimiento preventivo (EX-03), ni control de acceso en caseta (EX-04; Vigilancia solo captura en HU-04), ni aplicación nativa (EX-05), ni integración con WhatsApp (EX-06; HU-04 captura manualmente), ni multi-condominio (EX-07). Toda cuenta la crea la Administración y el propietario no residente solo recibe correo (EX-08; HU-01, HU-11). La fecha de visita no se valida contra horarios (EX-09; HU-07), las notas no son chat (EX-10), «Urgente» no sustituye el canal de emergencias (EX-11), el gasto solo aparece como motivo de detención (EX-12; HU-08), la autorización de acceso la da solo el reportante (EX-13) y el contexto es un condominio (EX-14).
