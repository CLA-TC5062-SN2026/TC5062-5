# Retrospectiva del proyecto — ReportaYa

**Equipo 5 · TC5062 · S11-A1 · Parte 3**

Integrantes: Manuel Medina, Emmanuel Castañeda «Lupus», Alejandro Arreola y Luis Guerrero.

## Sección A — Retrospectiva SCRUM

### ¿Qué salió bien?

- **La especificación fue la base de todo.** El SRS v2.0 consolidó tres propuestas individuales, con 27 RF y 161 criterios en formato Dado–Cuando–Entonces con datos concretos (`B-502`, `RY-000124`, fechas y mensajes exactos). Esos criterios se volvieron pruebas casi sin traducción: `test_reglas.py` tiene un caso por criterio y usa el mismo condominio de prueba del SRS (sección 3.0).
- **El contrato de API se diseñó antes que el código y se respetó.** `openapi_equipo.yaml` fijó rutas, códigos, esquemas, roles y la precedencia de errores. La prueba de contrato lo hizo verificable: en S05-S06 pasaba 697 verificaciones; ahora pasa 1,058, en 68 de 68 operaciones y con 0 fallos.
- **La revisión de código encontró lo importante.** En S09-A1, el hallazgo H-1 (un residente podía leer y modificar reportes de otras unidades) se **reprodujo con el API real**, no solo se describió. Esa reproducción fue la base de la corrección en S11.
- **El modelo de datos aguantó el flujo completo sin rediseño.** Ciclos de atención, confirmaciones, avisos, enlaces de activación y disparadores de solo inserción ya estaban en `esquema_bd.sql` desde S05. Para S11 solo se agregaron dos columnas: el asunto y el cuerpo del correo, para poder reintentarlo.
- **El reparto por actividad funcionó y no hubo conflictos personales.** Nos coordinamos por WhatsApp y cada entrega tuvo dueños claros: Alejandro y Luis escribieron cada uno su versión del SRS y después la unimos con el equipo; Manuel hizo los servicios CRUD del backend, y Emmanuel integró el frontend, el despliegue y las correcciones finales.
- **Las contradicciones se resolvieron con la voz de la clienta, no por votación.** Las versiones del SRS chocaban en 22 puntos (C-01 a C-22 en `S03_A1/diferencias_SRS.md`), por ejemplo quién cierra un reporte o si la foto es obligatoria. El criterio fue lo que dijo la clienta real en la entrevista: solo la Administración cierra y la foto del alta es opcional.

### ¿Qué no salió bien?

- **Las reglas de negocio se aplazaron sprint tras sprint.** S05-S06 implementó el CRUD y dejó el flujo de estados, la seguridad por registro y los avisos «para la siguiente actividad» (`S05_S06_A1/revision_sql.md`, sección 3). S09 refactorizó, pero dejó H-1 a propósito porque corregirlo cambiaba el comportamiento. Resultado: la primera versión de la matriz de trazabilidad de S11 (25/11/2026) dio **0 RF completos, 17 parciales y 10 sin implementar**. Hasta ese día, la aplicación no resolvía el núcleo del problema: ningún reporte pasaba de `Reportado`.
- **La prueba de contrato daba una falsa sensación de avance.** «759 verificaciones, 0 fallos» era cierto, pero esa prueba solo comprueba códigos y esquemas, no reglas. Además, para probar las notas y la persistencia escribía estados directamente en la base, lo que ocultaba que no existían las transiciones.
- **El backlog tuvo dos versiones con la misma numeración.** Hubo una propuesta de 15 historias y otra de 44, las dos numeradas HU-01, HU-02… con contenido distinto. El Sprint 1 (`S03_A2`) quedó con la de 44; la de 15 se subió y se revirtió el 25/11/2026. Eso costó tiempo al armar la matriz.
- **Dos copias del backend en `main`.** El refactor de S09 quedó en `S09_A1/backend/` y la raíz siguió con el código anterior. En S11 se adoptó el refactorizado como el oficial.
- **El frontend se quedó atrás.** Hasta S11 tenía inicio de sesión y una lista de solo lectura; no había forma de reportar desde la interfaz.
- **GitHub nos costó tiempo.** Por intermitencias de internet fallaron subidas, y en un par de ocasiones hubo que revertir o borrar carpetas que se subieron mal (por ejemplo, la reversión de `S03_A1` del 25/11/2026).
- **El cierre fue de último momento.** El núcleo del flujo, el modo sin conexión y el despliegue se resolvieron en los dos días previos a la entrega final.

### ¿Qué haríamos diferente la próxima vez?

- **Medir el avance contra los criterios de aceptación, no contra los endpoints.** Habría bastado con una matriz de trazabilidad desde el Sprint 1, actualizada en cada entrega, para ver que el núcleo seguía vacío.
- **Construir primero una «rebanada vertical» del flujo principal:** alta → asignación → terminado con evidencia → cierre, de punta a punta y con interfaz, antes de completar todo el CRUD del padrón.
- **No dejar pasar un hallazgo de seguridad crítico.** Si el refactor no debe cambiar el comportamiento, la corrección va en la tarea siguiente, con fecha, no en «deuda técnica».
- **Prohibir que las pruebas escriban estados en la base para saltarse reglas.** Si una prueba necesita ese atajo, es señal de que falta una funcionalidad.
- **Una sola fuente de verdad por artefacto:** un backlog, un backend.
- **Una carpeta por integrante para los borradores** y solo los entregables consolidados en la carpeta de la actividad, para no tener que revertir subidas.

