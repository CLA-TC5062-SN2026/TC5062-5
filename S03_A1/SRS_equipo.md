# Especificación de Requerimientos de Software (SRS) — ReportaYa

## Sistema de reporte y seguimiento de incidencias de mantenimiento en un condominio

| Campo | Valor |
|---|---|
| Sistema | ReportaYa |
| Versión del documento | 2.0 (versión consolidada del equipo) |
| Fecha | 3 de octubre de 2026 |
| Estructura | IEEE 830 simplificada |
| Fuentes | `SRS_final.md` (en adelante **SRS-Base**, v1.2, entrevista con la Lic. Patricia Soto), `SRS_final_Alejandro Arreola.md` (**SRS-Arreola**, v1.1) y `SRS_finalluis.md` (**SRS-Luis**, v1.2). Los dos últimos usan las mismas sesiones de elicitación (A: cliente simulado, B: cliente real). |

Este documento sustituye a los tres SRS individuales. Cada conflicto entre ellos y cada brecha (requerimiento que solo algunos identificaron) se resolvió y quedó registrado en la **sección 6**, con su justificación. Los identificadores `RF-XX-AC-Y` de la sección 3.1 son la clave de trazabilidad: cada endpoint de la API y cada prueba automatizada deben referenciar al menos uno. La numeración es única y continua; la sección 7 la relaciona con la numeración de cada SRS de origen.

Los valores y reglas que propuso el equipo sin que una entrevista los confirmara (por ejemplo, umbrales, plazos y la excepción de evidencia para proveedores sin acceso) se asumen como definitivos en esta versión. Se listan en la sección 5 como decisiones asumidas. Los que son numéricos se ajustan sin cambiar la especificación mediante RF-27.

---

## 1. Introducción

### 1.1 Propósito

Especificar qué debe hacer ReportaYa y bajo qué condiciones, con la precisión suficiente para diseñar la API, construir el sistema y derivar sus pruebas sin consultar a los autores. Está dirigido al equipo de desarrollo, al profesor que evalúa el proyecto y a la administración del condominio que valida que el sistema resuelve su problema.

### 1.2 Alcance del producto

**ReportaYa** es una aplicación web para **un condominio** de departamentos. Los residentes reportan fallas de mantenimiento con fotos y ubicación; la administración las clasifica, asigna y cierra; el personal de mantenimiento o el proveedor externo registra el avance y la evidencia; y la administración consulta el historial, los tiempos de atención y las fallas recurrentes.

**Problema que resuelve.** Hoy los reportes llegan por WhatsApp, llamada, caseta, correo o de palabra, y se anotan en una libreta o una hoja de cálculo. No hay un registro único: los reportes se mezclan con otros mensajes, se pierden, dos personas reportan lo mismo y nadie sabe en qué estado va cada uno. La administración no tiene evidencia con fechas para responder a los residentes ni al comité.

**Objetivos medibles:**

1. Todo reporte queda registrado con folio y fecha de aviso, sin importar el medio por el que llegó (RF-03, RF-04).
2. El residente consulta el estado de su reporte y la fecha programada de visita sin preguntar a la administración (RF-10, RF-15).
3. La administración mide el tiempo de atención contra un objetivo por prioridad (RF-13, RD-02).
4. Cada terminado tiene evidencia y un historial que nadie puede alterar (RF-08, RNF-07).
5. La adopción se mide como el porcentaje de reportes que entran por el sistema frente a otros medios (RF-13). La meta de la cliente es que sea la mayoría en 3 meses.

**Alcance mínimo de 12 semanas:** alta de reporte con fotos y ubicación, clasificación y asignación, seguimiento de estado, cierre con evidencia y tablero de tiempos e incidencias recurrentes. Las demás funciones de esta especificación se priorizan después de ese mínimo (ver sección 5, punto 15).

**Fuera de alcance (exclusiones):**

| # | Exclusión | Motivo |
|---|---|---|
| EX-01 | Cobro de cuotas, adeudos y pagos. | Es otro proceso del condominio. |
| EX-02 | Análisis del gasto por tipo de mantenimiento, facturas y su conservación contable. | El cliente real lo pidió como fase posterior. ReportaYa solo registra costo y pagador (RF-20). |
| EX-03 | Mantenimiento preventivo programado. | El historial es el insumo para una versión futura. |
| EX-04 | Control de acceso de proveedores en la caseta. | Es operación de seguridad. |
| EX-05 | Aplicación móvil nativa y sitio móvil separado. | El cliente pidió web sin instalar nada. La tolerancia a mala señal se cubre en RNF-11. |
| EX-06 | Integración con WhatsApp. | Los reportes que llegan por ahí se capturan con RF-04. Queda como posibilidad futura. |
| EX-07 | Varios condominios en una instalación (multi-tenant). | La versión 1 atiende a un solo condominio. |
| EX-08 | Cuentas para propietarios no residentes, para el comité, y registro abierto de cuentas. | El propietario no residente recibe avisos por correo sin cuenta (RF-11). Toda cuenta la crea la Administración (RF-02). |
| EX-09 | Validar automáticamente los horarios del reglamento para trabajos con ruido. | La fecha de visita la fija la Administración (RF-15). Los horarios se registran como RD-11, informativos. |
| EX-10 | Chat o mensajería entre usuarios. | El sistema comunica cambios (RF-11) y notas (RF-15). La conversación sigue por los medios actuales. |
| EX-11 | Emergencias reales. | Se atienden por teléfono o en la caseta (RD-12). ReportaYa no sustituye ese canal. |
| EX-12 | Flujo de cotización y autorización de gastos del comité. | Solo se registra como motivo de detención (RF-18). |
| EX-13 | Registrar la autorización de acceso de un ocupante distinto del reportante. | La Administración lo coordina fuera del sistema. |
| EX-14 | Contexto de campus escolar. | Las dos entrevistas confirmaron condominio. |

### 1.3 Definiciones, acrónimos y abreviaturas

| Término | Definición |
|---|---|
| Reporte / incidencia | Registro de una falla de mantenimiento. Tiene folio, ubicación, categoría, prioridad, estado y evidencia. |
| Folio | Identificador único y consecutivo, con el formato `RY-` más seis dígitos (por ejemplo, `RY-000124`). |
| Unidad | Departamento, identificado por torre, piso y número (por ejemplo, `B-502`: torre B, piso 5). |
| Área común | Espacio compartido: pasillos, escaleras, elevador, estacionamiento (incluido el sótano), cisterna y bombas, accesos, alberca, jardín, fachada. |
| Ubicación observada | Lugar donde se ve la falla. |
| Ubicación de origen | Lugar donde la Administración determina que está la causa. Si no se captura, es igual a la observada. |
| Medio de origen (canal) | Por dónde llegó el aviso: «Sistema» (alta directa del residente, RF-03) o, capturado por RF-04, «WhatsApp», «Llamada», «Caseta», «Correo» o «Presencial». |
| Fecha de aviso | Momento en que el condominio se enteró de la falla. En RF-03 es la fecha y hora de alta; en RF-04, la que captura la Administración. **Todos los tiempos, filtros y periodos se calculan desde la fecha de aviso.** |
| Reportante | Persona a cuyo nombre queda el reporte: un residente con cuenta, o una persona «Sin cuenta» (nombre de referencia) cuando la Administración o Vigilancia capturan por ella. |
| Residente | Persona que vive en una unidad y tiene cuenta: propietario residente o inquilino. |
| Propietario / condómino | Dueño de la unidad. Puede no vivir en el condominio. |
| Propietario no residente | Propietario que no vive ahí. No tiene cuenta (EX-08); recibe avisos por correo. |
| Administración | Rol con dos perfiles: **Administrador** y **Auxiliar administrativa**. La Auxiliar solo asigna, reclasifica y cierra mientras tenga una delegación vigente (RF-21). |
| Vigilancia | Rol de la caseta. Registra reportes en nombre de terceros (RF-04) y ve solo los que registró. |
| Usuario de Mantenimiento | Rol que atiende reportes asignados: personal propio (por ejemplo, el conserje) o proveedor externo con cuenta. |
| Proveedor externo | Empresa o técnico externo (plomero, elevadores, impermeabilización). **Con acceso:** tiene cuenta de rol Mantenimiento. **Sin acceso:** se registra como contacto asignable y la Administración actualiza su avance (RF-02, RF-07). |
| Prioridad | `Urgente`, `Normal` o `Menor` (RD-01). |
| Responsabilidad | Clasificación `Común`, `Privada` o `Por determinar` que define quién paga (RD-03). |
| Detenida | Marca (no es un estado) de un reporte `Asignado` o `En proceso` cuya atención está en espera por un motivo registrado (RF-18). |
| Terminado | Estado en que el responsable informa que concluyó su trabajo. **No equivale a cerrado.** |
| Cerrado | Acto administrativo de la Administración, tras revisar el trabajo y la evidencia (RF-09). |
| Reapertura | Regreso de un reporte `Terminado` o `Cerrado` a `En proceso`, con el mismo folio e historial (RF-07, RF-19). |
| Ciclo de atención | Periodo entre que un reporte pasa a `En proceso` y la siguiente vez que pasa a `Terminado`. Una reapertura inicia un ciclo nuevo. |
| Tiempo de primera atención | Tiempo entre la fecha de aviso y la primera vez que el reporte pasa a `En proceso`. |
| Tiempo de resolución | Tiempo entre la fecha de aviso y la primera vez que el reporte pasa a `Terminado`. |
| Incidencia recurrente | Tres o más reportes no cancelados ni unidos, de la misma categoría y la misma ubicación de origen, cuya fecha de aviso cae dentro de los 90 días anteriores a la fecha de consulta, inclusive (parámetros configurables, RF-27). |
| Rango de fechas | Siempre inclusivo por días completos en la zona horaria del condominio: del día inicial a las 00:00:00 al día final a las 23:59:59. |
| AC | Criterio de aceptación, en formato Dado que – cuando – entonces (Given–When–Then), con ID `RF-XX-AC-Y`. |
| RF / RNF / RD | Requerimiento funcional / no funcional / de dominio. |
| SRS | Software Requirements Specification. |

Todas las fechas y horas se registran en la zona horaria del condominio, configurable en el despliegue (valor inicial `America/Mexico_City`), y se muestran con el formato `dd/mm/aaaa hh:mm`. Los plazos se expresan en horas corridas, salvo que se indique otra cosa.

### 1.4 Referencias

- `proyecto_base.md`: ficha inicial del proyecto.
- `transcript_entrevista.md`: transcripción de las entrevistas (A: cliente simulado, B: cliente real) y la entrevista con la Lic. Patricia Soto.
- `SRS_final.md`, `SRS_final_Alejandro Arreola.md`, `SRS_finalluis.md`: SRS individuales consolidados aquí.
- `revision_SRS.md` de cada integrante: análisis de la elicitación y hallazgos de revisión.
- Arroyo Vaca y Obando Quito (2022), citado por Fracttal: el mantenimiento preventivo bien implementado reduce 30 % los costos y alarga hasta 50 % la vida útil de los equipos.

### 1.5 Visión general del documento

La sección 2 describe el producto, sus usuarios, restricciones y supuestos. La sección 3 detalla los requerimientos: funcionales con sus criterios de aceptación (3.1), no funcionales (3.2), de dominio (3.3) e interfaces (3.4). La sección 4 resume las notas de diseño. La sección 5 lista las decisiones asumidas y las cuestiones abiertas. La sección 6 registra cómo se resolvió cada conflicto y brecha entre los tres SRS. La sección 7 es la matriz de trazabilidad.

---

## 2. Descripción general

### 2.1 Perspectiva del producto

ReportaYa es un sistema nuevo e independiente. Reemplaza el registro informal actual, pero no se conecta con esos medios (EX-06). Quien siga reportando por WhatsApp, llamada o caseta se registra con RF-04.

| Componente | Responsabilidad |
|---|---|
| Frontend web (responsivo) | Interfaz para todos los roles, en celular y computadora. |
| Backend (FastAPI) | Reglas de negocio, flujo de estados, control de acceso por rol, cálculo de métricas. |
| Base de datos (PostgreSQL) | Padrón, reportes, historial, notas, notificaciones y parámetros. |
| Almacenamiento de archivos | Fotos y videos, detrás de una interfaz intercambiable (RNF-08). |
| Servicio de correo | Avisos (RF-11) y enlaces de acceso (RF-14). Es un servicio externo. |

