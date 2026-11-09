# Decisión de stack del frontend — ReportaYa

**Equipo 5 · TC5062 · S07-S08-A1**

## 1. Stack elegido

| Capa | Elección | Versión |
|---|---|---|
| Framework de UI | React | 19 |
| Construcción / servidor de desarrollo | Vite (plantilla `react`) con `@vitejs/plugin-react` | 8 |
| Estilos | Tailwind CSS con el plugin `@tailwindcss/vite` | 4 |
| Manejo de estado | Context API para la sesión (token, usuario, rol); `useState`/`useReducer` locales para todo lo demás | — |
| Ruteo | React Router | 7 |
| Cliente HTTP | `fetch` nativo envuelto en `src/services/api.js` | — |

La URL base del API se lee de `VITE_API_URL`. En desarrollo vale `/api/v1` y Vite reenvía esas peticiones a `http://127.0.0.1:8000`. En producción Caddy hace lo mismo (AR-5), así que el frontend nunca habla con otro origen.

## 2. Alternativas consideradas

### Framework

Las propuestas individuales quedaron registradas en `S05_S06_A1/arquitectura_equipo.md` (conflicto AR-2):

| Propuesta | Quién | Resultado |
|---|---|---|
| React + Vite (PWA) | Alejandro, Lupus | **Elegida** |
| «Por decidir» entre React + Vite y Next.js | Manuel | Se resolvió a favor de React + Vite |
| Next.js en su propio contenedor Node | Luis | Descartada |

**Por qué se descartó Next.js:** su ventaja principal es el render en servidor (SSR/SSG), y ReportaYa no la necesita. Es una aplicación detrás de inicio de sesión, sin páginas públicas que indexar. Además, nos obligaba a mantener un contenedor Node más, cuando RNF-17 y R-02 piden un despliegue pequeño. Lo que sí exige el proyecto es RNF-11 (guardar reportes sin conexión y reintentar), y eso se resuelve con un service worker sobre una SPA estática.

### Estilos

| Opción | Por qué no |
|---|---|
| Bootstrap | Ya trae botón, tarjeta y barra de navegación con su propio diseño. Esta actividad pide construir esos componentes, así que terminaríamos sobrescribiendo Bootstrap en lugar de usarlo, y además carga CSS y JS que no ocupamos. |
| CSS Modules / CSS puro | No agregan dependencias y aíslan bien los estilos, pero cada punto de quiebre responsivo se escribe a mano con `@media`, y los colores del tema quedan repartidos en varios archivos. |

### Manejo de estado

| Opción | Por qué no |
|---|---|
| Redux Toolkit | Pensado para mucho estado global compartido. Nosotros solo tenemos uno: la sesión. |
| Zustand | Más ligero que Redux, pero sigue siendo una dependencia extra para resolver lo mismo que ya resuelve Context. |

## 3. Justificación en términos del proyecto

1. **Experiencia del equipo.** Tres de los cuatro integrantes propusieron o consideraron React + Vite en sus SRS y diagramas, y el cuarto propuso Next.js, que también es React. Todos trabajamos sobre el mismo modelo de componentes y hooks.
2. **Integración con el backend (FastAPI + JWT).** El API es REST con JWT Bearer (AR-8). Para consumirlo basta `fetch` con la cabecera `Authorization`; no necesitamos librerías del lado del servidor. El token y el rol viven en un `AuthContext`, y el contexto es lo que decide qué ve la barra de navegación y qué rutas se protegen. La matriz de permisos real la sigue aplicando el backend (RNF-05).
3. **Mismo origen en desarrollo y producción.** El backend no tiene CORS a propósito (AR-5). Con el proxy de Vite hacia `/api/v1` replicamos en desarrollo lo que Caddy hará en producción, sin tocar el backend.
4. **UI requerida.** La interfaz consiste en formularios, listas, tarjetas de reportes y una navegación que cambia según el rol. Debe funcionar en celular y en computadora (SRS, «Frontend web responsivo»): Mantenimiento la usa en campo y Vigilancia desde la caseta. Tailwind resuelve lo responsivo con prefijos (`sm:`, `md:`) dentro del propio componente.
5. **Accesibilidad (RNF-09).** RNF-09 pide un contraste de 4.5:1 y un texto base de 16 px. En Tailwind los colores del tema se definen una sola vez (`@theme`), así que se pueden verificar en un solo lugar contra WCAG 2.1 AA.
6. **Camino a RNF-11.** Vite tiene un plugin de PWA (`vite-plugin-pwa`) que agrega el service worker cuando lleguemos a esa historia. Quedarnos en una SPA estática no cierra esa puerta.
