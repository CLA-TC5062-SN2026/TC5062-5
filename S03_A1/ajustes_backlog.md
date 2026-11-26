# Historias de usuario — ReportaYa

| Campo | Valor |
|---|---|
| Fuente | `SRS_equipo.md` (v2.0), 27 RF y 161 criterios de aceptación |
| Fecha | 3 de octubre de 2026 |
| Contenido | 44 historias agrupadas en 5 épicas |
| Estimación | Story Points con escala Fibonacci (1, 2, 3, 5, 8, 13). Son estimaciones **iniciales y relativas**, sin calibrar con la velocidad del equipo |

## Cómo leer este documento

- **Criterios de aceptación:** cada uno cita su ID `RF-XX-AC-Y` de `SRS_equipo.md`, de modo que cada historia y cada prueba se rastrea hasta el SRS. Los criterios marcados *(propuesto)* no existen en el SRS; los agregué porque la historia necesitaba un segundo criterio verificable o porque el requisito (un RNF) no tiene criterios Dado–Cuando–Entonces. Conviene incorporarlos al SRS si se aceptan.
- **Prioridad:** **Alta** = pertenece al alcance mínimo de 12 semanas (RF-01 a RF-16 y RF-27, según la sección 5, punto 15 del SRS). **Media** = segunda fase con valor operativo claro. **Baja** = segunda fase, mejora que no bloquea la operación.
- **Story Points:** una historia de 13 es candidata a dividirse antes de entrar a un sprint.
- **Personas:** Residente (propietario residente o inquilino), Administración (Administrador y Auxiliar), Personal de mantenimiento (propio o proveedor con cuenta), Vigilancia.

## Resumen por épica

| Épica | Historias | Story Points | Alta | Media | Baja |
|---|---|---|---|---|---|
| E1. Acceso y administración del sistema | 9 | 31 | 24 | 7 | 0 |
| E2. Registro de incidencias | 10 | 52 | 26 | 23 | 3 |
| E3. Gestión y atención del reporte | 12 | 45 | 37 | 6 | 2 |
| E4. Cierre y comunicación con el residente | 7 | 33 | 25 | 8 | 0 |
| E5. Historial, métricas e informes | 6 | 25 | 19 | 6 | 0 |
| **Total** | **44** | **186** | **131** | **50** | **5** |

*(Los puntos de las columnas Alta, Media y Baja suman los Story Points de cada prioridad.)*

---

## E1. Acceso y administración del sistema

### HU-01 · Iniciar sesión según mi rol
**Como** usuario con cuenta activa, **quiero** iniciar sesión con mi correo y contraseña, **para** acceder solo a las funciones que corresponden a mi rol.

**Prioridad:** Alta · **Story Points:** 3 · **RF:** RF-01

**Criterios de aceptación**
- **RF-01-AC-1:** Dado un residente activo con contraseña válida, cuando inicia sesión, entonces recibe una sesión con rol Residente y su unidad `B-502`.
- **RF-01-AC-2:** Dada una contraseña incorrecta, cuando intenta entrar, entonces recibe 401 «Correo o contraseña incorrectos» sin saber cuál falló.
- **RF-01-AC-3:** Dado un inquilino con sesión, cuando intenta asignar un reporte, entonces recibe 403 y el reporte no cambia.
- **RF-01-AC-4:** Dado el Vigilante con sesión, cuando intenta cerrar o asignar un reporte, entonces recibe 403.

### HU-02 · Mantener el padrón de unidades y áreas comunes
**Como** Administración, **quiero** dar de alta y editar unidades (torre, piso, número y propietario) y áreas comunes, **para** saber a qué unidad y a qué propietario corresponde cada reporte.

**Prioridad:** Alta · **Story Points:** 3 · **RF:** RF-02

**Criterios de aceptación**
- **RF-02-AC-5:** Dada el alta de la unidad `C-101`, cuando se omite el correo del propietario, entonces el sistema responde 422 «El correo del propietario es obligatorio».
- **RF-02-AC-6:** Dada el alta de la unidad `C-102`, cuando se omite el piso, entonces el sistema responde 422 «El piso es obligatorio».

### HU-03 · Dar de alta y desactivar usuarios
**Como** Administración, **quiero** crear cuentas de residentes, mantenimiento y vigilancia y desactivarlas, **para** controlar quién usa el sistema sin permitir el autoregistro.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-02

**Criterios de aceptación**
- **RF-02-AC-1:** Dado que existe la unidad `B-502`, cuando se da de alta a un inquilino vinculado a ella, entonces queda «Pendiente de activación» y se envía el enlace de activación.
- **RF-02-AC-2:** Dado un correo ya registrado, cuando se da de alta otro usuario con ese correo, entonces el sistema responde 422 «El correo ya está registrado».
- **RF-02-AC-3:** Dado un inquilino desactivado, cuando intenta iniciar sesión, entonces recibe 401 y sus reportes anteriores siguen visibles para la Administración.
- **RF-02-AC-8:** Dada el alta de un usuario con rol Vigilancia, cuando se activa, entonces solo ve las funciones de captura en nombre de terceros.

### HU-04 · Registrar proveedores externos con o sin acceso
**Como** Administración, **quiero** registrar proveedores externos, con cuenta o como simple contacto, **para** poder asignarles reportes aunque no usen el sistema.

**Prioridad:** Alta · **Story Points:** 3 · **RF:** RF-02