### 2.2 Funciones del producto

1. **Cuentas y padrón:** unidades, áreas comunes, usuarios y proveedores; activación y recuperación de contraseña (RF-01, RF-02, RF-14, RF-24).
2. **Registro:** alta por el residente, captura en nombre de terceros, fotos y video, corrección, detección y unión de duplicados (RF-03, RF-04, RF-05, RF-17, RF-26).
3. **Gestión:** prioridad sugerida y confirmada, responsabilidad, asignación, reclasificación, delegación y parámetros (RF-06, RF-21, RF-27).
4. **Flujo de estados:** `Reportado → Asignado → En proceso → Terminado → Cerrado`, más `Cancelado` y `Unido`, con detención y reapertura (RF-07, RF-18, RF-19).
5. **Atención:** lista de asignados, notas, fecha de visita, evidencia y garantía (RF-08, RF-15, RF-16, RF-25).
6. **Cierre:** confirmación del residente y validación de la Administración (RF-09).
7. **Avisos y alertas:** notificaciones y reportes estancados (RF-11, RF-22).
8. **Historial y métricas:** búsqueda, costo y pagador, tablero y exportación (RF-12, RF-13, RF-20, RF-23).

### 2.3 Características de los usuarios

| Perfil | Descripción | Dispositivo | Qué puede hacer |
|---|---|---|---|
| Residente (propietario residente o inquilino) | Vive en una unidad. Tiene cuenta. Algunos adultos mayores no usarán el sistema; la Administración captura por ellos (RF-04). | Celular | Reportar; consultar sus reportes y los de áreas comunes; corregir un reporte aún no asignado; confirmar o rechazar la solución; indicar que el problema persiste; cancelar un reporte ya resuelto. |
| Propietario no residente | Dueño que no vive ahí. **Sin cuenta.** | Correo | Recibir por correo los avisos de su unidad. |
| Vigilancia | Guardias de la caseta; rotan con frecuencia. | Computadora de la caseta | Registrar reportes en nombre de terceros y ver los que registró. |
| Mantenimiento (propio o proveedor con cuenta) | Poca experiencia digital; trabaja en movimiento y a veces sin señal. | Celular Android de gama básica | Ver sus asignados, iniciar la atención, agregar notas, detener y reanudar, marcar terminado con evidencia. |
| Proveedor externo sin acceso | No usa el sistema. Su avance lo registra la Administración. | — | — |
| Administración (Administrador y Auxiliar) | Recibe, revisa, clasifica, asigna, cierra y rinde cuentas. | Computadora y celular | Todas las funciones de gestión. La Auxiliar, con las restricciones de RF-21. |
| Comité de vigilancia | Autoriza gastos de más de $15,000 y pide cuentas. | — | Sin cuenta en esta versión; recibe la exportación del tablero (RF-23). |

**Matriz de visibilidad.** El backend la aplica en cada petición (RNF-05).

| Información | Residente | Propietario no residente (solo correo) | Vigilancia | Mantenimiento | Administración |
|---|---|---|---|---|---|
| Reportes de su unidad (RF-10) | Sí, desde su fecha de vinculación | Solo avisos de cambio de estado | Solo los que registró | Solo los asignados a él | Sí |
| Reportes de otras unidades | No | No | No | Solo los asignados a él | Sí |
| Reportes de áreas comunes | Sí, sin datos del reportante | No | Solo los que registró | Solo los asignados a él | Sí |
| Fotos del interior de una unidad (RD-08) | Solo de su unidad | No | Solo las que subió | Solo de los asignados a él | Sí |
| Fecha programada de visita (RF-15) | Sí | Sí, en el aviso | No | Sí | Sí |
| Notas de avance (RF-15) | No | No | No | Sí | Sí |
| Autorización y horarios de acceso a la unidad | Sí, los suyos | No | No | Sí, en los asignados | Sí |
| Motivo de detención (RF-18) | Sí, en sus reportes | No | No | Sí | Sí |
| Teléfonos y correos de otras personas | No | No | No | No | Sí |
| Tipo de ocupación y datos del propietario (RF-24) | No | No | No | No | Sí |
| Responsable asignado | No | No | No | Solo si es él | Sí |
| Pagador del costo (RF-20) | Sí, de su unidad | Sí, en el aviso | No | No | Sí |
| Monto del costo (RF-20) | No | No | No | No | Sí |

### 2.4 Restricciones

| # | Restricción | Origen |
|---|---|---|
| R-01 | Aplicación web adaptada al celular; no se exige instalar nada. | Cliente real |
| R-02 | Costo de operación modesto; cualquier gasto fijo requiere aprobación del comité o la asamblea. Se presentan métricas concretas para obtenerla. | Todas las entrevistas |
| R-03 | Stack del curso: backend FastAPI y Python, PostgreSQL y contenedores Docker. El frontend se decide en diseño (sección 4). Es una decisión del equipo, no un requisito del cliente; no se modifican requisitos para ajustarse a ella. | Actividad S01-A2 |
| R-04 | Entrega del alcance mínimo en 12 semanas. | `proyecto_base.md` |
| R-05 | El almacenamiento de archivos debe poder usar disco local o nube (patrón Adapter). | `proyecto_base.md` |
| R-06 | Los datos personales de residentes y propietarios solo los consulta la Administración. | Entrevistas A y B |
| R-07 | Sitio único: un condominio por instalación. | EX-07 |
| R-08 | Zonas de conectividad deficiente (sótano, nivel -2, cuarto de bombas, algunos pasillos). | Entrevistas |
| R-09 | El personal de mantenimiento usa un celular Android de gama básica. | Entrevistas |

### 2.5 Supuestos y dependencias

| # | Supuesto | Si resulta falso |
|---|---|---|
| S-01 | Cada usuario con cuenta y cada propietario no residente tiene un correo. | Sin correo no se activa la cuenta (RF-14) ni se envían avisos (RF-11). |
| S-02 | La Administración mantiene actualizado el padrón de ocupantes (RF-02). | No se sabe quién reporta desde qué unidad. |
| S-03 | Hay un servicio de correo disponible. | Los avisos quedan «Fallidos» (RF-11-AC-4) y la activación se detiene. |
| S-04 | Los tiempos objetivo (RD-02) salen de entrevistas, no de un contrato. | Se ajustan en los parámetros (RF-27). |
| S-05 | Cada usuario de Mantenimiento tiene un celular con navegador que cumple RNF-01. | La Administración registra el avance por esa persona. |
| S-06 | La mayoría de los residentes tiene smartphone; para quienes no, la Administración captura (RF-04). | Aumenta la carga de captura de la Administración. |
| S-07 | El comité aprueba el gasto si se le presentan métricas (RF-13, RF-23). | La adopción se detiene. |
| S-08 | Los proveedores sin acceso no registran información directamente. | Ver RF-08-AC-4 y RD-09. |

---

## 3. Requerimientos específicos

### 3.0 Convenciones para los criterios de aceptación

Los criterios se prueban contra la API, salvo los marcados **[UI]**, que se prueban en la interfaz. Los datos de ejemplo usan el condominio de prueba: torres `A` y `B`; unidad `B-502` (torre B, piso 5) ocupada por un inquilino y con propietario no residente; unidad `A-301` con otro residente; área común «Rampa del estacionamiento»; usuarios de Mantenimiento «Conserje» (personal propio) y «Bombas del Norte» (proveedor externo con acceso); proveedor «Elevadores del Centro» (sin acceso); usuarios «Administrador», «Auxiliar» y «Vigilante».

**Reloj de referencia.** Los criterios que dependen del tiempo se prueban con la hora del sistema fijada por la prueba (RNF-10). Los valores numéricos de plazos y objetivos son los valores iniciales de RF-27.

**Contrato de errores.** Cuando un criterio dice que el sistema rechaza una petición, responde con uno de estos códigos y no modifica ningún dato. Si aplica más de uno, gana el primero:

| Orden | Código | Cuándo | Mensaje |
|---|---|---|---|
| 1 | 401 | No hay sesión válida. | «Inicie sesión para continuar» |
| 2 | 404 | El recurso no existe **o** no es visible para ese usuario según la matriz 2.3. | «No encontrado» |
| 3 | 403 | El recurso es visible, pero el rol no tiene permiso para esa acción. | «No tiene permiso para esta acción» |
| 4 | 409 | La acción no está permitida desde el estado actual. | «Transición no permitida» (o el mensaje del criterio) |
| 5 | 422 | Un dato no cumple una validación. | El mensaje que indica cada criterio, con el nombre del campo |

---

### 3.1 Requerimientos funcionales

#### RF-01 · Autenticación por rol

El sistema permite iniciar sesión con correo y contraseña a los usuarios activos y da a cada uno solo las funciones de su rol: Residente, Vigilancia, Mantenimiento o Administración.

- **RF-01-AC-1.** **Dado que** existe un usuario activo con rol Residente y contraseña válida, **cuando** inicia sesión con ese correo y esa contraseña, **entonces** el sistema responde con una sesión válida que indica el rol Residente y la unidad `B-502`.
- **RF-01-AC-2.** **Dado que** un usuario escribe una contraseña incorrecta, **cuando** intenta iniciar sesión, **entonces** el sistema responde 401 con el mensaje «Correo o contraseña incorrectos», sin indicar cuál de los dos falló.
- **RF-01-AC-3.** **Dado que** el inquilino de `B-502` tiene sesión iniciada y existe el reporte `RY-000124` de su unidad, **cuando** intenta asignarlo, **entonces** el sistema responde 403 y el reporte no cambia.
- **RF-01-AC-4.** **Dado que** el Vigilante tiene sesión iniciada y registró el reporte `RY-000125`, **cuando** intenta cerrarlo o asignarlo, **entonces** el sistema responde 403 y el reporte no cambia.

#### RF-02 · Padrón: unidades, áreas comunes, usuarios y proveedores

La Administración puede dar de alta, editar y desactivar:

- **Unidades**, con torre, piso, número y propietario (nombre y correo obligatorios), e indicación de si el propietario vive o no en el condominio. El propietario que no vive ahí no tiene cuenta.
- **Áreas comunes**, con nombre.
- **Usuarios** con rol Residente, Vigilancia, Mantenimiento o Administración. Un Residente se vincula a una sola unidad con su ocupación (propietario o inquilino) y una fecha de inicio de vinculación. Un usuario de Mantenimiento tiene tipo «Personal propio» o «Proveedor externo»; el proveedor lleva además especialidad y teléfono.
- **Proveedores externos sin acceso**: contacto asignable (nombre, especialidad, teléfono) sin cuenta.

Toda cuenta la crea la Administración; nadie se registra por su cuenta (EX-08).

- **RF-02-AC-1.** **Dado que** existe la unidad `B-502`, **cuando** la Administración da de alta un usuario Residente con ocupación «Inquilino» vinculado a `B-502`, **entonces** el usuario queda «Pendiente de activación» y se envía el enlace de RF-14-AC-1.
- **RF-02-AC-2.** **Dado que** ya existe un usuario con el correo `inquilino@ejemplo.com`, **cuando** la Administración da de alta otro con ese correo, **entonces** el sistema responde 422 con el mensaje «El correo ya está registrado» y no crea el usuario.
- **RF-02-AC-3.** **Dado que** el inquilino de `B-502` fue desactivado, **cuando** intenta iniciar sesión con su contraseña correcta, **entonces** el sistema responde 401, y sus reportes anteriores siguen visibles para la Administración.
- **RF-02-AC-4.** **Dado que** no existe el usuario «Bombas del Norte», **cuando** la Administración lo da de alta con rol Mantenimiento, tipo «Proveedor externo», especialidad «Bombas y cisterna» y un teléfono, **entonces** queda «Pendiente de activación», se le envía el enlace de RF-14-AC-1 y aparece en la lista de responsables de RF-06.
- **RF-02-AC-5.** **Dado que** la Administración da de alta la unidad `C-101`, **cuando** omite el correo del propietario, **entonces** el sistema responde 422 con el mensaje «El correo del propietario es obligatorio».
- **RF-02-AC-6.** **Dado que** la Administración da de alta la unidad `C-102`, **cuando** omite el piso, **entonces** el sistema responde 422 con el mensaje «El piso es obligatorio».
- **RF-02-AC-7.** **Dado que** la Administración registra «Elevadores del Centro» como proveedor sin acceso, con especialidad «Elevadores» y teléfono, **cuando** guarda, **entonces** no se crea cuenta ni se envía enlace, y el proveedor aparece en la lista de responsables de RF-06 marcado «Sin acceso al sistema».
- **RF-02-AC-8.** **Dado que** la Administración da de alta un usuario con rol Vigilancia, **cuando** guarda, **entonces** el usuario queda «Pendiente de activación» y, una vez activo, solo ve las funciones de RF-04 (matriz 2.3).

