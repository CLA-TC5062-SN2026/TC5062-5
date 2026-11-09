import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig, loadEnv } from 'vite'

// En desarrollo, Vite reenvía /api/v1 al backend FastAPI (mismo origen, como hará Caddy en producción; AR-5).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    plugins: [react(), tailwindcss()],
    server: {
      proxy: {
        '/api/v1': env.VITE_BACKEND_URL || 'http://127.0.0.1:8000',
      },
    },
  }
})