**Criterios de aceptación**
- **RF-02-AC-4:** Dado el alta de «Bombas del Norte» con tipo «Proveedor externo», especialidad y teléfono, cuando se guarda, entonces queda «Pendiente de activación», recibe el enlace y aparece en la lista de responsables.
- **RF-02-AC-7:** Dado el alta de «Elevadores del Centro» como proveedor sin acceso, cuando se guarda, entonces no se crea cuenta ni enlace y aparece en la lista marcado «Sin acceso al sistema».

### HU-05 · Activar mi cuenta y recuperar mi contraseña
**Como** usuario del sistema, **quiero** activar mi cuenta desde el enlace que recibo y recuperar mi contraseña si la olvido, **para** entrar sin depender de la Administración.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-14

**Criterios de aceptación**
- **RF-14-AC-1:** Dado un enlace de activación abierto dentro de las 72 horas, cuando defino una contraseña válida, entonces mi cuenta pasa a «Activa» y el enlace deja de funcionar.
- **RF-14-AC-2:** Dado un enlace emitido el 20/09/2026 10:00, cuando se usa el 23/09/2026 10:01, entonces el sistema responde 422 «El enlace venció; pida uno nuevo a la Administración».
- **RF-14-AC-3:** Dada una solicitud de recuperación, cuando se pide con un correo existente o inexistente, entonces la respuesta es la misma y el enlace válido vence en 1 hora.

### HU-06 · Crear la primera cuenta de Administración
**Como** responsable del despliegue, **quiero** crear la primera cuenta de Administración con un comando de arranque, **para** poder empezar a operar el sistema sin un usuario previo.

**Prioridad:** Alta · **Story Points:** 2 · **RF:** RF-14

**Criterios de aceptación**
- **RF-14-AC-4:** Dada una base de datos sin usuarios, cuando se ejecuta el comando con un correo de Administración, entonces se crea ese usuario con rol Administración y se le envía el enlace de activación.
- *(propuesto)* Dado que ya existe al menos un usuario, cuando se ejecuta el comando de arranque, entonces no se crea otro usuario de Administración.

### HU-07 · Identificar al propietario de la unidad
**Como** Administración, **quiero** ver quién es el propietario de la unidad de un reporte sin pedírselo al inquilino, **para** saber a quién corresponde el costo y a quién avisar.

**Prioridad:** Media · **Story Points:** 2 · **RF:** RF-24

**Criterios de aceptación**
- **RF-24-AC-1:** Dado un inquilino que reporta en su unidad, cuando envía el reporte, entonces el sistema no le pide datos del propietario.
- **RF-24-AC-2:** Dado un reporte de un inquilino de `B-502`, cuando la Administración lo consulta, entonces ve nombre y correo del propietario.
- **RF-24-AC-3:** Dado el mismo reporte, cuando el inquilino lo consulta, entonces la respuesta no incluye datos del propietario.

### HU-08 · Delegar mis funciones a la auxiliar mientras estoy ausente
**Como** Administrador, **quiero** habilitar temporalmente a la Auxiliar para asignar, reclasificar y cerrar, **para** que la operación no se detenga cuando no estoy.

**Prioridad:** Media · **Story Points:** 5 · **RF:** RF-21

**Criterios de aceptación**
- **RF-21-AC-1:** Dada la delegación habilitada, cuando la Auxiliar asigna un reporte o cierra uno terminado, entonces el sistema registra la acción.
- **RF-21-AC-2:** Dada la delegación deshabilitada, cuando la Auxiliar intenta asignar o cerrar, entonces recibe 403.
- **RF-21-AC-3:** Dada una delegación habilitada, cuando el Administrador la deshabilita, entonces la Auxiliar ya no puede asignar, reclasificar ni cerrar.
- **RF-21-AC-4:** Dada la delegación habilitada, cuando la Auxiliar actúa, entonces el historial lo registra a nombre de la Auxiliar.
- **RF-21-AC-5:** Dada una delegación con fecha de fin 05/10/2026 23:59, cuando la Auxiliar intenta asignar el 06/10/2026 08:00, entonces recibe 403.

### HU-09 · Ajustar los plazos y umbrales del sistema
**Como** Administrador, **quiero** cambiar los tiempos objetivo, umbrales y plazos desde el sistema, **para** corregirlos sin pedir un nuevo despliegue.

**Prioridad:** Alta · **Story Points:** 3 · **RF:** RF-27

**Criterios de aceptación**
- **RF-27-AC-1:** Dado el Administrador con sesión, cuando cambia el objetivo de resolución «Urgente» de 24 a 12 horas, entonces el tablero lo usa en las consultas posteriores y el cambio queda registrado.
- **RF-27-AC-2:** Dado un parámetro de tiempo, cuando se captura un valor menor o igual a cero, entonces el sistema responde 422 «El valor debe ser mayor que cero» y conserva el valor vigente.
- **RF-27-AC-3:** Dada la Auxiliar con sesión, cuando intenta modificar un parámetro, entonces recibe 403.
- **RF-27-AC-4:** Dado un plazo de confirmación cambiado a 96 horas, cuando un reporte pasa a `Terminado`, entonces el plazo de ese ciclo es de 96 horas.

---

## E2. Registro de incidencias

### HU-10 · Reportar una falla desde mi celular
**Como** residente, **quiero** registrar una falla indicando categoría, subtipo, descripción, ubicación y si es peligrosa, **para** que la administración se entere y la atienda.

**Prioridad:** Alta · **Story Points:** 8 · **RF:** RF-03