#### RF-03 · Alta de reporte por el residente

El Residente registra un reporte con: categoría del catálogo (RD-01, obligatoria); subtipo (obligatorio en las categorías que lo definen); descripción de 10 a 1,000 caracteres (obligatoria); ubicación observada (su unidad o un área común; obligatoria); parte afectada o detalle de ubicación en texto libre de hasta 200 caracteres (opcional); respuesta «Sí/No» a «¿El problema es peligroso o está empeorando?» (obligatoria); «¿Autoriza el acceso a su departamento para revisar la falla?» y horarios en que hay alguien para dar acceso (la autorización es obligatoria solo si la ubicación es su unidad; los horarios son opcionales); «desde cuándo pasa» y «si ya había pasado antes» (opcionales); de 0 a 5 fotografías y 1 video opcional (RF-05). El sistema asigna el folio siguiente, fija la fecha de aviso igual a la fecha y hora de alta, registra el medio de origen «Sistema» y deja el reporte en `Reportado`.

- **RF-03-AC-1.** **Dado que** el último folio emitido es `RY-000123` y el inquilino de `B-502` tiene sesión iniciada, **cuando** registra un reporte con categoría «Iluminación», subtipo «Pasillo o área techada», ubicación «Rampa del estacionamiento», descripción «Lámpara parpadeando cerca de la entrada» y peligro «No», **entonces** el sistema crea el reporte `RY-000124` en `Reportado`, con fecha de aviso igual a la hora del sistema y medio de origen «Sistema».
- **RF-03-AC-2.** **Dado que** el inquilino de `B-502` tiene sesión iniciada, **cuando** envía un reporte con la descripción «Fuga» (4 caracteres), **entonces** el sistema responde 422 con el mensaje «La descripción debe tener entre 10 y 1,000 caracteres» y no crea el reporte.
- **RF-03-AC-3.** **Dado que** el inquilino de `B-502` elige como ubicación su unidad, **cuando** envía el reporte sin responder la autorización de acceso, **entonces** el sistema responde 422 con el mensaje «Indique si autoriza el acceso a su departamento».
- **RF-03-AC-4.** **Dado que** el inquilino de `B-502` tiene sesión iniciada, **cuando** intenta registrar un reporte con ubicación en la unidad `A-301`, **entonces** el sistema responde 422 con el mensaje «Solo puede reportar en su unidad o en áreas comunes».
- **RF-03-AC-5 [UI].** **Dado que** el residente llenó el formulario y el sistema respondió con un error de validación, **cuando** se muestra el error, **entonces** los datos que ya había capturado siguen en el formulario.
- **RF-03-AC-6.** **Dado que** el inquilino de `B-502` completó los datos obligatorios, **cuando** envía el reporte sin responder si el problema es peligroso o está empeorando, **entonces** el sistema responde 422 con el mensaje «Indique si el problema es peligroso o está empeorando» y no crea el reporte.
- **RF-03-AC-7.** **Dado que** el inquilino de `B-502` completó los datos obligatorios, **cuando** envía el reporte sin ninguna fotografía, **entonces** el sistema crea el reporte; y **[UI]** antes de enviar, la interfaz le muestra la solicitud de adjuntar fotografías.
- **RF-03-AC-8.** **Dado que** el inquilino de `B-502` reporta un problema dentro de su unidad, **cuando** indica la parte afectada «Baño» y envía el reporte, **entonces** el reporte queda con torre, piso, número de unidad y parte afectada.
- **RF-03-AC-9.** **Dado que** el inquilino de `B-502` completó los datos obligatorios, **cuando** envía el reporte sin «desde cuándo pasa», sin «si ya había pasado antes» y sin horarios de acceso, **entonces** el sistema crea el reporte; y cuando sí los indica, quedan guardados.
- **RF-03-AC-10.** **Dado que** el inquilino de `B-502` elige la categoría «Iluminación», **cuando** envía el reporte sin subtipo, **entonces** el sistema responde 422 con el mensaje «Indique el subtipo».

#### RF-04 · Captura de reportes en nombre de terceros

La Administración y Vigilancia registran un reporte recibido por otro medio o a nombre de un residente que no usa el sistema. Aplican los mismos campos obligatorios de RF-03, más: el medio de origen («WhatsApp», «Llamada», «Caseta», «Correo» o «Presencial»); la fecha y hora de aviso; y, opcionalmente, el **residente reportante** (usuario Residente). Si se indica residente reportante, el reporte se comporta como si él lo hubiera registrado: lo ve en RF-10, recibe los avisos de RF-11 y puede confirmar según RF-09. Si no se indica, el reportante queda «Sin cuenta», con un nombre de referencia obligatorio y un dato de contacto opcional. El sistema guarda siempre quién hizo la captura.

- **RF-04-AC-1.** **Dado que** el guardia avisó a la Administración el 20/09/2026 a las 22:10 de una luminaria fundida en «Rampa del estacionamiento», **cuando** la Administración captura el reporte el 21/09/2026 a las 09:00 con medio «Caseta» y fecha de aviso 20/09/2026 22:10, **entonces** el reporte queda con esa fecha de aviso, fecha de captura 21/09/2026 09:00 y medio «Caseta», y sus tiempos (RF-13) se calculan desde el 20/09/2026 22:10.
- **RF-04-AC-2.** **Dado que** la hora del sistema es 21/09/2026 09:00, **cuando** la Administración captura un reporte con fecha de aviso 21/09/2026 10:00, **entonces** el sistema responde 422 con el mensaje «La fecha del aviso no puede ser futura».
- **RF-04-AC-3.** **Dado que** el inquilino de `B-502` avisó por WhatsApp de una fuga en su unidad, **cuando** la Administración captura el reporte con residente reportante «inquilino de `B-502`», **entonces** el reporte aparece en la lista del inquilino (RF-10) y el inquilino recibe el aviso de alta (RF-11-AC-1).
- **RF-04-AC-4.** **Dado que** la Administración captura un reporte con ubicación `B-502`, **cuando** no indica la autorización de acceso, **entonces** el sistema responde 422 con el mensaje «Indique si el ocupante autoriza el acceso».
- **RF-04-AC-5.** **Dado que** el Vigilante registra un reporte a nombre del residente de `A-301`, **cuando** se consulta el reporte como Administración, **entonces** aparecen conservados el residente reportante `A-301` y el Vigilante como quien capturó.
- **RF-04-AC-6.** **Dado que** la Administración captura un reporte sin residente reportante y sin nombre de referencia, **cuando** intenta guardarlo, **entonces** el sistema responde 422 con el mensaje «Indique el nombre de quien reporta».
- **RF-04-AC-7.** **Dado que** el Vigilante tiene sesión iniciada, **cuando** consulta sus reportes, **entonces** ve únicamente los que él registró.
- **RF-04-AC-8.** **Dado que** el inquilino de `B-502` tiene sesión iniciada, **cuando** intenta usar la captura en nombre de terceros, **entonces** el sistema responde 403.
- **RF-04-AC-9.** **Dado que** la Administración captura un reporte con ubicación `B-502` a nombre del inquilino, **cuando** no responde si el problema es peligroso o está empeorando, **entonces** el sistema responde 422 con el mensaje «Indique si el problema es peligroso o está empeorando».

#### RF-05 · Fotografías y video

El sistema acepta fotografías JPEG o PNG de hasta 10 MB cada una, en dos momentos: al alta del reporte (RF-03 o RF-04; de 0 a 5 fotos, etapa «Alta») y al marcar `Terminado` (RF-08; de 1 a 5 fotos por ciclo, etapa «Evidencia»). Al alta se puede adjuntar además un video MP4 de hasta 50 MB. No se agregan archivos en otro momento. Cada archivo se valida por separado: los válidos se guardan y los inválidos se reportan uno por uno. Ningún archivo se puede borrar (RNF-07).

- **RF-05-AC-1.** **Dado que** el inquilino de `B-502` registra un reporte, **cuando** adjunta 3 fotografías JPEG de 4 MB cada una, **entonces** las tres quedan en la etapa «Alta».
- **RF-05-AC-2.** **Dado que** el inquilino de `B-502` registra un reporte, **cuando** adjunta una foto JPEG de 4 MB y un archivo PDF, **entonces** el reporte se crea con la foto y la respuesta indica, para el PDF, «Formato no permitido: use JPEG o PNG».
- **RF-05-AC-3.** **Dado que** el inquilino de `B-502` registra un reporte, **cuando** adjunta una foto de 12 MB, **entonces** la respuesta indica para ese archivo «La foto supera 10 MB» y no la guarda.
- **RF-05-AC-4.** **Dado que** el inquilino de `B-502` registra un reporte, **cuando** adjunta 6 fotografías válidas, **entonces** el sistema responde 422 con el mensaje «Máximo 5 fotografías por etapa» y no crea el reporte.
- **RF-05-AC-5.** **Dado que** el inquilino de `B-502` registra un reporte, **cuando** adjunta un video MP4 de 30 MB, **entonces** el video queda asociado al reporte y se puede consultar desde él.
- **RF-05-AC-6.** **Dado que** el inquilino de `B-502` registra un reporte, **cuando** adjunta un video de 60 MB, **entonces** la respuesta indica para ese archivo «El video supera 50 MB» y no lo guarda.
- **RF-05-AC-7.** **Dado que** existe un reporte con fotografías, **cuando** cualquier usuario, incluida la Administración, intenta borrar una de ellas, **entonces** el sistema responde 403 y la fotografía sigue guardada.

#### RF-06 · Prioridad, responsabilidad, asignación y reclasificación

Al dar de alta un reporte, el sistema **sugiere** una prioridad a partir de la categoría y el subtipo (RD-01); si el reportante respondió «Sí» al peligro, la sugerida es `Urgente`. La Administración confirma o cambia la prioridad; la decisión final es solo suya (RD-10) y el sistema nunca la revierte a la sugerida.

La Administración asigna a un reporte en `Reportado`: prioridad (obligatoria), responsable (obligatorio; un solo usuario de Mantenimiento o un proveedor externo con o sin acceso), ubicación de origen (si difiere de la observada), responsabilidad (`Común`, `Privada` o `Por determinar`; por defecto `Por determinar`) y responsable del costo (RD-03). Al guardar, el reporte pasa a `Asignado`. En `Asignado`, `En proceso` o `Terminado` la Administración puede **reclasificar** cualquiera de esos datos sin cambiar el estado, y la reasignación del responsable es posible solo en `Asignado` o `En proceso`. Cada asignación y reclasificación queda en el historial con valor anterior, valor nuevo, usuario y fecha.

