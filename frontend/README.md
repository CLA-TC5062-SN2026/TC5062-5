# ReportaYa — frontend

React + TypeScript · Vite · Tailwind CSS · React Router · TanStack Query. Justificación: `decision_stack_frontend.md`.

## Puesta en marcha

Requiere Node.js 20.19+ (probado con 26.13 LTS) y el backend corriendo (`../backend/README.md`).

```bash
npm install
cp .env.example .env        # Windows: copy .env.example .env
npm run dev                 # http://localhost:5173
```

La página de inicio muestra «Conectado» si alcanza `GET /health` del backend; si no, revise que el backend esté en
`API_PROXY_TARGET` (por omisión `http://127.0.0.1:8000`).

| Comando | Qué hace |
|---|---|
| `npm run dev` | Servidor de desarrollo con recarga en caliente |
| `npm run build` | Verifica tipos (`tsc -b`) y genera `dist/` para que lo sirva Caddy |
| `npm run typecheck` | Solo verifica tipos |
| `npm run lint` | Revisión estática (oxlint) |
| `npm run preview` | Sirve `dist/` localmente |

## Variables de entorno

| Variable | Uso | Valor por omisión |
|---|---|---|
| `VITE_API_URL` | URL base del API que usa el navegador | `/api/v1` (mismo origen) |
| `API_PROXY_TARGET` | Solo en `npm run dev`: a dónde reenvía Vite `/api` y `/health` | `http://127.0.0.1:8000` |

Con `VITE_API_URL` relativa, el navegador nunca llama a otro origen: en desarrollo reenvía el proxy de Vite y en
producción Caddy (AR-5), así que el backend no necesita CORS.

## Estructura

```
src/
  main.tsx            punto de entrada: QueryClient + RouterProvider
  router.tsx          rutas (las guardas por rol llegan con el login, tarea 01.3)
  index.css           Tailwind y tema (colores verificados a 4.5:1, RNF-09)
  components/         piezas reutilizables (Layout, EstadoApi)
  pages/              una por ruta
  services/           config (variables de entorno), apiClient (fetch + Bearer + esquema Error), servicios por recurso
```