**Criterios de aceptación**
- **RF-03-AC-1:** Dado el último folio `RY-000123`, cuando el inquilino de `B-502` registra un reporte de «Iluminación» en la «Rampa del estacionamiento», entonces se crea `RY-000124` en `Reportado` con fecha de aviso igual a la hora del sistema.
- **RF-03-AC-2:** Dada una descripción de 4 caracteres, cuando se envía, entonces el sistema responde 422 «La descripción debe tener entre 10 y 1,000 caracteres» y no crea el reporte.
- **RF-03-AC-4:** Dado un inquilino de `B-502`, cuando intenta reportar en la unidad `A-301`, entonces recibe 422 «Solo puede reportar en su unidad o en áreas comunes».
- **RF-03-AC-6:** Dado un reporte sin respuesta a «¿peligroso o empeorando?», cuando se envía, entonces recibe 422 y no se crea.
- **RF-03-AC-10:** Dada la categoría «Iluminación» sin subtipo, cuando se envía, entonces recibe 422 «Indique el subtipo».

### HU-11 · Adjuntar fotos y un video al reporte
**Como** residente, **quiero** adjuntar fotos y un video de la falla, **para** que quien la atienda vea el problema sin ir primero a revisarlo.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-05

**Criterios de aceptación**
- **RF-05-AC-1:** Dadas 3 fotos JPEG de 4 MB, cuando las adjunto, entonces las tres quedan en la etapa «Alta».
- **RF-05-AC-2:** Dados una foto JPEG y un PDF, cuando envío, entonces el reporte se crea con la foto y el PDF se rechaza con «Formato no permitido: use JPEG o PNG».
- **RF-05-AC-3:** Dada una foto de 12 MB, cuando la adjunto, entonces se rechaza con «La foto supera 10 MB».
- **RF-05-AC-4:** Dadas 6 fotos válidas, cuando envío, entonces el sistema responde 422 «Máximo 5 fotografías por etapa».
- **RF-05-AC-5 y AC-6:** Dado un video MP4 de 30 MB, queda asociado al reporte; dado uno de 60 MB, se rechaza con «El video supera 50 MB».
- **RF-05-AC-7:** Dada una foto guardada, cuando cualquier usuario intenta borrarla, entonces recibe 403 y la foto sigue guardada.

### HU-12 · Enviar el reporte aunque no tenga foto
**Como** residente, **quiero** poder enviar un reporte sin fotografías ni datos opcionales, **para** no retrasar el aviso de una falla por no poder tomar la foto.

**Prioridad:** Alta · **Story Points:** 2 · **RF:** RF-03

**Criterios de aceptación**
- **RF-03-AC-7:** Dado un reporte con los datos obligatorios y sin fotos, cuando se envía, entonces se crea; y la interfaz muestra antes la solicitud de adjuntar fotografías.
- **RF-03-AC-9:** Dado un reporte sin «desde cuándo pasa», sin «si ya había pasado antes» y sin horarios de acceso, cuando se envía, entonces se crea; y si se indican, quedan guardados.

### HU-13 · Indicar la ubicación exacta y si autorizo el acceso
**Como** residente, **quiero** indicar la parte afectada de mi departamento y si autorizo el acceso, **para** que el personal sepa dónde ir y no entre sin mi permiso.

**Prioridad:** Alta · **Story Points:** 3 · **RF:** RF-03

**Criterios de aceptación**
- **RF-03-AC-3:** Dada una ubicación en mi unidad, cuando envío sin responder la autorización de acceso, entonces recibo 422 «Indique si autoriza el acceso a su departamento».
- **RF-03-AC-8:** Dada una falla dentro de mi unidad, cuando indico la parte afectada «Baño», entonces el reporte guarda torre, piso, número de unidad y parte afectada.

### HU-14 · No perder lo que capturé aunque falle la conexión
**Como** residente o personal de mantenimiento, **quiero** que el sistema conserve lo que capturé si hay error o no hay señal y lo reenvíe solo, **para** no tener que volver a escribir el reporte ni repetir las fotos.

**Prioridad:** Media · **Story Points:** 13 · **RF:** RF-03, RNF-11

**Criterios de aceptación**
- **RF-03-AC-5 [UI]:** Dado un error de validación, cuando se muestra, entonces los datos capturados siguen en el formulario.
- *(propuesto, RNF-11)* Dado que no hay conexión al enviar un reporte o un terminado, cuando pulso enviar, entonces queda guardado en el dispositivo como «Pendiente» y se envía automáticamente al recuperar señal, sin recapturar.
- *(propuesto, RNF-11)* Dado un envío guardado en el dispositivo, cuando consulto mi lista, entonces distingo cuáles están «Pendiente» y cuáles «Enviado».

*Nota:* es la historia más grande y de mayor riesgo técnico. Conviene dividirla en «guardar y reenviar el reporte» y «guardar y reenviar el terminado».

### HU-15 · Registrar un reporte a nombre de un residente
**Como** Administración, **quiero** capturar un reporte que llegó por WhatsApp, llamada, caseta o en persona, **para** que no se pierda aunque el residente no use el sistema.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-04

**Criterios de aceptación**
- **RF-04-AC-1:** Dado un aviso del 20/09/2026 22:10 capturado el 21/09/2026 09:00 con medio «Caseta», cuando se guarda, entonces el reporte conserva la fecha de aviso y los tiempos se calculan desde ella.
- **RF-04-AC-2:** Dada una fecha de aviso posterior a la hora del sistema, cuando se captura, entonces recibe 422 «La fecha del aviso no puede ser futura».
- **RF-04-AC-3:** Dado un reporte capturado a nombre del inquilino de `B-502`, cuando se guarda, entonces aparece en su lista y recibe el aviso de alta.
- **RF-04-AC-4:** Dada una ubicación `B-502` sin autorización de acceso, cuando se captura, entonces recibe 422 «Indique si el ocupante autoriza el acceso».
- **RF-04-AC-6:** Dado un reporte sin residente y sin nombre de referencia, cuando se guarda, entonces recibe 422 «Indique el nombre de quien reporta».
- **RF-04-AC-9:** Dado un reporte sin respuesta de peligro, cuando se captura, entonces recibe 422.

