# Capa de servicios de API — ReportaYa

**Equipo 5 · TC5062 · S07-S08-A2**

## 1. Estructura

```
frontend/src/services/
├── apiClient.js        cliente HTTP único: URL base, JWT, tiempo límite y manejo centralizado de errores
├── tokenStorage.js     único módulo que lee/escribe la sesión en el navegador
├── authService.js      recurso /auth   → login(), me(), logout(), sesionActual()
└── reportesService.js  recurso /reports → listar(filtros), obtener(folio)
```

Los componentes y páginas nunca llaman a `fetch` directamente: usan `authService` o `reportesService`, y estos usan solo `apiClient`. Cada recurso nuevo del `openapi_equipo.yaml` (unidades, avisos, usuarios…) se agrega como un `[recurso]Service.js` más, sin tocar el cliente.

## 2. Cliente HTTP: `fetch` nativo

Mantenemos la decisión de `decision_stack_frontend.md`: `fetch` envuelto en un módulo propio, sin Axios.

| Opción | Por qué sí / por qué no |
|---|---|
| **`fetch` + envoltura propia** (elegida) | Viene en el navegador, no suma dependencias. Lo que Axios daría (interceptores, JSON automático, tiempo límite) son ~60 líneas en `apiClient.js` y quedan escritas a la medida del esquema `Error` del backend. |
| Axios | Trae interceptores listos, pero agrega una dependencia para algo que ya resolvemos con poco código. |
| TanStack Query | Útil para caché e invalidación cuando haya muchas vistas que comparten datos. Por ahora solo hay un flujo de negocio; se puede montar después **encima** de estos servicios sin cambiarlos. |

## 3. Interceptores (equivalente con `fetch`)

`fetch` no tiene interceptores, así que `apiClient.request()` pasa toda petición por dos funciones:

**Petición — `prepararPeticion()`**
- Antepone la URL base, que se lee de `import.meta.env.VITE_API_URL` (`frontend/.env`; por defecto `/api/v1`). En desarrollo Vite reenvía `/api/v1` al backend y en producción lo hará Caddy, así que siempre es el mismo origen (AR-5, el backend no tiene CORS).
- Si hay sesión, agrega `Authorization: Bearer <token>` tomado de `tokenStorage`. Las llamadas públicas (`/auth/login`) se marcan con `{ auth: false }`.
- Serializa el cuerpo a JSON y pone `Content-Type` (excepto `FormData`, que se usará para el alta de reportes con fotos).
- Agrega un tiempo límite de 15 s con `AbortController`.

**Respuesta — `procesarRespuesta()`**
- 2xx → devuelve el JSON (o `null` en 204).
- Cualquier otro código → lanza un único tipo de error, `ApiError { message, status, codigo, errores }`, con un mensaje **listo para mostrarse al usuario**:
  - Si el backend manda su mensaje (esquema `Error`: `{ codigo, mensaje, errores? }`) y es un 4xx, se usa ese mensaje, que ya es específico (p. ej. «Correo o contraseña incorrectos»).
  - Si no, se usa una tabla por código HTTP (403 «No tienes permiso…», 404, 409/412, 429, 500, 503…). En 5xx nunca se muestra el texto interno del servidor.
  - En 422 se conservan los `errores` por campo para que el formulario los ponga junto a cada input.
- **401 con token** = sesión vencida o inválida: borra la sesión y emite el evento `reportaya:sesion-expirada`. `AuthContext` lo escucha, limpia el estado y `ProtectedRoute` manda al login con el aviso «Tu sesión expiró». Un 401 **sin** token (credenciales incorrectas) solo se muestra en el formulario.
- **Errores de red** (`fetch` rechaza): «No se pudo conectar con el servidor. Revisa tu conexión…». **Tiempo agotado**: «El servidor tardó demasiado en responder…». Si la petición la canceló el propio componente (se desmontó), no se reporta como error.

Así, cada página solo hace `try { … } catch (e) { mostrar(e.message) }`; no hay manejo de códigos HTTP repartido en los componentes. El componente `Alerta` (con `role="alert"`) es el que presenta esos mensajes en pantalla, no la consola.

## 4. Dónde se guarda el token: `sessionStorage`

`tokenStorage.js` guarda `{ token, usuario, expiraEn }` en `sessionStorage` bajo la clave `reportaya.sesion`.

| Opción | Decisión |
|---|---|
| **`sessionStorage`** (elegida) | Sobrevive a recargar la página, pero se borra al cerrar la pestaña. Encaja con RNF-06 (token de 30 min) y con equipos compartidos como la computadora de la caseta de Vigilancia. |
| `localStorage` | Persistiría el token entre pestañas y reinicios del navegador; en un equipo compartido la sesión quedaría abierta para el siguiente usuario. |
| Cookie `HttpOnly` | Es lo más resistente a XSS, pero exige cambiar el backend (emitir la cookie, protección CSRF), y el contrato actual entrega el JWT en el cuerpo de `/auth/login`. Queda como mejora si se endurece la seguridad. |

Mitigaciones: el token solo se lee desde `tokenStorage` y solo se envía en la cabecera `Authorization`; `authService.sesionActual()` descarta la sesión si `expiraEn` ya pasó, sin esperar al 401; y React escapa el contenido que se pinta, lo que reduce la superficie de XSS. La autorización real por rol la sigue aplicando el backend (RNF-05); el frontend solo decide qué mostrar.

## 5. Flujos implementados sobre la capa

| Flujo | Archivos | Servicio |
|---|---|---|
| Login → dashboard | `pages/Login.jsx`, `context/AuthContext.jsx` | `authService.login()` |
| Ruta protegida | `components/ProtectedRoute.jsx` (envuelve `/` y `/reportes` en `App.jsx`) | `tokenStorage` vía `AuthContext` |
| Listar reportes (E2E) | `pages/Reportes.jsx`: estado de carga, error con «Reintentar», lista vacía y resultado | `reportesService.listar()` → `GET /reports` |

## 6. Cómo se probó

- Backend con `python scripts/init_db.py --reset --demo` (usuarios `*@reportaya.demo`, contraseña `Demo1234!`) y frontend con `npm run dev`.
- Revisado con Playwright: redirección al login sin sesión, contraseña incorrecta (mensaje del backend), login y redirección, cabecera `Authorization: Bearer …` en `GET /reports`, caída de red (mensaje de conexión), respuesta 500 (mensaje genérico) y token inválido (401 → login con «Tu sesión expiró»).
- `flujo_auth.mp4` y `flujo_e2e.mp4` se grabaron con Playwright sobre la app corriendo contra el backend real. En `flujo_e2e.mp4` se añadió una latencia de 1.5 s a `GET /reports` para que el estado de carga se alcance a ver (en local la respuesta tarda milisegundos), y al final se simula una caída de red para mostrar el mensaje de error y el botón «Reintentar».