- **RF-06-AC-1.** **Dado que** `RY-000124` está en `Reportado`, **cuando** la Administración asigna prioridad «Urgente» y responsable «Conserje», **entonces** el reporte pasa a `Asignado`, aparece en la lista del Conserje (RF-16) y el historial registra el cambio con usuario, fecha y hora.
- **RF-06-AC-2.** **Dado que** un reporte de fuga tiene ubicación observada `A-402`, **cuando** la Administración registra ubicación de origen `A-502` y responsable del costo «Propietario de A-502», **entonces** ambos datos quedan guardados y el reporte aparece al buscar por `A-402` y por `A-502` (RF-12-AC-2).
- **RF-06-AC-3.** **Dado que** `RY-000124` está en `Reportado`, **cuando** la Administración intenta asignarlo sin prioridad, **entonces** el sistema responde 422 con el mensaje «La prioridad es obligatoria» y el estado no cambia.
- **RF-06-AC-4.** **Dado que** `RY-000124` está `En proceso` asignado al Conserje, **cuando** la Administración lo reclasifica con responsable «Bombas del Norte», **entonces** el estado sigue en `En proceso`, el reporte sale de la lista del Conserje y el historial muestra «Responsable: Conserje → Bombas del Norte».
- **RF-06-AC-5.** **Dado que** se crea un reporte de categoría «Iluminación» con subtipo «Pasillo o área techada» y peligro «No», **cuando** se guarda, **entonces** la prioridad sugerida es «Normal».
- **RF-06-AC-6.** **Dado que** se crea un reporte de categoría «Iluminación» con subtipo «Jardín o exterior» y peligro «No», **cuando** se guarda, **entonces** la prioridad sugerida es «Menor».
- **RF-06-AC-7.** **Dado que** se crea un reporte de categoría «Plomería y fugas» con subtipo «Fuga activa», **cuando** se guarda, **entonces** la prioridad sugerida es «Urgente»; y **dado que** se crea uno de «Iluminación», subtipo «Jardín o exterior», con peligro «Sí», **entonces** la sugerida es «Urgente».
- **RF-06-AC-8.** **Dado que** un reporte tiene prioridad sugerida «Normal», **cuando** la Administración la cambia a «Urgente» y guarda, **entonces** el reporte conserva «Urgente» y el historial registra el cambio.
- **RF-06-AC-9.** **Dado que** `RY-000124` está `Asignado` con responsabilidad «Por determinar», **cuando** la Administración la reclasifica como «Privada», **entonces** el sistema registra la determinación, avisa al reportante (RF-11) y el estado no cambia.
- **RF-06-AC-10.** **Dado que** `RY-000124` está en `Reportado`, **cuando** la Administración lo asigna al proveedor «Elevadores del Centro» (sin acceso), **entonces** el reporte pasa a `Asignado` con ese responsable y no se genera aviso a ningún usuario de Mantenimiento.

#### RF-07 · Flujo de estados

El sistema aplica solo estas transiciones, con estos roles:

| De | A | Quién | Condición |
|---|---|---|---|
| `Reportado` | `Asignado` | Administración | RF-06 |
| `Reportado` o `Asignado` | `Cancelado` | Administración | Motivo obligatorio |
| `Reportado` o `Asignado` | `Cancelado` | Residente que registró el reporte | Motivo fijo «Ya se resolvió» |
| `Reportado` o `Asignado` | `Unido` | Administración | RF-17 |
| `Asignado` | `En proceso` | Mantenimiento asignado o Administración | — |
| `En proceso` | `Terminado` | Mantenimiento asignado o Administración | RF-08 |
| `Terminado` | `Cerrado` | Administración | RF-09 |
| `Terminado` | `En proceso` | Administración | Reapertura; comentario obligatorio; ciclo nuevo |
| `Cerrado` | `En proceso` | Administración | RF-19 |

Para un proveedor externo sin acceso, la Administración registra las transiciones en su nombre; el historial indica el usuario interno y el proveedor. `Cancelado` y `Unido` son estados finales. `Cerrado` solo admite la reapertura de RF-19. Un reporte `En proceso` no se cancela: se termina o se reclasifica. Cada transición guarda estado anterior, estado nuevo, usuario, fecha y hora, y comentario.

- **RF-07-AC-1.** **Dado que** `RY-000124` está en `Asignado` al Conserje, **cuando** el Conserje lo pasa a `En proceso`, **entonces** el historial muestra «Asignado → En proceso», el nombre del Conserje, y la fecha y hora.
- **RF-07-AC-2.** **Dado que** `RY-000124` está en `Reportado`, **cuando** la Administración intenta pasarlo a `Terminado`, **entonces** el sistema responde 409 con el mensaje «Transición no permitida» y el estado no cambia.
- **RF-07-AC-3.** **Dado que** un reporte está en `Cancelado` y otro en `Unido`, **cuando** la Administración intenta cambiar el estado de cualquiera de los dos, **entonces** el sistema responde 409 en ambos casos.
- **RF-07-AC-4.** **Dado que** `RY-000124` está asignado al Conserje y existe otro usuario de Mantenimiento, **cuando** ese otro usuario intenta pasarlo a `En proceso`, **entonces** el sistema responde 404, porque el reporte no es visible para él.
- **RF-07-AC-5.** **Dado que** `RY-000124` está en `Asignado`, **cuando** la Administración lo cancela sin motivo, **entonces** el sistema responde 422 con el mensaje «El motivo es obligatorio»; y **cuando** lo cancela con el motivo «Falsa alarma», el reporte pasa a `Cancelado`.
- **RF-07-AC-6.** **Dado que** el inquilino de `B-502` registró `RY-000124` y está en `Asignado`, **cuando** lo cancela con el motivo «Ya se resolvió», **entonces** el reporte pasa a `Cancelado`, el historial guarda el motivo y el usuario, y se avisa según RF-11-AC-6.
- **RF-07-AC-7.** **Dado que** el inquilino de `B-502` registró `RY-000124` y está `En proceso`, **cuando** intenta cancelarlo, **entonces** el sistema responde 409 con el mensaje «Transición no permitida».
- **RF-07-AC-8.** **Dado que** el residente de `A-301` registró el reporte `RY-000130`, **cuando** el inquilino de `B-502` intenta cancelarlo, **entonces** el sistema responde 404.
- **RF-07-AC-9.** **Dado que** el inquilino de `B-502` registró `RY-000124` y está en `Asignado`, **cuando** intenta cancelarlo con un motivo distinto de «Ya se resolvió», **entonces** el sistema responde 422 con el mensaje «Solo puede cancelar un reporte que ya se resolvió».
- **RF-07-AC-10.** **Dado que** un reporte está asignado al proveedor sin acceso «Elevadores del Centro» y está `Asignado`, **cuando** la Administración lo pasa a `En proceso` con el comentario «El proveedor confirmó que ya inició», **entonces** el estado cambia y el historial muestra al usuario de la Administración y al proveedor en cuyo nombre se registró.

#### RF-08 · Terminado con evidencia

Para pasar un reporte a `Terminado` se adjuntan de 1 a 5 fotografías de evidencia del ciclo actual (RF-05). La nota del trabajo realizado es opcional, de hasta 1,000 caracteres, para no obligar a escribir a quien no acostumbra hacerlo. **Excepción (RD-09):** si el responsable es un proveedor externo sin acceso y la Administración registra el avance en su nombre, puede pasar a `Terminado` sin fotografías si captura una justificación obligatoria; el reporte queda marcado «Terminado sin evidencia fotográfica» para auditoría. Registrar `Terminado` nunca cierra el reporte.

- **RF-08-AC-1.** **Dado que** `RY-000124` está `En proceso` asignado al Conserje, **cuando** el Conserje adjunta una foto de la lámpara reparada, sin nota, **entonces** el reporte pasa a `Terminado` y la foto queda en la etapa «Evidencia», separada de las fotos del alta.
- **RF-08-AC-2.** **Dado que** `RY-000124` está `En proceso` asignado al Conserje, **cuando** el Conserje intenta marcarlo como `Terminado` sin fotografías, **entonces** el sistema responde 422 con el mensaje «Adjunte al menos una foto del trabajo terminado» y el reporte permanece `En proceso`.
- **RF-08-AC-3.** **Dado que** `RY-000124` fue reabierto y ya tiene 5 fotos de evidencia del primer ciclo, **cuando** el Conserje lo marca otra vez como `Terminado` con 2 fotos nuevas, **entonces** el sistema acepta las 2 y el detalle muestra las evidencias agrupadas por ciclo.
- **RF-08-AC-4.** **Dado que** un reporte está `En proceso` asignado al proveedor sin acceso «Elevadores del Centro», **cuando** la Administración lo marca `Terminado` sin fotografías y con la justificación «El proveedor entregó solo la orden de servicio firmada», **entonces** el reporte pasa a `Terminado` y queda marcado «Terminado sin evidencia fotográfica».
- **RF-08-AC-5.** **Dado que** un reporte está `En proceso` asignado al proveedor sin acceso, **cuando** la Administración lo marca `Terminado` sin fotografías y sin justificación, **entonces** el sistema responde 422 con el mensaje «Escriba la justificación» y el estado no cambia.
- **RF-08-AC-6.** **Dado que** un reporte está `En proceso` asignado al Conserje, **cuando** se intenta marcar `Terminado` sin fotografías aunque se incluya una justificación, **entonces** el sistema responde 422 con el mensaje «Adjunte al menos una foto del trabajo terminado», porque la excepción no aplica al personal propio.
- **RF-08-AC-7.** **Dado que** el Conserje tiene un reporte `En proceso`, **cuando** lo marca `Terminado` e indica que solo se atendió lo urgente, con una descripción de lo pendiente, **entonces** la descripción de lo pendiente queda en el historial y el reporte queda `Terminado`, sin cerrarse.

#### RF-09 · Confirmación del residente y cierre

Cuando un reporte pasa a `Terminado`, su residente reportante (RF-03, o el indicado en RF-04) puede responder **una vez por ciclo** «Ya quedó» o «Sigue fallando» (con comentario obligatorio), dentro de las **72 horas** siguientes. El plazo se reinicia cada vez que el reporte vuelve a `Terminado`. Pasado el plazo ya no puede responder en ese ciclo. El plazo es un parámetro configurable (RF-27).

La Administración cierra (`Terminado → Cerrado`) solo si se cumple una condición: (a) el residente respondió «Ya quedó»; (b) pasaron 72 horas sin respuesta; (c) la ubicación observada es un área común; (d) el reporte no tiene residente reportante con cuenta. Si el residente respondió «Sigue fallando», la Administración puede reabrir, o cerrar con un comentario obligatorio. Solo la Administración cierra (RD-04).

- **RF-09-AC-1.** **Dado que** el reporte de `B-502` pasó a `Terminado` el 22/09/2026 a las 10:00, **cuando** el inquilino responde «Ya quedó» el 22/09/2026 a las 18:00, **entonces** el sistema registra la respuesta y la Administración puede cerrarlo.
- **RF-09-AC-2.** **Dado que** el reporte de `B-502` pasó a `Terminado` el 22/09/2026 a las 10:00 y el inquilino no ha respondido, **cuando** la Administración intenta cerrarlo el 22/09/2026 a las 20:00, **entonces** el sistema responde 409 con el mensaje «Esperando confirmación del residente hasta el 25/09/2026 10:00».
- **RF-09-AC-3.** **Dado que** el reporte de `B-502` pasó a `Terminado` el 22/09/2026 a las 10:00, **cuando** el inquilino intenta responder el 25/09/2026 a las 10:01, **entonces** el sistema responde 409 con el mensaje «El plazo para responder terminó».
- **RF-09-AC-4.** **Dado que** el inquilino respondió «Sigue fallando» con el comentario «Volvió a gotear», **cuando** la Administración intenta cerrar sin comentario, **entonces** el sistema responde 422 con el mensaje «Escriba el motivo del cierre».
- **RF-09-AC-5.** **Dado que** el inquilino respondió «Sigue fallando», **cuando** la Administración reabre el reporte con el comentario «Se revisará de nuevo la tubería», **entonces** el reporte pasa a `En proceso` con el mismo folio, inicia un ciclo nuevo y el historial conserva la respuesta del residente.
- **RF-09-AC-6.** **Dado que** el reporte de la «Rampa del estacionamiento» pasó a `Terminado` hace 1 hora, **cuando** la Administración lo cierra, **entonces** el reporte pasa a `Cerrado`, porque es de un área común.
- **RF-09-AC-7.** **Dado que** un reporte está `Terminado` y asignado al Conserje, **cuando** el Conserje intenta cerrarlo, **entonces** el sistema responde 403 y el reporte sigue `Terminado`.
- **RF-09-AC-8.** **Dado que** un reporte de `B-502` está `Terminado`, **cuando** el inquilino que lo registró intenta cerrarlo, **entonces** el sistema responde 403 y el reporte sigue `Terminado`.
- **RF-09-AC-9.** **Dado que** un reporte registrado por la Administración tiene reportante «Sin cuenta» y está `Terminado`, **cuando** la Administración lo cierra, **entonces** el reporte pasa a `Cerrado`, porque no hay residente que confirme.