### HU-16 · Registrar reportes desde la caseta
**Como** personal de Vigilancia, **quiero** registrar los avisos que recibo en la caseta y ver solo los que registré, **para** que lo que me dicen de palabra llegue a la administración.

**Prioridad:** Alta · **Story Points:** 3 · **RF:** RF-04, RF-02

**Criterios de aceptación**
- **RF-04-AC-5:** Dado un reporte registrado por el Vigilante a nombre del residente de `A-301`, cuando la Administración lo consulta, entonces conserva al residente reportante y al Vigilante como quien capturó.
- **RF-04-AC-7:** Dado el Vigilante con sesión, cuando consulta sus reportes, entonces ve únicamente los que él registró.
- **RF-04-AC-8:** Dado un residente con sesión, cuando intenta usar la captura en nombre de terceros, entonces recibe 403.

### HU-17 · Enterarme de un posible reporte duplicado
**Como** Administración, **quiero** que el sistema me avise cuando se crea un reporte igual a uno ya abierto, **para** no atender dos veces la misma falla.

**Prioridad:** Media · **Story Points:** 5 · **RF:** RF-17

**Criterios de aceptación**
- **RF-17-AC-1:** Dado el reporte abierto `RY-000150` de «Plomería y fugas» en torre B, piso 4, cuando se crea otro igual, entonces el nuevo se crea marcado «Posible duplicado de RY-000150» y la Administración recibe el aviso.
- **RF-17-AC-5:** Dado un reporte abierto en torre B, piso 4, cuando se crea otro de la misma categoría en torre B, piso 5, entonces no se marca como posible duplicado.
- **RF-17-AC-6:** Dado que el único reporte similar está `Cerrado`, cuando se crea uno nuevo, entonces no se marca como posible duplicado.

### HU-18 · Unir reportes duplicados o mantenerlos independientes
**Como** Administración, **quiero** decidir si dos reportes son el mismo caso, **para** dar seguimiento a una sola atención y avisar a todos los afectados.

**Prioridad:** Media · **Story Points:** 5 · **RF:** RF-17

**Criterios de aceptación**
- **RF-17-AC-2:** Dado un posible duplicado, cuando la Administración decide que no es el mismo caso, entonces la marca se retira y los reportes siguen por separado.
- **RF-17-AC-3:** Dado un posible duplicado, cuando la Administración lo une, entonces el más reciente pasa a `Unido`, deja de tener seguimiento independiente y queda enlazado al original.
- **RF-17-AC-4:** Dados dos reportes unidos, cuando el principal se cierra, entonces ambos residentes reciben el aviso de cierre.

### HU-19 · Corregir mi reporte antes de que lo asignen
**Como** residente, **quiero** corregir la descripción, categoría o ubicación de mi reporte mientras no se asigna, **para** arreglar un error sin crear otro reporte.

**Prioridad:** Baja · **Story Points:** 3 · **RF:** RF-26

**Criterios de aceptación**
- **RF-26-AC-1:** Dado un reporte en `Reportado`, cuando el residente que lo registró corrige la descripción, entonces el cambio se guarda como versión nueva.
- **RF-26-AC-2:** Dada una corrección, cuando la Administración consulta el historial, entonces ve la descripción original, la nueva, el usuario y la fecha.
- **RF-26-AC-3:** Dado un reporte `Asignado`, cuando el residente intenta corregirlo, entonces recibe 409.
- **RF-26-AC-5:** Dado un cambio de subtipo de «Jardín o exterior» a «Pasillo o área techada», cuando se guarda, entonces la prioridad sugerida pasa a «Normal».

---

## E3. Gestión y atención del reporte

### HU-20 · Confirmar o cambiar la prioridad sugerida
**Como** Administración, **quiero** ver una prioridad sugerida según la categoría, el subtipo y el peligro, y poder cambiarla, **para** decidir rápido y con criterio uniforme.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-06

**Criterios de aceptación**
- **RF-06-AC-5:** Dado «Iluminación» con subtipo «Pasillo o área techada» y peligro «No», cuando se guarda, entonces la prioridad sugerida es «Normal».
- **RF-06-AC-6:** Dado «Iluminación» con subtipo «Jardín o exterior» y peligro «No», entonces la sugerida es «Menor».
- **RF-06-AC-7:** Dada una «Fuga activa», entonces la sugerida es «Urgente»; y un peligro «Sí» siempre sugiere «Urgente».
- **RF-06-AC-8:** Dada una prioridad sugerida «Normal», cuando la Administración la cambia a «Urgente», entonces el reporte conserva «Urgente».

### HU-21 · Asignar un reporte a un responsable
**Como** Administración, **quiero** asignar cada reporte a una persona de mantenimiento o a un proveedor, **para** que alguien sea responsable de atenderlo.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-06

**Criterios de aceptación**
- **RF-06-AC-1:** Dado `RY-000124` en `Reportado`, cuando se asigna con prioridad «Urgente» al Conserje, entonces pasa a `Asignado`, aparece en su lista y el historial registra el cambio.
- **RF-06-AC-3:** Dado un reporte sin prioridad, cuando se intenta asignar, entonces recibe 422 «La prioridad es obligatoria» y el estado no cambia.
- **RF-06-AC-10:** Dado un proveedor sin acceso, cuando se le asigna, entonces el reporte pasa a `Asignado` y no se genera aviso a ningún usuario.
- **RF-11-AC-5:** Dada una asignación al Conserje, entonces el Conserje recibe un aviso con el folio y la prioridad.

