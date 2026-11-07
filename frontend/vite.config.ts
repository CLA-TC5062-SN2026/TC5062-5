import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // El tercer argumento '' carga también las variables sin prefijo VITE_ (API_PROXY_TARGET), que solo usa este archivo.
  const env = loadEnv(mode, process.cwd(), '')
  const destino = env.API_PROXY_TARGET || 'http://127.0.0.1:8000'

  return {
    plugins: [react(), tailwindcss()],
    server: {
      port: 5173,
      // Reproduce en desarrollo lo que hará Caddy en producción (AR-5): la app y el API comparten origen.
      proxy: {
        '/api': { target: destino, changeOrigin: true },
        '/health': { target: destino, changeOrigin: true },
      },
    },
  }
})
