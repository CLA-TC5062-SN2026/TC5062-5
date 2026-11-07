# Decisión del stack de frontend — ReportaYa

**Estado:** decisión del equipo · **Fecha:** 2026-11-07 · **Autor:** Equipo 5 (análisis comparativo asistido por agente)

**Insumos:** `S03_A1/SRS_equipo.md` v2.0 (secciones 2.3, 2.4, 3.2 y 4), `S05_S06_A1/arquitectura_equipo.md` (decisión AR-2), `S05_S06_A1/openapi_equipo.yaml`, `S05_S06_A2/revision_seguridad.md` y el backend en `backend/`.

---

## 1. Stack elegido

| Capa | Elección | En una línea |
|---|---|---|
| **Framework de UI** | **React** con **TypeScript** | Ya lo usamos y ya está aprobado en AR-2; TypeScript permite generar los tipos desde `openapi_equipo.yaml` |
| **Construcción y servidor de desarrollo** | **Vite** + `vite-plugin-pwa` (Workbox) | Genera archivos estáticos que sirve Caddy y crea el service worker que exige RNF-11 |
| **Estilos** | **Tailwind CSS** con colores y tamaños definidos como variables del tema | Diseño desde 360 px con poco CSS propio; el contraste de RNF-09 se verifica una sola vez en la paleta |
| **Manejo de estado** | **Sin librería de estado global.** Estado local de React + **Context API** para la sesión + **TanStack Query** para los datos del servidor + **IndexedDB** (con `idb`) para la cola de envíos pendientes | Casi todo el estado de la app es una copia de lo que hay en el servidor; lo único realmente global es la sesión |

**Complementos que la decisión implica** (no son parte de las cuatro capas, pero se fijan aquí para que nadie los elija por separado):

- **React Router** para las rutas y las guardas por rol (tarea 01.3 del Sprint 1).
- **`openapi-typescript`** para generar los tipos de las 46 operaciones a partir del YAML del equipo; si el contrato cambia, el compilador marca las pantallas afectadas.
- **`fetch` nativo** envuelto en un cliente propio pequeño (agrega `Authorization: Bearer`, traduce el esquema `Error` del contrato y maneja `ETag`/`If-Match` y `Idempotency-Key`). No se usa Axios.

---

## 2. Alternativas consideradas y por qué se descartaron

### 2.1 Framework y construcción

| Alternativa | Por qué se descarta |
|---|---|
| **Next.js** (propuesta de Luis, SRS-Luis) | Ya se descartó en AR-2: su ventaja es el render en servidor (SSR), que ReportaYa no necesita (todas las pantallas están detrás del inicio de sesión, no hay SEO). Exigiría un contenedor Node adicional, contra RNF-17 y R-02 (bajo costo), y su modelo de servidor complica el service worker y la cola offline de RNF-11, que son el requisito de mayor riesgo. |
| **Vue 3 + Pinia** | Técnicamente adecuado (también funciona con Vite y PWA), pero nadie en el equipo lo ha usado y la Actividad 0 de esta semana fue con React + Vite. Aprender otro framework en un proyecto de 12 semanas (R-04) es costo sin beneficio para este caso. |
| **Angular** | Trae todo incluido (rutas, formularios, HTTP), pero tiene la curva de aprendizaje más alta y genera paquetes más pesados para un Android de gama básica (R-09, RNF-01). Nadie en el equipo lo domina. |
| **Svelte / SvelteKit** | Paquetes muy ligeros, que favorecen RNF-01, pero sin experiencia en el equipo y con menos ejemplos y librerías para el caso offline con fotos. |
| **JavaScript sin framework** | Viable para pocas pantallas, pero ReportaYa tiene cinco perfiles con vistas distintas, guardas por rol, formularios con validación y un flujo de estados. Sin componentes, ese código se duplica y se vuelve difícil de probar. |
| **Webpack / Create React App** | CRA está descontinuado; Webpack requiere mucha más configuración que Vite para el mismo resultado y su servidor de desarrollo es más lento. |

### 2.2 Estilos