### HU-22 · Reclasificar un reporte durante la atención
**Como** Administración, **quiero** cambiar el responsable, el origen de la falla, la responsabilidad o la prioridad sin cambiar el estado, **para** corregir el rumbo cuando se descubre la causa real.

**Prioridad:** Alta · **Story Points:** 3 · **RF:** RF-06

**Criterios de aceptación**
- **RF-06-AC-2:** Dada una fuga observada en `A-402`, cuando registro origen `A-502` y responsable del costo «Propietario de A-502», entonces ambos datos quedan guardados y el reporte aparece al buscar por las dos ubicaciones.
- **RF-06-AC-4:** Dado `RY-000124` `En proceso`, cuando lo reclasifico con responsable «Bombas del Norte», entonces el estado no cambia, sale de la lista del Conserje y el historial muestra el cambio.
- **RF-06-AC-9:** Dada una responsabilidad «Por determinar», cuando la reclasifico como «Privada», entonces se registra la determinación y se avisa al reportante.

### HU-23 · Ver mis pendientes ordenados por urgencia
**Como** personal de mantenimiento, **quiero** una lista de mis reportes asignados con ubicación, fotos y datos de acceso, **para** saber qué atender primero.

**Prioridad:** Alta · **Story Points:** 3 · **RF:** RF-16

**Criterios de aceptación**
- **RF-16-AC-1:** Dado un reporte «Normal» y uno «Urgente», cuando consulto mi lista, entonces el «Urgente» aparece primero.
- **RF-16-AC-2:** Dados un reporte de otro usuario y uno mío ya `Cerrado`, entonces ninguno aparece.
- **RF-16-AC-3:** Dados dos reportes «Normal» con avisos del 18/09/2026 y del 21/09/2026, entonces el del 18/09/2026 aparece primero.
- **RF-16-AC-4:** Dado un reporte sin autorización de acceso, entonces veo «Sin autorización de acceso: coordinar con la Administración».

### HU-24 · Aplicar el flujo de estados del reporte
**Como** personal de mantenimiento, **quiero** iniciar la atención de un reporte asignado y que el sistema solo permita las transiciones válidas, **para** que el historial refleje lo que realmente pasó.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-07

**Criterios de aceptación**
- **RF-07-AC-1:** Dado `RY-000124` `Asignado` al Conserje, cuando lo pasa a `En proceso`, entonces el historial muestra la transición con usuario, fecha y hora.
- **RF-07-AC-2:** Dado un reporte en `Reportado`, cuando se intenta pasar a `Terminado`, entonces recibe 409 «Transición no permitida».
- **RF-07-AC-3:** Dados un reporte `Cancelado` y uno `Unido`, cuando se intenta cambiar su estado, entonces recibe 409 en ambos.
- **RF-07-AC-4:** Dado un reporte asignado al Conserje, cuando otro usuario de mantenimiento intenta pasarlo a `En proceso`, entonces recibe 404.
- **RF-07-AC-5:** Dado un reporte `Asignado`, cuando la Administración lo cancela sin motivo, recibe 422 «El motivo es obligatorio»; con motivo, pasa a `Cancelado`.

### HU-25 · Terminar un trabajo con evidencia
**Como** personal de mantenimiento, **quiero** marcar un reporte como terminado subiendo una foto de cómo quedó, **para** que haya evidencia del trabajo sin tener que escribir un informe.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-08

**Criterios de aceptación**
- **RF-08-AC-1:** Dado `RY-000124` `En proceso`, cuando adjunto una foto sin nota, entonces pasa a `Terminado` y la foto queda en la etapa «Evidencia».
- **RF-08-AC-2:** Dado un intento de terminar sin fotos, entonces recibo 422 «Adjunte al menos una foto del trabajo terminado» y el reporte sigue `En proceso`.
- **RF-08-AC-3:** Dado un reporte reabierto con 5 fotos del primer ciclo, cuando lo termino con 2 fotos nuevas, entonces se aceptan y el detalle las agrupa por ciclo.
- **RF-08-AC-7:** Dado que solo se atendió lo urgente, cuando describo lo pendiente, entonces queda en el historial y el reporte no se cierra.

### HU-26 · Registrar el avance de un proveedor que no usa el sistema
**Como** Administración, **quiero** actualizar el estado de un reporte en nombre de un proveedor sin acceso, **para** que su avance quede registrado aunque él no entre al sistema.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-07, RF-08

**Criterios de aceptación**
- **RF-07-AC-10:** Dado un reporte asignado a «Elevadores del Centro», cuando la Administración lo pasa a `En proceso`, entonces el historial muestra a la Administración y al proveedor en cuyo nombre se registró.
- **RF-08-AC-4:** Dado el mismo reporte, cuando la Administración lo termina sin fotos y con justificación, entonces pasa a `Terminado` y queda marcado «Terminado sin evidencia fotográfica».
- **RF-08-AC-5:** Dado el mismo caso sin justificación, entonces recibe 422 «Escriba la justificación».
- **RF-08-AC-6:** Dado el Conserje (personal propio), cuando intenta terminar sin fotos aunque escriba una justificación, entonces recibe 422, porque la excepción no le aplica.