#### RF-10 · Consulta de estado por el residente

El Residente ve: los reportes de su unidad cuya fecha de aviso sea igual o posterior a su fecha de inicio de vinculación, los que él reportó, y todos los de áreas comunes. Para cada reporte: folio, categoría, estado actual, fecha programada de visita (RF-15), motivo de detención si está detenido (RF-18), indicación de «unido a» si aplica (RF-17) y fecha de cada cambio de estado. Los reportes de áreas comunes se muestran sin el nombre ni la unidad de quien reportó, y ninguna consulta incluye teléfonos ni correos de otras personas.

- **RF-10-AC-1.** **Dado que** el inquilino de `B-502` reportó 2 fallas en su unidad y otros residentes reportaron 3 fallas en áreas comunes, **cuando** consulta su lista, **entonces** recibe esos 5 reportes, cada uno con su estado actual y la fecha de cada cambio.
- **RF-10-AC-2.** **Dado que** existe el reporte `RY-000130` de la unidad `A-301`, **cuando** el inquilino de `B-502` lo solicita por su folio, **entonces** el sistema responde 404.
- **RF-10-AC-3.** **Dado que** el residente de `A-301` reportó la luminaria de la rampa, **cuando** el inquilino de `B-502` consulta ese reporte, **entonces** recibe categoría, descripción, estado y fechas, pero no el nombre ni la unidad del reportante.
- **RF-10-AC-4.** **Dado que** un inquilino anterior de `B-502` reportó una fuga el 01/03/2026 y el inquilino actual se vinculó a `B-502` el 01/06/2026, **cuando** el inquilino actual consulta su lista, **entonces** ese reporte no aparece.
- **RF-10-AC-5.** **Dado que** el reporte del inquilino de `B-502` fue unido al reporte principal `RY-000150` (RF-17), **cuando** el inquilino consulta su lista, **entonces** ve su reporte con la indicación «Unido a RY-000150» y el estado del reporte principal.
- **RF-10-AC-6.** **Dado que** un reporte del inquilino de `B-502` está detenido con el motivo «Espera de pieza», **cuando** el inquilino lo consulta, **entonces** ve que está detenido y el motivo.

#### RF-11 · Avisos

El sistema envía, en los eventos de la tabla, un correo a los destinatarios y, cuando tienen cuenta, también un aviso dentro del sistema. Si el reportante no tiene canal digital (reportante «Sin cuenta»), el aviso se dirige a la Administración, que lo comunica manualmente. **No se avisa al residente** por el paso a `En proceso` ni por notas de avance internas.

| Evento | Destinatarios |
|---|---|
| Alta de un reporte (RF-03 o RF-04) | Residente reportante, si lo hay; Administración (reporte nuevo) |
| Asignación o reclasificación de responsable | Ese usuario de Mantenimiento, si tiene cuenta |
| Cambio de estado a `Asignado`, `Terminado`, `Cerrado`, `Cancelado` o `Unido`, o reapertura | Residente reportante; y, si la ubicación observada es una unidad, el propietario de esa unidad cuando no es el reportante |
| Reporte marcado o reanudado como detenido (RF-18); responsabilidad reclasificada (RF-06) | Residente reportante |
| Cancelación por el residente (RF-07) | Administración y responsable asignado, si lo hay |
| Cambio de la fecha programada de visita (RF-15) | Los mismos que en «cambio de estado» |
| Reporte estancado (RF-22) | Administración |
| Unión de reportes (RF-17) | Residentes reportantes de los reportes unidos |

Si el envío de un correo falla, el sistema reintenta hasta 3 veces con 10 minutos entre intentos. Si los 3 fallan, el correo queda «Fallido» y es visible para la Administración. El fallo del correo nunca impide guardar el cambio que lo originó. Cada envío deja constancia (canal, fecha y hora) en el historial del reporte.

- **RF-11-AC-1.** **Dado que** el inquilino de `B-502` tiene sesión iniciada, **cuando** registra un reporte, **entonces** recibe un aviso en el sistema y un correo con el folio y la fecha de aviso, y la Administración recibe el aviso de reporte nuevo.
- **RF-11-AC-2.** **Dado que** el inquilino de `B-502` reportó una fuga en su unidad y el propietario de `B-502` no vive en el condominio, **cuando** la Administración pasa el reporte a `Asignado`, **entonces** el inquilino recibe aviso en el sistema y correo, y el propietario recibe solo un correo, porque no tiene cuenta, con el folio, el estado nuevo, la fecha y el responsable del costo.
- **RF-11-AC-3.** **Dado que** un reporte es de un área común, **cuando** cambia de estado, **entonces** solo se avisa al residente que lo reportó y no se envía correo a ningún propietario.
- **RF-11-AC-4.** **Dado que** el servicio de correo no responde, **cuando** un reporte cambia de estado, **entonces** el cambio se guarda, el aviso en el sistema se crea, y después de 3 intentos fallidos el correo aparece como «Fallido» en la lista de correos de la Administración.
- **RF-11-AC-5.** **Dado que** `RY-000124` está en `Reportado`, **cuando** la Administración lo asigna al Conserje, **entonces** el Conserje recibe un aviso en el sistema y un correo con el folio y la prioridad.
- **RF-11-AC-6.** **Dado que** `RY-000124` está en `Asignado` al Conserje y lo registró el inquilino de `B-502`, **cuando** el inquilino lo cancela con el motivo «Ya se resolvió», **entonces** el Conserje y la Administración reciben un aviso en el sistema y un correo con el folio y el motivo.
- **RF-11-AC-7.** **Dado que** `RY-000124` está `Asignado` y lo registró el inquilino de `B-502`, **cuando** el Conserje lo pasa a `En proceso`, **entonces** el inquilino no recibe ningún aviso por ese cambio.
- **RF-11-AC-8.** **Dado que** un reporte tiene reportante «Sin cuenta», **cuando** el reporte pasa a `Asignado`, **entonces** la Administración recibe un aviso que indica comunicarlo manualmente al reportante.
- **RF-11-AC-9.** **Dado que** el reporte de `B-502` quedó `Terminado`, **cuando** se envía el aviso, **entonces** el correo informa que puede responder «Ya quedó» o «Sigue fallando» hasta el vencimiento del plazo de RF-09.

#### RF-12 · Historial y búsqueda

La Administración busca reportes por cualquier combinación de: ubicación (observada u origen), categoría, estado, prioridad, responsable, medio de origen, rango de fechas de aviso y texto contenido en la descripción. Los resultados se ordenan por fecha de aviso, de la más reciente a la más antigua. El detalle muestra, por reporte: qué pasó, dónde, cuándo, qué se hizo, quién lo hizo, costo y pagador, fotos por etapa y ciclo, notas de avance y el historial completo, incluidos los reportes cerrados.

- **RF-12-AC-1.** **Dado que** existen 4 reportes de «Bombas y cisterna» con fechas de aviso 15/12/2025, 01/01/2026, 30/06/2026 23:30 y 01/07/2026, **cuando** la Administración filtra por esa categoría y el rango del 01/01/2026 al 30/06/2026, **entonces** recibe exactamente 2 reportes, el del 30/06/2026 primero y el del 01/01/2026 después.
- **RF-12-AC-2.** **Dado que** un reporte tiene ubicación observada `A-402` y de origen `A-502`, **cuando** la Administración busca por la ubicación `A-502`, **entonces** el reporte aparece en los resultados.
- **RF-12-AC-3.** **Dado que** un reporte cerrado tuvo una reapertura, **cuando** la Administración consulta su detalle, **entonces** recibe las fotos del alta y las de evidencia separadas por ciclo, y cada cambio de estado con usuario, fecha, hora y comentario.
- **RF-12-AC-4.** **Dado que** existen reportes con la palabra «gotera» en la descripción, **cuando** la Administración busca el texto «gotera», **entonces** recibe todos los reportes que lo contienen y ninguno que no.
- **RF-12-AC-5.** **Dado que** un usuario con rol Residente tiene sesión iniciada, **cuando** intenta usar la búsqueda de la Administración, **entonces** el sistema responde 403.

#### RF-13 · Tablero de tiempos, incidencias recurrentes y adopción

La Administración consulta, para un rango de fechas de aviso que elige:

1. número de reportes por estado y por categoría;
2. tiempo promedio de primera atención y de resolución por prioridad;
3. porcentaje de cumplimiento por prioridad, calculado por separado para cada objetivo de RD-02 (primera atención y resolución), en dos bloques: reportes de personal propio y reportes de proveedores externos. Un reporte cumple si alcanzó el hito dentro del objetivo; incumple si lo alcanzó tarde o si sigue sin alcanzarlo y el objetivo ya venció; si el objetivo aún no vence y no ha alcanzado el hito, queda fuera del cálculo;
4. lista de incidencias recurrentes, según la definición de 1.3;
5. tiempo que cada reporte estuvo detenido (RF-18), mostrado por separado y con los motivos registrados;
6. adopción: porcentaje de reportes con medio de origen «Sistema» frente al total.

Los reportes `Cancelado` y `Unido` no cuentan en promedios, cumplimiento, recurrencia ni adopción. Los porcentajes se redondean al entero. Las reaperturas se muestran como dato aparte y no crean un reporte nuevo.

- **RF-13-AC-1.** **Dado que** en septiembre de 2026 hubo 3 reportes «Urgente» de personal propio con tiempos de primera atención de 30, 50 y 130 minutos y tiempos de resolución de 10, 20 y 36 horas, **cuando** la Administración consulta el tablero del 01/09/2026 al 30/09/2026, **entonces** ve: primera atención promedio 70 minutos y cumplimiento 67 % (2 de 3 dentro de 1 hora); resolución promedio 22 horas y cumplimiento 67 % (2 de 3 dentro de 24 horas).
- **RF-13-AC-2.** **Dado que** la fecha de consulta es 03/10/2026 y existen 3 reportes de «Iluminación» con origen «Rampa del estacionamiento» y fechas de aviso 15/07/2026, 15/08/2026 y 20/09/2026, **cuando** la Administración consulta el tablero, **entonces** «Iluminación — Rampa del estacionamiento» aparece como incidencia recurrente con los 3 folios.
- **RF-13-AC-3.** **Dado que** existen 3 reportes de la misma categoría y ubicación de origen en los últimos 90 días y uno de ellos está `Cancelado`, **cuando** la Administración consulta el tablero, **entonces** esa combinación **no** aparece como incidencia recurrente.
- **RF-13-AC-4.** **Dado que** un reporte «Normal» tiene fecha de aviso 20/09/2026 10:00, no ha pasado a `Terminado` y la hora del sistema es 23/09/2026 11:00, **cuando** se calcula el cumplimiento de resolución, **entonces** ese reporte cuenta como incumplido, porque su objetivo de 72 horas venció el 23/09/2026 10:00.
- **RF-13-AC-5.** **Dado que** un reporte estuvo detenido del 10/09/2026 09:00 al 12/09/2026 09:00 con el motivo «Espera de pieza», **cuando** la Administración consulta el tablero de septiembre, **entonces** ve 48 horas de tiempo detenido para ese reporte, por separado, con el motivo.
- **RF-13-AC-6.** **Dado que** en octubre de 2026 se registraron 10 reportes, 6 con medio de origen «Sistema» y 4 capturados por WhatsApp, **cuando** la Administración consulta el tablero de octubre, **entonces** la adopción es 60 %.
- **RF-13-AC-7.** **Dado que** en septiembre de 2026 hubo 2 reportes asignados a «Bombas del Norte», **cuando** la Administración consulta el tablero de septiembre, **entonces** esos 2 reportes aparecen en el bloque de proveedores externos y no en el de personal propio.
- **RF-13-AC-8.** **Dado que** un usuario con rol Residente tiene sesión iniciada, **cuando** solicita el tablero, **entonces** el sistema responde 403.