| Alternativa | Por qué se descarta |
|---|---|
| **Bootstrap** | Rápido para pantallas de administración, pero agrega su CSS completo (y su JavaScript para algunos componentes) a cada celular, y personalizarlo para que no "se vea Bootstrap" cuesta más que construir con utilidades. Sus colores por defecto no siempre llegan a 4.5:1 sobre todos los fondos (RNF-09), así que habría que sobrescribirlos de todos modos. |
| **CSS Modules / CSS puro** | Es la opción sin curva de aprendizaje (viene con Vite) y fue la segunda mejor evaluada. Se descarta porque cada pantalla tendría que resolver de nuevo espaciados, puntos de quiebre y colores; con tres personas y poco tiempo, la consistencia visual dependería de la disciplina de cada uno. Se mantiene como respaldo si Tailwind resulta un obstáculo en los primeros sprints. |
| **Librería de componentes (MUI, Chakra, Ant Design)** | Resuelven componentes complejos (tablas, selectores de fecha), pero pesan más en el primer acceso desde un Android básico y fijan una apariencia difícil de adaptar. Se puede incorporar **un** componente puntual (por ejemplo, un selector de fechas accesible) si hace falta, sin adoptar la librería completa. |

### 2.3 Manejo de estado

| Alternativa | Por qué se descarta |
|---|---|
| **Redux Toolkit** | Diseñado para mucho estado compartido que cambia en el cliente. En ReportaYa casi todo el estado vive en el servidor (reportes, padrón, avisos); con Redux habría que escribir a mano la caché, la recarga y la invalidación que TanStack Query ya resuelve. |
| **Zustand** | Ligero y simple, pero tampoco resuelve caché ni sincronización con el servidor, y lo único global que queda (la sesión) cabe en un Context. Se podría adoptar después sin reescribir si aparece estado de cliente compartido que no sea del servidor. |
| **Solo estado local + Context, sin TanStack Query** | Es lo más sencillo de entender, pero obligaría a reescribir en cada pantalla la carga, los errores, los reintentos y la caché, y a construir desde cero la consulta sin conexión que pide RNF-11 para Mantenimiento. |

---

## 3. Justificación en términos del proyecto

### 3.1 Características del equipo

- **Experiencia:** la tecnología que el equipo conoce es React, y la Actividad 0 de esta semana se hizo con React + Vite, así que el arranque del proyecto reutiliza lo que acabamos de practicar.
- **Tamaño y tiempo:** tres personas, ~8.5 h por semana cada una y 12 semanas (R-04, `sprint1_planning.md`). El rol de Frontend es un "sombrero" que comparten personas que también hacen backend y QA, así que el stack debe tener poca configuración y patrones conocidos.
- **Costo de aprendizaje asumido:** **Tailwind**, **TanStack Query** y el **service worker** son nuevos para el equipo. Se acepta porque cada uno reemplaza código que de otra forma escribiríamos a mano (CSS repetido, caché y reintentos, modo offline). Mitigación: el esqueleto de la app (tarea 06.3) incluye un ejemplo de cada uno que las demás pantallas copian.
- **TypeScript:** el backend está en Python y no todos hemos usado TypeScript en un proyecto. Se adopta en modo no estricto al inicio; su valor principal es que los tipos generados del contrato detectan, al compilar, que la pantalla y la API no coinciden. Esa clase de error ya nos pasó en S05-S06: algunos diagramas de secuencia usaban rutas viejas del API (`/sesiones`, `/transiciones`; sección 6 de `arquitectura_equipo.md`).

### 3.2 Integración con el backend (API REST con JWT)