### HU-27 · Registrar avances y la fecha de la visita
**Como** personal de mantenimiento, **quiero** dejar notas de avance y fijar la fecha de visita, **para** que el residente sepa cuándo irán y la administración entienda por qué un trabajo tarda.

**Prioridad:** Alta · **Story Points:** 3 · **RF:** RF-15

**Criterios de aceptación**
- **RF-15-AC-1:** Dado `RY-000124` `En proceso`, cuando agrego la nota «Falta la pieza; llega el jueves», entonces queda en el historial y el estado no cambia.
- **RF-15-AC-2:** Dada una visita fijada para el 29/09/2026 10:00, entonces el inquilino de `B-502` la ve en su lista y recibe el aviso.
- **RF-15-AC-3:** Dado un reporte con notas, cuando el inquilino lo consulta, entonces la respuesta no incluye las notas.

### HU-28 · Marcar un reporte como detenido
**Como** personal de mantenimiento, **quiero** marcar un reporte como detenido indicando el motivo, **para** que se entienda por qué no avanza y no se cuente como retraso mío.

**Prioridad:** Media · **Story Points:** 3 · **RF:** RF-18

**Criterios de aceptación**
- **RF-18-AC-1:** Dado `RY-000124` `En proceso`, cuando lo marco detenido con motivo «Espera de pieza», entonces queda detenido, el estado no cambia y el historial lo registra.
- **RF-18-AC-2:** Dado un intento sin motivo, entonces recibo 422 «Indique el motivo de la detención».
- **RF-18-AC-3:** Dado un reporte detenido, cuando lo reanudo, entonces deja de estar detenido y el historial lo registra.
- **RF-18-AC-4:** Dado un reporte `Terminado`, cuando intento marcarlo detenido, entonces recibo 409.
- **RF-18-AC-5:** Dado un reporte marcado detenido, entonces el residente recibe el aviso.

### HU-29 · Registrar el costo y quién lo pagó
**Como** Administración, **quiero** anotar el monto de la reparación y si lo pagó el condominio o el condómino, **para** rendir cuentas al comité y cobrar al responsable correcto.

**Prioridad:** Media · **Story Points:** 3 · **RF:** RF-20

**Criterios de aceptación**
- **RF-20-AC-1 y AC-2:** Dado un costo de $2,500.00 pagado por el condominio, o de $1,200.00 pagado por el condómino, entonces el reporte queda con ese monto y pagador.
- **RF-20-AC-3:** Dado un monto negativo, entonces recibo 422 «El monto no puede ser negativo».
- **RF-20-AC-4:** Dado un costo corregido de $2,500.00 a $2,300.00, entonces el nuevo valor es el vigente y el anterior se conserva en el historial.
- **RF-20-AC-5:** Dado un reporte con costo, cuando el inquilino lo consulta, entonces ve el pagador pero no el monto.

### HU-30 · Marcar una reparación con garantía
**Como** personal de mantenimiento, **quiero** marcar una reparación como cubierta por garantía con su fecha de vencimiento, **para** poder reclamarla si la falla regresa.

**Prioridad:** Baja · **Story Points:** 2 · **RF:** RF-25

**Criterios de aceptación**
- **RF-25-AC-1:** Dado `RY-000124` terminado con evidencia, cuando lo marco «con garantía» hasta el 30/09/2027, entonces guarda la marca y la fecha.
- **RF-25-AC-2:** Dado un vencimiento 01/10/2026 con hora del sistema 03/10/2026, entonces recibo 422 «La fecha de vencimiento no puede ser pasada».
- **RF-25-AC-3:** Dada una garantía registrada, cuando la Administración consulta el detalle, entonces ve la marca y la fecha.

### HU-31 · Cancelar un reporte que ya se resolvió
**Como** residente, **quiero** cancelar un reporte mío cuando el problema ya se resolvió solo, **para** que no se mande personal a atender algo que ya no existe.

**Prioridad:** Alta · **Story Points:** 3 · **RF:** RF-07

**Criterios de aceptación**
- **RF-07-AC-6:** Dado `RY-000124` `Asignado`, cuando lo cancelo con el motivo «Ya se resolvió», entonces pasa a `Cancelado` y se avisa a la Administración y al responsable.
- **RF-07-AC-7:** Dado un reporte `En proceso`, cuando intento cancelarlo, entonces recibo 409.
- **RF-07-AC-8:** Dado un reporte de otro residente, cuando intento cancelarlo, entonces recibo 404.
- **RF-07-AC-9:** Dado un motivo distinto de «Ya se resolvió», entonces recibo 422 «Solo puede cancelar un reporte que ya se resolvió».

---

## E4. Cierre y comunicación con el residente

### HU-32 · Consultar el estado de mis reportes
**Como** residente, **quiero** ver el estado de mis reportes, la fecha de la visita y si algo está detenido, **para** no tener que preguntar a la administración.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-10

**Criterios de aceptación**
- **RF-10-AC-1:** Dado un inquilino con 2 reportes en su unidad y 3 en áreas comunes, cuando consulta, entonces recibe los 5 con su estado y las fechas de cada cambio.
- **RF-10-AC-2:** Dado un reporte de `A-301`, cuando el inquilino de `B-502` lo pide por folio, entonces recibe 404.
- **RF-10-AC-3:** Dado un reporte de un área común hecho por otro residente, entonces veo categoría, descripción, estado y fechas, pero no al reportante.
- **RF-10-AC-4:** Dado un reporte de un inquilino anterior previo a mi fecha de vinculación, entonces no aparece.
- **RF-10-AC-5 y AC-6:** Dado un reporte unido, veo «Unido a RY-000150»; dado uno detenido, veo el motivo.