#### RF-14 · Activación y recuperación de contraseña

Al dar de alta un usuario con cuenta (RF-02), el sistema le envía por correo un enlace de activación de un solo uso que vence en 72 horas, con el que define su contraseña. Cualquier usuario puede pedir un enlace de recuperación de un solo uso que vence en 1 hora. La primera cuenta de Administración se crea con un comando de arranque del despliegue, no desde la interfaz.

- **RF-14-AC-1.** **Dado que** la Administración dio de alta al inquilino de `B-502`, **cuando** el inquilino abre el enlace dentro de las 72 horas y define una contraseña válida, **entonces** su cuenta pasa a «Activa» y el enlace deja de funcionar.
- **RF-14-AC-2.** **Dado que** un enlace de activación se emitió el 20/09/2026 a las 10:00, **cuando** se usa el 23/09/2026 a las 10:01, **entonces** el sistema responde 422 con el mensaje «El enlace venció; pida uno nuevo a la Administración».
- **RF-14-AC-3.** **Dado que** el inquilino de `B-502` olvidó su contraseña, **cuando** pide la recuperación con su correo, **entonces** recibe un enlace que vence en 1 hora; y **cuando** se pide con un correo que no existe, la respuesta es la misma, para no revelar qué correos están registrados.
- **RF-14-AC-4.** **Dado que** la base de datos no tiene usuarios, **cuando** se ejecuta el comando de arranque con un correo de Administración, **entonces** se crea ese usuario con rol Administración y se le envía el enlace de activación.

#### RF-15 · Notas de avance y fecha programada de visita

La Administración y el Mantenimiento asignado agregan a un reporte en `Asignado` o `En proceso` notas de avance internas (de 1 a 500 caracteres, solo inserción, sin cambiar el estado) y la fecha programada de visita. La fecha es visible para el residente reportante, los residentes de la unidad (RF-10) y el propietario (en el correo de RF-11); las notas solo para la Administración y el Mantenimiento asignado.

- **RF-15-AC-1.** **Dado que** `RY-000124` está `En proceso` asignado al Conserje, **cuando** el Conserje agrega la nota «Falta la pieza; llega el jueves», **entonces** la nota queda en el historial con autor y fecha, y el estado sigue en `En proceso`.
- **RF-15-AC-2.** **Dado que** `RY-000124` está en `Asignado`, **cuando** la Administración fija la visita para el 29/09/2026 a las 10:00, **entonces** el inquilino de `B-502` ve esa fecha en su lista y recibe el aviso de RF-11.
- **RF-15-AC-3.** **Dado que** `RY-000124` tiene notas de avance, **cuando** el inquilino de `B-502` consulta el reporte, **entonces** la respuesta no incluye las notas.

#### RF-16 · Lista de reportes asignados para Mantenimiento

El usuario de Mantenimiento ve la lista de reportes asignados a él en `Asignado` o `En proceso`, ordenada por prioridad (Urgente, Normal, Menor) y, a igual prioridad, por fecha de aviso, del más antiguo al más reciente. Para cada reporte: folio, prioridad, categoría, ubicación observada y de origen, detalle de ubicación, autorización y horarios de acceso, fecha programada, marca de detenido con su motivo y fotos del alta.

- **RF-16-AC-1.** **Dado que** el Conserje tiene asignados un reporte «Normal» con aviso del 20/09/2026 y uno «Urgente» con aviso del 22/09/2026, **cuando** consulta su lista, **entonces** el «Urgente» aparece primero.
- **RF-16-AC-2.** **Dado que** existe un reporte asignado a «Bombas del Norte» y uno del Conserje ya `Cerrado`, **cuando** el Conserje consulta su lista, **entonces** ninguno de los dos aparece.
- **RF-16-AC-3.** **Dado que** el Conserje tiene dos reportes «Normal» con avisos del 18/09/2026 y del 21/09/2026, **cuando** consulta su lista, **entonces** el del 18/09/2026 aparece primero.
- **RF-16-AC-4.** **Dado que** el reporte de `B-502` tiene autorización de acceso «No», **cuando** el Conserje lo consulta, **entonces** ve el mensaje «Sin autorización de acceso: coordinar con la Administración».

#### RF-17 · Detección y unión de reportes duplicados

Al crear un reporte (RF-03 o RF-04), el sistema busca otro **abierto** (no `Cerrado`, `Cancelado` ni `Unido`) de la misma categoría y la misma ubicación: para unidades, mismo piso de la misma torre (o el nivel más específico común a ambos, por ejemplo, la misma unidad); para áreas comunes, la misma área. Si lo encuentra, el reporte **se crea de inmediato** (para no perder reportes), queda marcado «Posible duplicado de RY-XXXXXX» y se avisa a la Administración; cuando la captura la hace la propia Administración, la interfaz muestra la advertencia antes de confirmar. La Administración decide si los une. Solo el reporte más reciente, en `Reportado` o `Asignado`, puede pasar a `Unido`.

- **RF-17-AC-1.** **Dado que** existe el reporte abierto `RY-000150` de «Plomería y fugas» en torre B, piso 4, **cuando** se crea otro de «Plomería y fugas» en torre B, piso 4, **entonces** el nuevo se crea, queda marcado «Posible duplicado de RY-000150» y la Administración recibe el aviso.
- **RF-17-AC-2.** **Dado que** un reporte está marcado como posible duplicado, **cuando** la Administración decide que no es el mismo caso y lo confirma como independiente, **entonces** la marca se retira y los dos reportes siguen su flujo por separado.
- **RF-17-AC-3.** **Dado que** un reporte está marcado como posible duplicado, **cuando** la Administración lo une al reporte original, **entonces** el reporte más reciente pasa a `Unido`, deja de tener seguimiento independiente y queda enlazado al original con ambos historiales conservados.
- **RF-17-AC-4.** **Dado que** dos residentes reportaron la misma falla y sus reportes fueron unidos, **cuando** el reporte principal pasa a `Cerrado`, **entonces** ambos residentes reciben el aviso de cierre.
- **RF-17-AC-5.** **Dado que** existe el reporte abierto `RY-000150` en torre B, piso 4, **cuando** se crea otro de la misma categoría en torre B, piso 5, **entonces** el nuevo no se marca como posible duplicado.
- **RF-17-AC-6.** **Dado que** el único reporte de la misma categoría y ubicación está `Cerrado`, **cuando** se crea uno nuevo, **entonces** no se marca como posible duplicado.

#### RF-18 · Incidencia detenida

El responsable asignado o la Administración pueden marcar como detenido un reporte `Asignado` o `En proceso`, eligiendo un motivo del catálogo («Acceso al departamento», «Espera de proveedor», «Espera de pieza», «Espera de autorización de gasto», «Otro» con texto), y después reanudarlo. Detener no cambia el estado.

- **RF-18-AC-1.** **Dado que** `RY-000124` está `En proceso` asignado al Conserje, **cuando** el Conserje lo marca detenido con el motivo «Espera de pieza», **entonces** el reporte queda detenido con ese motivo, el estado sigue `En proceso` y el historial registra fecha, hora y usuario.
- **RF-18-AC-2.** **Dado que** `RY-000124` está `En proceso`, **cuando** el Conserje intenta marcarlo detenido sin motivo, **entonces** el sistema responde 422 con el mensaje «Indique el motivo de la detención».
- **RF-18-AC-3.** **Dado que** `RY-000124` está detenido, **cuando** el Conserje o la Administración lo reanuda, **entonces** deja de estar detenido y el historial registra la reanudación.
- **RF-18-AC-4.** **Dado que** `RY-000124` está en `Terminado`, **cuando** se intenta marcarlo detenido, **entonces** el sistema responde 409 con el mensaje «Transición no permitida».
- **RF-18-AC-5.** **Dado que** `RY-000124` fue marcado detenido, **cuando** se registra, **entonces** el residente reportante recibe el aviso de RF-11.

#### RF-19 · El problema persiste y reapertura de un reporte cerrado

El residente reportante puede indicar que el problema persiste en un reporte `Cerrado`, dentro de los **30 días** posteriores al cierre (parámetro configurable, RF-27). La indicación no reabre sola: la Administración decide. Si reabre, el mismo reporte vuelve a `En proceso` con su folio e historial y se inicia un ciclo nuevo; no se crea un reporte nuevo. Pasado el plazo, la Administración crea un reporte nuevo.

- **RF-19-AC-1.** **Dado que** el reporte de `B-502` se cerró el 01/10/2026 a las 10:00, **cuando** el inquilino indica el 10/10/2026 que el problema persiste, **entonces** el sistema registra la indicación y la Administración puede consultarla.
- **RF-19-AC-2.** **Dado que** el inquilino indicó que el problema persiste, **cuando** la Administración todavía no ha decidido, **entonces** el reporte sigue `Cerrado`.
- **RF-19-AC-3.** **Dado que** el reporte cerrado tiene trabajo, evidencia y acciones registradas, **cuando** la Administración lo reabre con el comentario «Sigue la humedad», **entonces** el reporte pasa a `En proceso` con el mismo folio, inicia un ciclo nuevo, conserva su historial y no se crea un reporte nuevo.
- **RF-19-AC-4.** **Dado que** el reporte se cerró el 01/10/2026 a las 10:00, **cuando** el inquilino intenta indicar que persiste el 31/10/2026 a las 10:01, **entonces** el sistema responde 409 con el mensaje «El plazo para reabrir terminó».
- **RF-19-AC-5.** **Dado que** la Administración reabre un reporte cerrado, **cuando** no escribe comentario, **entonces** el sistema responde 422 con el mensaje «Escriba el motivo de la reapertura».

#### RF-20 · Costo y pagador

La Administración puede registrar en cada reporte el **monto** del costo (en pesos mexicanos, mayor o igual a cero; opcional) y **quién pagó**: el condominio o el condómino. Puede registrarlo en cualquier estado, incluidos `Terminado` y `Cerrado`. La corrección de un dato ya capturado se registra como una entrada nueva que anula la anterior; la original se conserva (RNF-07). El sistema no cobra ni genera facturas (EX-01, EX-02).

- **RF-20-AC-1.** **Dado que** un reporte está registrado, **cuando** la Administración registra un costo de $2,500.00 pagado por el condominio, **entonces** el reporte queda con ese monto y con el condominio como pagador.
- **RF-20-AC-2.** **Dado que** un reporte es de una fuga en `B-502`, **cuando** la Administración registra un costo de $1,200.00 pagado por el condómino, **entonces** el reporte queda con ese monto y con el condómino como pagador.
- **RF-20-AC-3.** **Dado que** la Administración registra un costo, **cuando** el monto es negativo, **entonces** el sistema responde 422 con el mensaje «El monto no puede ser negativo».
- **RF-20-AC-4.** **Dado que** un reporte tiene un costo de $2,500.00, **cuando** la Administración lo corrige a $2,300.00, **entonces** el sistema guarda el valor nuevo como vigente y conserva el anterior con usuario y fecha en el historial.
- **RF-20-AC-5.** **Dado que** un reporte tiene costo registrado, **cuando** el inquilino de `B-502` consulta ese reporte, **entonces** la respuesta incluye el pagador pero no el monto.

#### RF-21 · Delegación temporal a la Auxiliar

El Administrador puede habilitar a la Auxiliar administrativa para asignar, reclasificar y cerrar reportes durante su ausencia, con una fecha de fin opcional, y deshabilitarla después. Sin una delegación vigente, la Auxiliar no puede asignar, reclasificar ni cerrar. La Auxiliar nunca modifica los parámetros (RF-27) ni autoriza gastos (RD-10). Sus acciones quedan registradas a su nombre. La delegación incluye también clasificar urgencia y responsabilidad (RD-10).