### Análisis del uso de herramientas agentes

| Fase | Uso del agente | Más útil en… | Trabajo adicional que generó |
|---|---|---|---|
| Especificación (S01–S03) | Consolidar tres SRS individuales; generar el backlog | Rapidez y exhaustividad: 44 historias priorizadas, con criterios, en una sesión (`S03_A1/reflexion.md`) | Revisar cada historia contra el SRS. Los errores que «pasan desapercibidos» cuestan tanto como hacerlo de cero. La propuesta inicial de 15 historias / 97 SP se ajustó y dejó dos numeraciones |
| Diseño (S05) | Contrato OpenAPI, esquema SQL, diagrama de clases | Consistencia entre YAML, SQL y diagrama; decisiones justificadas por escrito | Correcciones al código generado contra el YAML (G-1 a G-3 en `revision_sql.md`): códigos no declarados y un choque con una restricción de la base |
| Construcción (S05–S08) | CRUD, autenticación JWT, scaffolding del frontend | Código repetitivo (routers, validación, serialización) y la prueba de contrato | El agente implementó lo que se le pidió (CRUD) y **dejó fuera el flujo sin que eso se notara** en las pruebas verdes |
| Calidad (S09) | Code review, linter, refactor guiado | Encontrar y **reproducir** H-1; medir antes y después (pylint 7.91 → 8.03; complejidad de `create_report` 26 → ≤ 10) | Decidir qué no refactorizar; la falla de seguridad quedó abierta |
| Interfaz (S07–S08) | Componentes React + Tailwind | Una primera versión completa de `Button`, `Input`, `Card` y `Navbar` | Los componentes tenían errores que corregimos nosotros: la barra no filtraba los enlaces por rol, los campos no generaban su `id` ni marcaban los obligatorios y la sesión se guardaba donde no convenía (`S07_S08_A1/revision_componentes.md`) |
| Cierre (S11) | Matriz de trazabilidad; corrección de los 27 RF; frontend del flujo; modo sin conexión; pruebas de los RNF; CI; despliegue en Render; README | Leer el SRS, el YAML y el código completos y cruzarlos; implementar el flujo, los avisos y el tablero **con una prueba por criterio**; recorrer la interfaz en un navegador real; medir carga, subida y accesibilidad | Hubo que tomar decisiones que el SRS no fija (correo simulado por omisión, eliminar `/auth/register`, quedarnos con SQLite). El agente también cometió errores que solo atraparon las pruebas o el despliegue: el componente Sí/No del formulario nunca quedaba marcado (lo detectó el recorrido E2E) y el primer despliegue en Render falló porque quitó de las dependencias del servidor una librería que la carga de la demo necesitaba |

**¿Cambió nuestra forma de programar?** Sí: nos ayudó a trabajar de forma más segura y profesional. El ejemplo más claro es H-1: el agente encontró que un residente podía ver y modificar reportes de otros departamentos; lo comprobamos contra el API real, lo corregimos y ahora hay pruebas que fallan si la falla regresa (al reintroducirla a propósito, 10 pruebas fallan). También aprendimos a no aceptar todo lo que propone: en los componentes de la página tenía errores que corregimos nosotros, y en S11 las pruebas y el despliegue atraparon errores suyos que se veían bien a simple vista. La lección es que el agente acelera, pero las pruebas y la revisión del equipo son las que deciden si algo está bien.

## Sección B — Consistencia problema–solución

### ¿La aplicación resuelve el problema planteado en la Semana 2?

Sí. El problema (SRS 1.2) eran reportes dispersos por WhatsApp, caseta y libreta, que se pierden, se duplican, nadie sabe en qué estado están y no dejan evidencia con fechas. Cada objetivo medible del SRS tiene hoy una funcionalidad y una prueba:

| Objetivo del SRS | Cómo lo cumple ReportaYa | Evidencia |
|---|---|---|
| 1. Todo reporte con folio y fecha de aviso, sin importar el medio | Alta del residente (RF-03) y captura de la Administración o Vigilancia con medio y fecha real del aviso (RF-04); detección de duplicados (RF-17) | `test_rf03_ac1_*`, `test_rf04_ac1_*`, `test_rf17_*`; captura `docs/capturas/02_error_validacion.png` y `03_reporte_creado_residente.png` |
| 2. El residente consulta estado y visita sin preguntar | Lista y detalle del residente con estado, visita y motivo de detención; avisos en el sistema y por correo en cada cambio (RF-10, RF-11, RF-15) | `test_rf10_*`, `test_rf11_*`, `test_rf15_ac2_*`; captura `09_confirmado_residente.png` |
| 3. Medir el tiempo de atención contra un objetivo por prioridad | Tablero con promedios y cumplimiento en dos bloques, recurrencia y PDF para el comité (RF-13, RF-23) | `test_rf13_ac1_*` (70 min / 67 %, 22 h / 67 %); `11_tablero.png`, `tablero.pdf` |
| 4. Cada terminado con evidencia y un historial inalterable | Terminado exige de 1 a 5 fotos por ciclo; cierre solo de la Administración tras la confirmación del residente; historial de solo inserción (RF-08, RF-09, RNF-07) | `test_rf08_*`, `test_rf09_*`; `10_cerrado_con_historial.png` |
| 5. Medir la adopción | Porcentaje de reportes con medio «Sistema» en el tablero (RF-13-AC-6) | `test_rf13_ac6_adopcion` |