### HU-33 · Recibir avisos de mis reportes
**Como** residente o propietario, **quiero** recibir un aviso cuando mi reporte avanza, **para** enterarme sin entrar al sistema.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-11

**Criterios de aceptación**
- **RF-11-AC-1:** Dado un reporte nuevo del inquilino, entonces recibe aviso en el sistema y un correo con folio y fecha.
- **RF-11-AC-2:** Dado que el propietario de `B-502` no vive ahí, cuando el reporte pasa a `Asignado`, entonces el inquilino recibe aviso y correo, y el propietario solo un correo.
- **RF-11-AC-3:** Dado un reporte de un área común, cuando cambia de estado, entonces solo se avisa a quien lo reportó.
- **RF-11-AC-7:** Dado el paso de `Asignado` a `En proceso`, entonces el residente no recibe aviso.
- **RF-11-AC-9:** Dado un reporte `Terminado`, entonces el correo informa que puedo responder «Ya quedó» o «Sigue fallando» hasta el vencimiento del plazo.

### HU-34 · Avisar a Mantenimiento y a la Administración, y vigilar los correos fallidos
**Como** Administración, **quiero** que el sistema avise a mantenimiento de sus asignaciones y a mí de lo que requiere atención, y que muestre los correos que no se enviaron, **para** que ningún cambio pase sin que se entere quien debe.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-11

**Criterios de aceptación**
- **RF-11-AC-4:** Dado que el correo no responde, cuando un reporte cambia de estado, entonces el cambio se guarda, el aviso interno se crea y tras 3 intentos el correo aparece como «Fallido».
- **RF-11-AC-5:** Dada una asignación al Conserje, entonces recibe aviso interno y correo con folio y prioridad.
- **RF-11-AC-6:** Dada una cancelación por el residente, entonces el Conserje y la Administración reciben aviso y correo con el motivo.
- **RF-11-AC-8:** Dado un reportante «Sin cuenta», cuando el reporte pasa a `Asignado`, entonces la Administración recibe el aviso para comunicarlo manualmente.

### HU-35 · Confirmar si la reparación quedó bien
**Como** residente, **quiero** responder «Ya quedó» o «Sigue fallando» cuando mi reporte se marca terminado, **para** que no se cierre un problema que no se resolvió.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-09

**Criterios de aceptación**
- **RF-09-AC-1:** Dado un reporte terminado el 22/09/2026 10:00, cuando respondo «Ya quedó» el mismo día a las 18:00, entonces se registra y la Administración puede cerrarlo.
- **RF-09-AC-3:** Dado el mismo reporte, cuando intento responder el 25/09/2026 10:01, entonces recibo 409 «El plazo para responder terminó».
- **RF-09-AC-5:** Dada una respuesta «Sigue fallando», cuando la Administración reabre el reporte, entonces pasa a `En proceso` con ciclo nuevo y se conserva mi respuesta.

### HU-36 · Cerrar un reporte después de revisarlo
**Como** Administración, **quiero** cerrar un reporte solo cuando el residente confirmó o venció el plazo, **para** garantizar que nada se cierra sin revisión.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-09

**Criterios de aceptación**
- **RF-09-AC-2:** Dado un reporte terminado sin respuesta del residente, cuando intento cerrarlo antes del plazo, entonces recibo 409 «Esperando confirmación del residente hasta el 25/09/2026 10:00».
- **RF-09-AC-4:** Dada una respuesta «Sigue fallando», cuando intento cerrar sin comentario, entonces recibo 422 «Escriba el motivo del cierre».
- **RF-09-AC-6 y AC-9:** Dado un reporte de un área común o de un reportante «Sin cuenta», cuando lo cierro, entonces pasa a `Cerrado` sin esperar confirmación.
- **RF-09-AC-7 y AC-8:** Dados un usuario de mantenimiento o el residente, cuando intentan cerrar, entonces reciben 403.

### HU-37 · Indicar que el problema persiste y reabrir el reporte
**Como** residente, **quiero** avisar que el problema volvió después de cerrarse, **para** que la administración lo reabra con su historial en lugar de empezar de cero.

**Prioridad:** Media · **Story Points:** 5 · **RF:** RF-19

**Criterios de aceptación**
- **RF-19-AC-1:** Dado un reporte cerrado el 01/10/2026, cuando indico el 10/10/2026 que persiste, entonces la indicación se registra y la Administración puede consultarla.
- **RF-19-AC-2:** Dada la indicación, cuando la Administración aún no decide, entonces el reporte sigue `Cerrado`.
- **RF-19-AC-3:** Dado un reporte cerrado con historial, cuando la Administración lo reabre con comentario, entonces pasa a `En proceso` con el mismo folio y ciclo nuevo.
- **RF-19-AC-4:** Dado el plazo de 30 días vencido, cuando intento indicar que persiste, entonces recibo 409 «El plazo para reabrir terminó».
- **RF-19-AC-5:** Dada una reapertura sin comentario, entonces recibo 422 «Escriba el motivo de la reapertura».

### HU-38 · Enterarme de los reportes que no se mueven
**Como** Administración, **quiero** una alerta cuando un reporte lleva demasiado tiempo sin cambiar de estado, **para** intervenir antes de que se convierta en queja.

**Prioridad:** Media · **Story Points:** 3 · **RF:** RF-22