- **RF-21-AC-1.** **Dado que** el Administrador habilitó la delegación para la Auxiliar, **cuando** la Auxiliar asigna `RY-000124` al Conserje o cierra un reporte con trabajo terminado, **entonces** el sistema registra la asignación o el cierre.
- **RF-21-AC-2.** **Dado que** la delegación no está habilitada, **cuando** la Auxiliar intenta asignar o cerrar, **entonces** el sistema responde 403 y no registra la acción.
- **RF-21-AC-3.** **Dado que** la delegación estaba habilitada, **cuando** el Administrador la deshabilita, **entonces** la Auxiliar ya no puede asignar, reclasificar ni cerrar.
- **RF-21-AC-4.** **Dado que** la delegación está habilitada, **cuando** la Auxiliar realiza una asignación o un cierre, **entonces** el historial lo registra a nombre de la Auxiliar.
- **RF-21-AC-5.** **Dado que** la delegación tiene fecha de fin 05/10/2026 23:59, **cuando** la Auxiliar intenta asignar el 06/10/2026 a las 08:00, **entonces** el sistema responde 403.

#### RF-22 · Alerta de reporte estancado

El sistema avisa a la Administración cuando un reporte lleva más tiempo del umbral configurado **para su prioridad** sin cambiar de estado. No cuentan los reportes detenidos (RF-18), los `Terminado` que esperan la confirmación del residente (RF-09) ni los estados finales. El aviso se envía una sola vez hasta que el reporte cambie de estado. Valores iniciales de los umbrales: Urgente 2 h, Normal 24 h, Menor 72 h (configurables en RF-27).

- **RF-22-AC-1.** **Dado que** `RY-000140` es «Urgente», está en `Reportado` desde las 08:00 y el umbral es 2 horas, **cuando** la hora del sistema es 10:01, **entonces** la Administración recibe el aviso de que ese reporte no se ha movido.
- **RF-22-AC-2.** **Dado que** el aviso de `RY-000140` ya se envió, **cuando** pasa una hora más sin cambio de estado, **entonces** no se envía un segundo aviso.
- **RF-22-AC-3.** **Dado que** `RY-000141` lleva 30 horas en `En proceso` pero está detenido con el motivo «Espera de pieza», **cuando** se evalúan los umbrales, **entonces** no se genera aviso.
- **RF-22-AC-4.** **Dado que** el Administrador cambió el umbral «Normal» a 12 horas, **cuando** un reporte «Normal» lleva 13 horas sin cambiar de estado, **entonces** la Administración recibe el aviso.

#### RF-23 · Exportación del tablero

La Administración exporta el tablero (RF-13) de un periodo a un archivo imprimible (PDF) con tiempos promedio por prioridad, cumplimiento, incidencias recurrentes y adopción, apto para presentarse al comité o a la asamblea anual.

- **RF-23-AC-1.** **Dado que** la Administración consultó el tablero del 01/09/2026 al 30/09/2026, **cuando** solicita exportarlo, **entonces** el sistema genera un PDF con el periodo, el tiempo promedio de atención por prioridad, el cumplimiento y las incidencias recurrentes.
- **RF-23-AC-2.** **Dado que** el tablero de septiembre muestra una resolución promedio «Urgente» de 22 horas, **cuando** se exporta, **entonces** el PDF muestra las mismas cifras que la pantalla.
- **RF-23-AC-3.** **Dado que** un usuario con rol Residente tiene sesión iniciada, **cuando** solicita la exportación, **entonces** el sistema responde 403.

#### RF-24 · Identificación del propietario

La Administración identifica al propietario (nombre y correo) de la unidad de un reporte a partir del padrón de RF-02, sin pedírselo al inquilino que reporta.

- **RF-24-AC-1.** **Dado que** el inquilino de `B-502` registra un reporte sobre su unidad, **cuando** captura y envía el reporte, **entonces** el sistema no le pide datos del propietario.
- **RF-24-AC-2.** **Dado que** un reporte fue registrado por un inquilino sobre `B-502`, **cuando** la Administración consulta el reporte, **entonces** puede ver el nombre y el correo del propietario de `B-502`.
- **RF-24-AC-3.** **Dado que** un reporte de `B-502` existe, **cuando** el inquilino lo consulta, **entonces** la respuesta no incluye el nombre ni el correo del propietario.

#### RF-25 · Reparación con garantía

Al pasar un reporte a `Terminado`, el responsable o la Administración pueden marcarlo «con garantía» indicando la fecha de vencimiento. Esa marca extiende el periodo de retención de sus fotos (RNF-13).

- **RF-25-AC-1.** **Dado que** el Conserje marca `Terminado` el reporte `RY-000124` con evidencia, **cuando** lo marca «con garantía» hasta el 30/09/2027, **entonces** el reporte guarda la marca y la fecha de vencimiento.
- **RF-25-AC-2.** **Dado que** la hora del sistema es 03/10/2026, **cuando** se marca «con garantía» con vencimiento 01/10/2026, **entonces** el sistema responde 422 con el mensaje «La fecha de vencimiento no puede ser pasada».
- **RF-25-AC-3.** **Dado que** un reporte tiene garantía hasta el 30/09/2027, **cuando** la Administración consulta su detalle, **entonces** ve la marca y la fecha de vencimiento.

#### RF-26 · Corrección del reporte por el residente

Mientras el reporte esté en `Reportado`, el residente que lo registró puede corregir su categoría, subtipo, descripción, ubicación y detalle de ubicación. Cada corrección se guarda como una versión nueva y conserva la anterior (RNF-07). Desde `Asignado` solo la Administración puede modificar esos datos.

- **RF-26-AC-1.** **Dado que** `RY-000124` está en `Reportado`, **cuando** el inquilino que lo registró corrige la descripción, **entonces** el sistema guarda el cambio y registra la versión nueva en el historial.
- **RF-26-AC-2.** **Dado que** el inquilino corrigió la descripción, **cuando** la Administración consulta el historial, **entonces** ve la descripción original, la nueva, el usuario y la fecha.
- **RF-26-AC-3.** **Dado que** `RY-000124` está en `Asignado`, **cuando** el inquilino intenta corregir la descripción, **entonces** el sistema responde 409 con el mensaje «Transición no permitida».
- **RF-26-AC-4.** **Dado que** el residente de `A-301` registró `RY-000130`, **cuando** el inquilino de `B-502` intenta corregirlo, **entonces** el sistema responde 404.
- **RF-26-AC-5.** **Dado que** `RY-000124` está en `Reportado`, **cuando** el inquilino corrige el subtipo de «Jardín o exterior» a «Pasillo o área techada», **entonces** la prioridad sugerida se recalcula a «Normal».

#### RF-27 · Parámetros configurables

El Administrador puede consultar y modificar los parámetros del sistema que se muestran en la tabla. Un cambio se aplica a las consultas y evaluaciones posteriores y queda registrado (valor anterior, nuevo, usuario, fecha). La Auxiliar y los demás roles no pueden modificarlos.

| Parámetro | Valor inicial | Origen / estado |
|---|---|---|
| Objetivo de primera atención «Urgente» | 1 h | RD-02, entrevistas |
| Objetivo de resolución «Urgente» | 24 h | RD-02, entrevistas |
| Objetivo de resolución «Normal» | 72 h | RD-02. Contrastar con «3 a 5 días hábiles» de SRS-Base |
| Objetivo de resolución «Menor» | 168 h | RD-02, cliente simulado |
| Umbral de estancamiento Urgente / Normal / Menor | 2 h / 24 h / 72 h | RF-22 |
| Plazo de confirmación del residente | 72 h | RF-09 |
| Plazo para reabrir un reporte cerrado | 30 días | RF-19 |
| Ventana y mínimo de recurrencia | 90 días y 3 reportes | RD-02 / 1.3 |

- **RF-27-AC-1.** **Dado que** el Administrador tiene sesión iniciada, **cuando** cambia el objetivo de resolución «Urgente» de 24 a 12 horas, **entonces** el tablero (RF-13) usa 12 horas en las consultas posteriores y el cambio queda registrado con valor anterior, nuevo, usuario y fecha.
- **RF-27-AC-2.** **Dado que** el Administrador modifica un parámetro de tiempo, **cuando** captura un valor menor o igual a cero, **entonces** el sistema responde 422 con el mensaje «El valor debe ser mayor que cero» y conserva el valor vigente.
- **RF-27-AC-3.** **Dado que** la Auxiliar tiene sesión iniciada, **cuando** intenta modificar un parámetro, **entonces** el sistema responde 403.
- **RF-27-AC-4.** **Dado que** el Administrador cambia el plazo de confirmación del residente a 96 horas, **cuando** un reporte pasa a `Terminado`, **entonces** el plazo de RF-09 de ese ciclo es de 96 horas.

---

### 3.2 Requerimientos no funcionales

Cada RNF incluye su forma de verificación. Los RNF no se prueban con criterios Dado–Cuando–Entonces porque se prestan a pruebas de carga, resiliencia o auditoría.

- **RNF-01 · Compatibilidad móvil y web:** la interfaz se usa sin desplazamiento horizontal desde 360 px de ancho, en las dos versiones más recientes de Chrome para Android y Safari para iOS publicadas al 1 de octubre de 2026, sin instalar ninguna aplicación. La Administración también la usa desde computadora. Funciona en un Android de gama básica. | Categoría: usabilidad / portabilidad | Verificación: prueba manual en esos navegadores y en un equipo de gama básica.
- **RNF-02 · Facilidad de uso:** un residente registra un reporte con una fotografía en un máximo de 3 pantallas desde que inicia sesión, y el personal de mantenimiento termina un reporte en un máximo de 3 pantallas o pasos. | Categoría: usabilidad | Verificación: conteo de pasos y prueba con usuarios de poca experiencia digital.
- **RNF-03 · Rendimiento:** las consultas de RF-10, RF-12, RF-13 y RF-16 responden en 2 segundos o menos en el percentil 95, con 5,000 reportes en la base y 20 usuarios concurrentes; el sistema soporta hasta 100 reportes al mes sin degradación. | Categoría: rendimiento | Verificación: prueba de carga en un contenedor por servicio con 1 vCPU y 1 GB de memoria.
- **RNF-04 · Subida de fotografías:** una fotografía de 10 MB se sube en 15 segundos o menos con una conexión limitada a 10 Mbit/s. | Categoría: rendimiento | Verificación: limitación de red en el navegador.
- **RNF-05 · Control de acceso en el servidor:** el backend aplica la matriz de visibilidad (2.3) en cada petición y responde según el contrato de errores (3.0). Ninguna respuesta incluye datos que la matriz niega al usuario que los pide. Un residente tampoco puede modificar reportes ajenos. | Categoría: seguridad | Verificación: pruebas de API por rol.
- **RNF-06 · Seguridad de cuentas:** las contraseñas se almacenan con un hash con sal diseñado para contraseñas (bcrypt o Argon2) y tienen al menos 8 caracteres; todo el tráfico usa HTTPS; la sesión expira tras 30 minutos de inactividad; y una cuenta se bloquea 15 minutos después de 5 intentos fallidos consecutivos. | Categoría: seguridad | Verificación: pruebas de API y revisión de configuración.
- **RNF-07 · Historial inalterable:** el historial de estados, las reclasificaciones, las notas de avance, las versiones de corrección, los costos y las fotografías son de solo inserción. Ningún usuario, incluida la Administración, puede editarlos ni borrarlos. Una corrección se registra como entrada adicional que referencia y anula la incorrecta; la original nunca se elimina. Tampoco se pueden eliminar reportes. | Categoría: trazabilidad | Verificación: intentos de edición y borrado por API.
- **RNF-08 · Almacenamiento intercambiable:** los archivos se acceden mediante una sola interfaz con dos implementaciones, disco local y almacenamiento de objetos en la nube, seleccionables por configuración sin cambiar las reglas de negocio. | Categoría: mantenibilidad / portabilidad | Verificación: pruebas con ambas implementaciones.
- **RNF-09 · Accesibilidad:** el texto normal tiene una relación de contraste de al menos 4.5:1 (WCAG 2.1, nivel AA) y un tamaño base de 16 px. | Categoría: accesibilidad | Verificación: auditoría automatizada y revisión manual.
- **RNF-10 · Reloj controlable:** toda regla que depende del tiempo (plazos de RF-09, RF-14 y RF-19, vencimientos de RF-13, sesión y bloqueo de RNF-06, reintentos y umbrales de RF-22) obtiene la hora de un reloj del sistema que las pruebas automatizadas pueden fijar. | Categoría: verificabilidad | Verificación: las pruebas de AC fijan la hora.
- **RNF-11 · Tolerancia a mala conectividad:** si no hay conexión al enviar un reporte (RF-03, RF-04) o un registro de `Terminado` (RF-08), el sistema guarda lo capturado, incluidas las fotos, en el dispositivo y reintenta el envío automáticamente al recuperar señal, sin obligar al usuario a capturar de nuevo; el usuario distingue si el envío está «Pendiente» o «Enviado». Un reporte confirmado como enviado no se pierde. El personal de mantenimiento puede consultar en zonas sin señal el detalle de los reportes asignados que ya cargó en su dispositivo. | Categoría: fiabilidad | Verificación: prueba con el dispositivo sin conexión | **La viabilidad técnica la evalúa el equipo en diseño; si no es viable en 12 semanas, el requisito no se baja de nivel, se difiere explícitamente (sección 5, punto 15).**
- **RNF-12 · Disponibilidad:** el sistema está disponible también fuera del horario laboral, incluidos fines de semana, noches y picos de lluvia, con un objetivo de 99 % mensual. Las emergencias reales se atienden por teléfono (RD-12). | Categoría: disponibilidad | Verificación: monitoreo mensual.
- **RNF-13 · Retención de datos:** los reportes se conservan al menos 3 años y las fotografías al menos 1 año; las fotografías de reparaciones «con garantía» (RF-25) se conservan hasta el vencimiento de la garantía si es posterior a 1 año. El periodo para fotos de interiores de unidades se ajusta si la normativa de privacidad aplicable lo exige. | Categoría: retención | Verificación: revisión de la política y de la marca de garantía.
- **RNF-14 · Respaldo y recuperación:** el sistema mantiene respaldos al menos diarios de los reportes y su historial, y un respaldo acorde de las fotografías, con una política compatible con el presupuesto de R-02. Proveedor, frecuencia exacta y tiempo objetivo de recuperación se definen en diseño técnico. | Categoría: continuidad | Verificación: prueba de restauración.
- **RNF-15 · Fotos compartidas con terceros:** cuando la Administración comparte manualmente una foto con un proveedor sin acceso, el sistema deja constancia de qué fotos se compartieron, con quién y cuándo. La política de fondo se asume así: se comparte solo la foto necesaria, se registra el consentimiento del residente cuando la foto muestra el interior de su unidad y se pide al proveedor no conservarla tras su uso. | Categoría: privacidad | Verificación: revisión de la bitácora.
- **RNF-16 · Integridad de las cifras:** las cifras del tablero y de la exportación coinciden con los registros de los que se calculan. | Categoría: exactitud | Verificación: RF-13-AC-1 a AC-7 y RF-23-AC-2.
- **RNF-17 · Costo de infraestructura:** el sistema puede operar en infraestructura de bajo costo (incluido el almacenamiento de fotos), de modo que el gasto pueda aprobarse en asamblea. | Categoría: costo | Verificación: estimación mensual presentada al comité.

