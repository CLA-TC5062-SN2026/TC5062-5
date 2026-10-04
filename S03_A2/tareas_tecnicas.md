# ReportaYa · Sprint 1 · Descomposición en tareas

Complementa `sprint1_planning.md`. Todas las tareas duran **4 h o menos**. Las horas son de trabajo efectivo e incluyen escribir pruebas y abrir el PR.

## Convenciones

- **Roles:** Backend/DevOps, Frontend y QA. Son sombreros, no personas: con tres integrantes, cada uno usa más de uno.
- **Personas A, B y C:** son marcadores de posición, así que hay que sustituirlos por los nombres reales del equipo.
- **Definition of Done común (aplica a toda tarea de código, además de su criterio propio):** PR revisado por otra persona, CI en verde, fusionado a `main` y sin deuda abierta sin issue.
- **QA cruzado:** quien prueba una historia no escribió su backend.
- **Stack:** las tareas no asumen uno. Los criterios de done son verificables con cualquier tecnología.

## Resumen de carga

| Persona | Rol principal | Horas | Tareas |
|---|---|---|---|
| A | Backend/DevOps y QA | 12.0 | S-2, S-3, 06.1, 06.2, 01.4, 09.4 |
| B | Frontend y QA | 12.0 | 06.3, 01.3, 02.3, 09.3, 06.4, 02.4 |
| C | Backend | 12.5 | S-1, 01.1, 01.2, 02.1, 02.2, 09.1, 09.2 |
| **Total** | | **36.5** | |

La capacidad neta estimada es de ~34 h, así que el plan queda ~7 % arriba. Si a mitad de sprint hay retraso, se recorta **HU-09** primero (09.3 y 09.4, y las lecturas fijas en código se documentan como deuda).

## Tareas habilitadoras (sin historia, ~7 h)

Son el arranque técnico del primer sprint.

| ID | Tarea | Rol | Resp. | h | Depende de | Criterio de done |
|---|---|---|---|---|---|---|
| S-1 | Estructura del repositorio, README de arranque, convención de ramas, plantilla de PR con la DoD y protección de `main` | Backend/DevOps | C | 1.5 | — | Un PR de prueba no se puede fusionar sin revisión; el README permite a otra persona entender cómo contribuir. |
| S-2 | Entorno local reproducible: base de datos y herramienta de migraciones | Backend/DevOps | A | 2.5 | S-1 | Otra persona clona el repo y lo levanta siguiendo ≤3 comandos documentados; una migración vacía se aplica y se revierte. |
| S-3 | CI (lint y pruebas) y despliegue automático a un entorno de pruebas | Backend/DevOps | A | 3 | S-2 | Un merge a `main` dispara el pipeline, que termina en verde y deja la aplicación accesible por URL. |

## HU-06 · Crear la primera cuenta de Administración (2 SP · 6 h)

| ID | Tarea | Rol | Resp. | h | Depende de | Criterio de done |
|---|---|---|---|---|---|---|
| 06.1 | Modelo de usuario y rol con su migración; contraseñas con hash y sal | Backend | A | 2 | S-2 | La migración aplica en una base limpia; ningún campo guarda la contraseña en claro; una prueba unitaria verifica el hash. |
| 06.2 | Endpoint de alta de la primera cuenta de Administración, bloqueado si ya existe una | Backend | A | 1.5 | 06.1 | En base vacía devuelve éxito y crea la cuenta; en una segunda llamada devuelve rechazo y no crea nada; ambos casos tienen prueba automática. |
| 06.3 | Esqueleto de la aplicación web (rutas, layout, cliente HTTP) y pantalla de configuración inicial | Frontend | B | 2 | 06.2 | La pantalla solo aparece si no existe Administración; muestra errores de validación del formulario; la cuenta se crea de punta a punta en el entorno de pruebas. |
| 06.4 | Pruebas de aceptación de HU-06 | QA | B | 1 | 06.3 | Los criterios de aceptación de la historia pasan en el entorno de pruebas; los defectos quedan registrados como issues. |

## HU-01 · Iniciar sesión según mi rol (3 SP · 8 h)