**Criterios de aceptación**
- **RF-22-AC-1:** Dado un reporte «Urgente» en `Reportado` desde las 08:00 y un umbral de 2 horas, cuando son las 10:01, entonces la Administración recibe el aviso.
- **RF-22-AC-2:** Dado el aviso ya enviado, cuando pasa una hora más sin cambio, entonces no se envía un segundo aviso.
- **RF-22-AC-3:** Dado un reporte detenido por «Espera de pieza», cuando se evalúan los umbrales, entonces no genera aviso.
- **RF-22-AC-4:** Dado el umbral «Normal» cambiado a 12 horas, cuando un reporte «Normal» lleva 13 horas sin cambio, entonces la Administración recibe el aviso.

---

## E5. Historial, métricas e informes

### HU-39 · Buscar reportes anteriores
**Como** Administración, **quiero** buscar reportes por ubicación, categoría, estado, prioridad, fechas y texto, **para** responder a un residente o al comité con evidencia.

**Prioridad:** Alta · **Story Points:** 5 · **RF:** RF-12

**Criterios de aceptación**
- **RF-12-AC-1:** Dados 4 reportes de «Bombas y cisterna» y el rango 01/01/2026 a 30/06/2026, entonces recibo exactamente 2, el del 30/06/2026 primero.
- **RF-12-AC-2:** Dado un reporte observado en `A-402` con origen `A-502`, cuando busco por `A-502`, entonces aparece.
- **RF-12-AC-4:** Dados reportes con la palabra «gotera», cuando busco ese texto, entonces recibo todos los que la contienen y ninguno más.
- **RF-12-AC-5:** Dado un residente con sesión, cuando intenta usar la búsqueda, entonces recibe 403.

### HU-40 · Ver el detalle completo de un reporte
**Como** Administración, **quiero** ver en un reporte las fotos por etapa y ciclo, las notas y todo su historial, **para** reconstruir qué pasó y quién lo hizo.

**Prioridad:** Alta · **Story Points:** 3 · **RF:** RF-12, RF-08

**Criterios de aceptación**
- **RF-12-AC-3:** Dado un reporte cerrado con una reapertura, cuando lo consulto, entonces veo las fotos del alta y las de evidencia separadas por ciclo, y cada cambio con usuario, fecha, hora y comentario.
- **RF-08-AC-3:** Dado un reporte terminado en dos ciclos, entonces el detalle muestra las evidencias agrupadas por ciclo.

### HU-41 · Ver los tiempos de atención y el cumplimiento
**Como** Administración, **quiero** un tablero con el tiempo promedio de atención y el cumplimiento por prioridad, **para** demostrar al comité cómo se está atendiendo.

**Prioridad:** Alta · **Story Points:** 8 · **RF:** RF-13

**Criterios de aceptación**
- **RF-13-AC-1:** Dados 3 reportes «Urgente» de septiembre con primera atención de 30, 50 y 130 minutos y resolución de 10, 20 y 36 horas, entonces veo primera atención promedio de 70 minutos con cumplimiento de 67 %, y resolución promedio de 22 horas con cumplimiento de 67 %.
- **RF-13-AC-4:** Dado un reporte «Normal» sin terminar con su objetivo de 72 horas vencido, entonces cuenta como incumplido.
- **RF-13-AC-7:** Dados 2 reportes asignados a «Bombas del Norte», entonces aparecen en el bloque de proveedores externos y no en el de personal propio.
- **RF-13-AC-8:** Dado un residente con sesión, cuando solicita el tablero, entonces recibe 403.

### HU-42 · Detectar fallas que se repiten
**Como** Administración, **quiero** ver qué combinaciones de categoría y ubicación se repiten, **para** decidir una reparación de fondo en lugar de seguir parchando.

**Prioridad:** Alta · **Story Points:** 3 · **RF:** RF-13

**Criterios de aceptación**
- **RF-13-AC-2:** Dados 3 reportes de «Iluminación» en la «Rampa del estacionamiento» con avisos 15/07/2026, 15/08/2026 y 20/09/2026, cuando consulto el 03/10/2026, entonces aparece como recurrente con los 3 folios.
- **RF-13-AC-3:** Dados 3 reportes en los últimos 90 días y uno `Cancelado`, entonces la combinación no aparece como recurrente.

### HU-43 · Ver el tiempo detenido y la adopción del sistema
**Como** Administración, **quiero** ver cuánto tiempo estuvieron detenidos los reportes y qué porcentaje entra por el sistema, **para** separar los retrasos de terceros de los propios y medir si el sistema se adopta.

**Prioridad:** Media · **Story Points:** 3 · **RF:** RF-13

**Criterios de aceptación**
- **RF-13-AC-5:** Dado un reporte detenido del 10/09/2026 09:00 al 12/09/2026 09:00 por «Espera de pieza», entonces el tablero muestra 48 horas detenidas, por separado, con el motivo.
- **RF-13-AC-6:** Dados 10 reportes de octubre, 6 con medio «Sistema» y 4 por WhatsApp, entonces la adopción es 60 %.

### HU-44 · Exportar el tablero para la asamblea
**Como** Administración, **quiero** exportar el tablero de un periodo a un PDF, **para** presentarlo al comité o a la asamblea anual.

**Prioridad:** Media · **Story Points:** 3 · **RF:** RF-23

**Criterios de aceptación**
- **RF-23-AC-1:** Dado el tablero de septiembre, cuando lo exporto, entonces el PDF incluye el periodo, el tiempo promedio por prioridad, el cumplimiento y las incidencias recurrentes.
- **RF-23-AC-2:** Dada una resolución promedio «Urgente» de 22 horas en pantalla, entonces el PDF muestra las mismas cifras.
- **RF-23-AC-3:** Dado un residente con sesión, cuando solicita la exportación, entonces recibe 403.