La matriz de trazabilidad (`S11_A1/matriz_trazabilidad.md`) queda con **27 de 27 RF completos**. Además se cerró el hallazgo H-1: cada rol ve solo lo que le corresponde según la matriz 2.3, lo que protege la privacidad entre condóminos, una preocupación de las entrevistas (R-06, RD-07).

### ¿Qué partes del problema original no se resolvieron?

Lo que en la primera versión de esta retrospectiva quedaba pendiente (modo sin conexión, correo real, despliegue, almacenamiento en la nube y prueba de carga) se resolvió antes de la entrega. Queda esto:

| Pendiente | ¿Alcance u obstáculo técnico? |
|---|---|
| **Datos reales persistentes en línea** | **Obstáculo práctico (costo).** La demo pública (https://reportaya-6guv.onrender.com) usa el plan gratuito de Render, que no guarda datos entre reinicios ni garantiza disponibilidad (RNF-12). Para operar el condominio hace falta un servidor con `docker-compose.yml` o un disco persistente de pago. |
| **Correo y fotos con proveedores reales** | **Configuración.** El envío por SMTP y el almacén S3 están implementados y probados contra servidores simulados; faltan el buzón y el bucket del condominio. |
| **PostgreSQL** (R-03 de la arquitectura) | **Decisión de alcance.** Nos quedamos con SQLite: la prueba de carga con 5,000 reportes y 20 usuarios cumple RNF-03 (p95 ≤ 1.06 s). Solo cambiaría si el sistema atiende varios condominios. |
| **Prueba con usuarios y en dispositivos reales** | **Alcance.** RNF-01 y RNF-02 se verificaron en Chrome y con pruebas automáticas, no con residentes de poca experiencia digital ni en Safari de iOS. |
| **La meta de adopción** | **Depende de la operación.** El tablero mide el porcentaje de reportes que entran por el sistema, pero la meta de la clienta (la mayoría en 3 meses) solo se puede comprobar usándolo. |

### Si le presentáramos el proyecto a la clienta de la Semana 2, ¿qué mostraríamos primero y por qué?

Mostraríamos **el recorrido de un solo reporte, de principio a fin**, empezando por donde hoy le duele: un aviso que llega por WhatsApp o por la caseta.

1. La Administración lo captura con la **fecha real del aviso** y el sistema le asigna folio. Ya no se pierde en el chat.
2. Se asigna al conserje con prioridad; él lo ve en su celular, ordenado por urgencia.
3. Lo marca terminado **con foto**, y la residente confirma «Ya quedó» (o «Sigue fallando», y se reabre con el mismo folio).
4. Termina en el **tablero**: tiempo contra el objetivo, fallas recurrentes como la lámpara de la rampa y el PDF para el comité.

**Por qué ese orden:** responde una por una las quejas de la entrevista (perder reportes, no saber el estado, no tener evidencia, no poder rendir cuentas). Además, termina en lo que convence al comité de aprobar el gasto (supuesto S-07 del SRS): **métricas con evidencia**.

Lo que la clienta enfatizó en la entrevista y cómo aparece en ese recorrido:

| Lo que pidió la clienta | Dónde se ve en la demo |
|---|---|
| Página web desde el celular, sin instalar nada | Todo el recorrido se hace en el navegador del celular (RNF-01) |
| Solo la Administración cierra, para evitar cierres sin revisión | Mantenimiento marca «Terminado»; el cierre lo hace la Administración tras la confirmación (RF-09) |
| La foto al reportar no siempre obligatoria | El alta acepta 0 a 5 fotos; el terminado sí exige evidencia (RF-03, RF-08) |
| Que funcione sin señal (sótano, cuarto de bombas, pasillos) | Con el modo avión, el reporte queda «Pendiente» y se envía solo al volver la señal (RNF-11) |
| Costo bajo y cifras concretas para el comité | Tablero y PDF con tiempos, cumplimiento y recurrencia; operación en un servidor pequeño o la demo gratuita (RF-13, RF-23, RNF-17) |
| Que la mayoría de los reportes entren por el sistema en 3 meses | Porcentaje de adopción en el tablero (RF-13-AC-6) |

Por eso el paso 1 cambiaría ligeramente en la presentación: además del aviso de WhatsApp capturado por la Administración, mostraríamos al conserje registrando el terminado en el cuarto de bombas **sin señal**, porque es la queja más concreta que no resuelve ninguna libreta ni chat.