| ID | Tarea | Rol | Resp. | h | Depende de | Criterio de done |
|---|---|---|---|---|---|---|
| 01.1 | Endpoint de inicio de sesión con sesión o token con expiración y cierre de sesión | Backend | C | 2.5 | 06.1 | Credenciales válidas abren sesión; las inválidas devuelven un mensaje genérico que no revela si falló el usuario o la contraseña; una sesión expirada se rechaza (pruebas automáticas). |
| 01.2 | Middleware de autorización por rol con la matriz de permisos en configuración | Backend | C | 1.5 | 01.1 | Una ruta protegida devuelve 401 sin sesión y 403 con un rol no permitido; la matriz de permisos vive en un archivo de configuración y no en el código de cada ruta. |
| 01.3 | Pantalla de login, manejo de sesión, cierre de sesión y guardas de ruta por rol | Frontend | B | 2.5 | 01.1 | Un usuario sin sesión no ve rutas privadas; tras iniciar sesión llega a la vista de su rol; cerrar sesión limpia el estado. |
| 01.4 | Prueba de la matriz de acceso rol × ruta | QA | A | 1.5 | 01.2, 01.3 | Existe una tabla de casos con al menos un caso por rol; todos pasan con **0 accesos indebidos**; los casos quedan automatizados o documentados. |

## HU-02 · Mantener el padrón de unidades y áreas comunes (3 SP · 8 h)

| ID | Tarea | Rol | Resp. | h | Depende de | Criterio de done |
|---|---|---|---|---|---|---|
| 02.1 | Modelos de unidad y área común con su migración y validaciones | Backend | C | 1.5 | S-2 | Los identificadores son únicos; los campos obligatorios se validan; la migración se aplica y se revierte. |
| 02.2 | Endpoints de crear, listar, editar y desactivar, solo para Administración | Backend | C | 2 | 02.1, 01.2 | Cada operación responde correctamente para Administración y rechaza a otros roles; desactivar es **baja lógica**, para no romper reportes futuros que apunten a la unidad (decisión de diseño, a confirmar con el equipo). |
| 02.3 | Pantalla de listado y formulario de alta y edición | Frontend | B | 3 | 02.2, 01.3 | Se puede crear y editar una unidad y un área común desde la interfaz; los errores del servidor se muestran; los registros persisten tras recargar. |
| 02.4 | Pruebas de aceptación de HU-02 | QA | B | 1.5 | 02.3 | Los criterios de aceptación pasan; se cubre el caso de identificador duplicado y el de acceso con un rol no autorizado. |

## HU-09 · Ajustar los plazos y umbrales del sistema (3 SP · 7 h)

| ID | Tarea | Rol | Resp. | h | Depende de | Criterio de done |
|---|---|---|---|---|---|---|
| 09.1 | Tabla de parámetros con valores iniciales y validación | Backend | C | 2 | S-2 | El seed carga los plazos del SRS (1 h, 24 h, 72 h, 168 h) con sus nombres exactos tomados del SRS; la validación rechaza valores no numéricos, cero o negativos. |
| 09.2 | Endpoints para leer y actualizar parámetros, con registro de quién y cuándo | Backend | C | 1.5 | 09.1, 01.2 | Solo Administración puede modificar; cada cambio guarda el valor anterior, el nuevo, quién lo hizo y cuándo; el valor nuevo se refleja sin reiniciar la aplicación. |
| 09.3 | Pantalla de parámetros | Frontend | B | 2 | 09.2, 01.3 | Se ve la lista con valores actuales; se edita uno; el cambio se confirma y persiste. |
| 09.4 | Pruebas de aceptación de HU-09 | QA | A | 1.5 | 09.3 | Cambiar un plazo de 72 h a 48 h se refleja en la configuración sin redeploy; los valores inválidos se rechazan; se verifica el registro del cambio. |

## Orden sugerido

- **Semana 1:** S-1, S-2, S-3, 06.1 a 06.4, 01.1 a 01.3. Al terminar, ya hay login desplegado.
- **Semana 2:** 01.4, 02.1 a 02.4 y 09.1 a 09.4. Los dos últimos días quedan para la demo, corregir lo que salga de las pruebas y la retro.
- **Ruta crítica:** S-2 → 06.1 → 01.1 → 01.2 → (02.2 y 09.2) → pantallas. Un retraso en S-2 mueve todo, así que debe cerrarse en los primeros 2–3 días.

## Supuestos a confirmar

1. Tres integrantes y los nombres de A, B y C.
2. La baja de unidades es lógica y no se borra información.
3. Los nombres y valores de los plazos de HU-09 se toman del SRS, porque aquí solo se conocen los cuatro valores.
4. La carga masiva del padrón no entra en este sprint; HU-02 cubre el alta y edición una por una.