### 3.3 Requerimientos de dominio

- **RD-01 · Catálogo de categorías, subtipos y prioridad sugerida.**

| Categoría | Subtipo (obligatorio donde se indica) | Prioridad sugerida |
|---|---|---|
| Plomería y fugas | Fuga activa · Drenaje tapado o desbordado · Otra | Urgente · Urgente · Normal |
| Electricidad | Riesgo eléctrico · Otra | Urgente · Normal |
| Iluminación | Pasillo o área techada · Jardín o exterior | Normal · Menor |
| Bombas y cisterna | Falta de agua por falla de bombas · Otra | Urgente · Normal |
| Elevador | Persona atrapada · Otra | Urgente · Normal |
| Accesos y seguridad (incluye puertas y portones) | Portón o acceso que no cierra y deja el acceso abierto · Otra | Urgente · Normal |
| Albañilería y acabados | Daño con riesgo de caída o accidente · Estético · Otra | Urgente · Menor · Normal |
| Impermeabilización | Sin subtipo | Normal |
| Limpieza de áreas comunes | Sin subtipo | Normal |
| Jardinería | Sin subtipo | Normal |
| Otro | Sin subtipo | Normal |

  Reglas: **Urgente** es lo que pone en riesgo a las personas o al edificio (fuga fuerte, riesgo eléctrico, falta de agua, drenaje, caída, persona atrapada, portón que no cierra); **Normal** afecta el funcionamiento pero puede esperar horas o días; **Menor** es estético o sin efecto en el uso. Si el reportante responde «Sí» al peligro, la sugerida es `Urgente`. La Administración decide la prioridad final (RD-10).

- **RD-02 · Tiempos objetivo por prioridad,** contados desde la fecha de aviso: **Urgente:** primera atención en 1 hora o menos y resolución en 24 horas o menos. **Normal:** resolución en 72 horas o menos. **Menor:** resolución en 168 horas o menos. Normal y Menor no tienen objetivo de primera atención. El cumplimiento se mide en dos bloques: personal propio y proveedores externos (RF-13), porque estos últimos dependen de terceros. Los valores son parámetros (RF-27).
- **RD-03 · Responsable del costo.** Elemento común o instalación general: el condominio (fondo de mantenimiento). Interior de una unidad: el propietario de esa unidad, aunque lo haya reportado un inquilino. Daño causado por un residente o por una modificación en su unidad: lo determina la Administración. Un reporte puede clasificarse como `Común`, `Privada` o `Por determinar` y reclasificarse tras revisar (RF-06). El reglamento del condominio puede precisar más reglas.
- **RD-04 · Cierre.** Solo la Administración cierra un reporte en definitiva. El personal de mantenimiento puede marcarlo como `Terminado`, pero no cerrarlo, y el residente no cierra nada.
- **RD-05 · El propietario es el condómino** y responde por su unidad ante la Administración, aunque no viva en el condominio. Por eso se le informa de los reportes de su unidad aunque los haga un inquilino.
- **RD-06 · Acceso a unidades.** Nadie entra a una unidad sin autorización de quien la ocupa y con un adulto presente. Un reporte en el interior de una unidad registra si el ocupante autorizó el acceso. Si respondió «No», el reporte se puede asignar y el responsable ve «Sin autorización de acceso: coordinar con la Administración».
- **RD-07 · Confidencialidad.** El tipo de ocupación, los teléfonos y los correos de residentes y propietarios son información confidencial de la Administración.
- **RD-08 · Fotografías sensibles.** Las fotos pueden mostrar el interior de un departamento, por lo que se tratan como información sensible del residente (matriz 2.3, RNF-15).
- **RD-09 · Proveedores externos sin acceso y evidencia.** Los reportes atendidos por un proveedor sin acceso pueden pasar a `Terminado` sin foto solo con una justificación registrada por la Administración, y quedan marcados «Terminado sin evidencia fotográfica» para auditoría (RF-08). Los casos que dependen de proveedores externos se miden aparte (RD-02) y su estado siempre es visible.
- **RD-10 · Decisiones de gestión por rol.** Clasificar la urgencia y la responsabilidad, asignar, cerrar y decidir la reapertura corresponde a la Administración (a la Auxiliar solo con delegación, RF-21). Ningún usuario de Mantenimiento autoriza gastos ni llama a proveedores por su cuenta. Los gastos de más de $15,000 requieren autorización del comité de vigilancia y, cuando sea posible, tres cotizaciones; los menores los autoriza el Administrador. ReportaYa no automatiza esa autorización (EX-12).
- **RD-11 · Horarios del condominio** (informativo): mantenimiento de planta trabaja de lunes a sábado de 8 a 5; los trabajos con ruido van de lunes a viernes de 9 a 6 y sábados hasta las 2. El sistema no los valida (EX-09).
- **RD-12 · Emergencias.** Una emergencia real (persona en riesgo, incendio, inundación fuerte) se atiende por teléfono o en la caseta, no por ReportaYa.
- **RD-13 · Estructura de ubicación.** La ubicación se expresa con torre, piso y número de unidad (con la parte afectada dentro del departamento) o con un área común y una referencia en texto libre. La detección de duplicados usa torre y piso, o el nivel más específico común a ambos reportes (RF-17).
- **RD-14 · Recurrencia.** Una falla recurrente se identifica por la repetición de la misma categoría en la misma ubicación de origen, y se reporta en la asamblea anual. Una reapertura (RF-19) no cuenta como reporte nuevo.

### 3.4 Interfaces externas

- **Interfaz de usuario:** aplicación web responsiva, accesible desde el navegador del celular (residentes, Vigilancia y Mantenimiento) y desde computadora (Administración), sin instalación.
- **Interfaz de hardware:** cámara del dispositivo del usuario, para adjuntar fotos y video.
- **Interfaz de software:** servicio de almacenamiento de archivos (disco local o nube), servicio de correo (RF-11, RF-14) y, como posibilidad futura, WhatsApp para notificaciones (EX-06).
- **Interfaz de comunicación:** HTTPS sobre red móvil o Wi-Fi, con tolerancia a interrupciones (RNF-11).

---

## 4. Notas de diseño (referencia, fuera del alcance formal)

El núcleo técnico difícil combina subida y almacenamiento de archivos, un flujo de estados con asignación y el cálculo de métricas de tiempo. Los patrones previstos son:

- **Adapter:** para el almacenamiento de archivos (disco local o nube), de modo que el mecanismo de guardado sea intercambiable (RNF-08).
- **Observer:** para notificar cambios de estado a las partes interesadas (RF-11, RF-17, RF-22) sin acoplar el flujo de estados a cada canal.
- **State:** para modelar el ciclo de vida del reporte (`Reportado`, `Asignado`, `En proceso`, `Terminado`, `Cerrado`, `Cancelado`, `Unido`) de forma explícita y verificable. La detención (RF-18) es una marca sobre `Asignado` y `En proceso`, no un estado aparte.
- **Stack:** backend FastAPI, PostgreSQL y Docker (actividad S01-A2). El frontend queda por decidir entre React con Vite (SRS-Arreola) y Next.js (SRS-Luis). El criterio de decisión debe ser RNF-11 (modo sin conexión), que favorece una aplicación web progresiva.

## 5. Decisiones asumidas y cuestiones abiertas

**Decisiones asumidas como definitivas por el equipo.** Ninguna entrevista las confirmó textualmente; el equipo las adopta en esta versión. Los valores numéricos se cambian en RF-27 sin modificar la especificación.

1. Terminado sin evidencia fotográfica para proveedores sin acceso, con justificación obligatoria y marca de auditoría (RF-08-AC-4, RD-09).
2. RNF-02 (3 pantallas), RNF-12 (99 % mensual), umbrales de estancamiento de RF-22 (2 h / 24 h / 72 h) y plazo de reapertura de RF-19 (30 días).
3. Plazo de confirmación del residente de 72 horas (RF-09).
4. Objetivo de «Normal» de 72 horas corridas (RD-02).
5. Un reporte reabierto no cuenta como reporte nuevo para la recurrencia (RD-14).
6. Límite de video de 50 MB y de fotos de 10 MB (RF-05).
7. Política de fotos compartidas con terceros (RNF-15) y periodos de retención (RNF-13).
8. Delegación a la Auxiliar con asignar, reclasificar, cerrar y clasificar (RF-21, RD-10).
9. Umbral de $15,000 para autorización del comité (RD-10).
10. Los casos de responsabilidad privada los cierra la Administración.

**Cuestiones abiertas** (dependen de información que el cliente aún no ha dado):

11. Autorización de acceso: la cliente real dijo que la da «el residente»; el cliente simulado, propietario o inquilino (RD-06).
12. Participación del comité y de los proveedores en el sistema más allá de lo especificado.
13. Quién ve los tiempos de atención además de la Administración.
14. Mecanismo de identificación de usuarios que no recuerdan contraseñas (se mitiga con RF-14, pero conviene probarlo con usuarios).

**Priorización (decisión del equipo):**

15. Alcance mínimo de 12 semanas: RF-01 a RF-16 y RF-27. Segunda fase: RF-17 a RF-26 y RNF-11 en su modalidad completa. Si el equipo decide diferir una función, debe quedar escrito aquí y no cambiar su especificación.

**Pendientes de definición técnica:** integración con WhatsApp (EX-06), detalles de RNF-14 y elección del frontend (sección 4).

---
