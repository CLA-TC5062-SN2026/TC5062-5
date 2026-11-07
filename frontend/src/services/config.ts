/** Configuración leída de las variables de entorno (ver .env.example). */

/** URL base del API, sin diagonal final. Por omisión, ruta relativa al mismo origen (proxy de Vite o Caddy). */
export const API_URL: string = (import.meta.env.VITE_API_URL || '/api/v1').replace(/\/+$/, '')

/**
 * URL de `GET /health`, que el backend expone en la raíz y no bajo /api/v1.
 * Se calcula a partir del origen de API_URL para que funcione con URL relativa o absoluta.
 */
export const HEALTH_URL: string = new URL('/health', new URL(API_URL, window.location.origin)).toString()