| Aspecto del backend | Cómo lo atiende el stack |
|---|---|
| **Mismo origen detrás de Caddy (AR-5)** — el backend no tiene configurado CORS | En producción Caddy sirve los estáticos de `vite build` y reenvía `/api/v1`. En desarrollo, el `server.proxy` de Vite reenvía `/api/v1` a `127.0.0.1:8000`, que reproduce el mismo origen. Por eso no hace falta habilitar CORS en FastAPI. |
| **JWT Bearer de 30 min sin token de renovación** (`POST /auth/login` devuelve `token` y `expiraEn: 1800`) | El token vive en el Context de sesión (en memoria) y, como respaldo ante recargas, en `sessionStorage`; no se usa `localStorage`, para que no sobreviva al cierre del navegador. El cliente HTTP lo agrega a cada petición. Ante un `401` con código `SESION_EXPIRADA`, limpia la sesión y lleva al login, conservando la ruta para regresar. |
| **Autorización por rol con `403`** (tabla `PERMISOS` de `app/security.py`) | `GET /auth/me` devuelve el rol; React Router oculta las rutas que el rol no puede usar. **Esto es solo comodidad para el usuario:** quien protege los datos sigue siendo el servidor (RNF-05). |
| **Esquema `Error` del contrato, `ETag`/`If-Match` (412) y paginación** | Se resuelven una vez en el cliente HTTP y en los hooks de TanStack Query; las pantallas no repiten esa lógica. |
| **`multipart` para fotos y video** (RNF-04) | `FormData` nativo; la foto se comprime en el navegador antes de subirla si supera el límite (`MAX_FOTO_MB=10`). |
| **`Idempotency-Key`** (AR-7) | El cliente genera la clave al **capturar** el reporte, no al enviarlo, y la guarda en la cola de IndexedDB; si el reintento llega dos veces, el servidor no duplica el reporte. |

### 3.3 Complejidad de la interfaz requerida

- **Dos tipos de uso muy distintos.** Residentes y Mantenimiento usan un celular a 360 px, Mantenimiento en un Android de gama básica y con poca experiencia digital (sección 2.3 del SRS). Administración y Vigilancia usan computadora y necesitan tablas, filtros y un tablero (RF-13). Tailwind permite diseñar primero para celular y agregar el diseño de escritorio con puntos de quiebre en la misma clase, sin dos hojas de estilo.
- **RNF-02 (máximo 3 pantallas para reportar o terminar):** con rutas anidadas y estado local de formulario, el flujo de alta (datos → fotos → confirmar) se queda en una sola ruta con pasos y no se pierde lo capturado al cambiar de paso.
- **RNF-09 (contraste 4.5:1, 16 px base):** los colores se definen una sola vez en el tema de Tailwind y se verifican con una herramienta de contraste; las pantallas usan solo esos colores, así que no aparecen combinaciones sin revisar.
- **RNF-11 (sin conexión) es lo que más pesa en la decisión**, como pedía la sección 4 del SRS:
  - `vite-plugin-pwa` genera el service worker que guarda la aplicación para abrirla sin señal.
  - La cola de **reportes y `Terminado` pendientes, con sus fotos**, se guarda en IndexedDB y se reenvía al recuperar la señal (evento `online` y al abrir la app). La pantalla muestra «Pendiente» o «Enviado» leyendo esa cola.
  - La consulta sin señal de los reportes asignados a Mantenimiento se cubre guardando la caché de TanStack Query en IndexedDB.
  - **Riesgo abierto:** si el token venció mientras el dispositivo estaba sin señal, la cola espera a que el usuario vuelva a iniciar sesión y luego se envía; lo capturado no se pierde. Esto se valida en el prototipo que pide la sección 6 de `arquitectura_equipo.md`.
- **Lo que no se decide aquí:** la librería de gráficas del tablero (RF-13) y la generación del PDF (RF-23, que según la arquitectura se hace en el backend). Se eligen cuando se planifiquen esas historias.

---

## 4. Criterios con los que se comparó

Las opciones se evaluaron con estos criterios, en este orden de prioridad:

1. **Viabilidad de RNF-11** (service worker, cola con fotos, consulta sin señal), porque es el requisito de mayor riesgo.
2. **Experiencia del equipo** y costo de aprendizaje dentro de 12 semanas.
3. **Integración con el backend:** mismo origen, Bearer JWT, contrato OpenAPI.
4. **Peso en un Android de gama básica** (RNF-01, R-09) y **costo de operación** (RNF-17).
5. **Accesibilidad** verificable (RNF-09).
