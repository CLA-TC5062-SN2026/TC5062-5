/**
 * Cliente HTTP único para el API de ReportaYa.
 *
 * - Antepone API_URL a cada ruta (`/auth/me` -> `/api/v1/auth/me`).
 * - Agrega `Authorization: Bearer <token>` cuando hay sesión.
 * - Convierte las respuestas de error al esquema `Error` del contrato: { codigo, mensaje, errores? }.
 *
 * Pendiente para historias posteriores: ETag/If-Match, Idempotency-Key y la cola sin conexión (RNF-11).
 */
import { API_URL } from './config'

/** Esquema `Error` de openapi_equipo.yaml. */
export interface ErrorApi {
  codigo: string
  mensaje: string
  errores?: { campo?: string; mensaje: string }[]
}

export class ApiError extends Error {
  readonly status: number
  readonly codigo: string
  readonly errores?: ErrorApi['errores']

  constructor(status: number, cuerpo: ErrorApi) {
    super(cuerpo.mensaje)
    this.name = 'ApiError'
    this.status = status
    this.codigo = cuerpo.codigo
    this.errores = cuerpo.errores
  }
}

let token: string | null = null

/** Lo llamará el contexto de sesión al iniciar o cerrar sesión (tarea 01.3). */
export function establecerToken(nuevo: string | null): void {
  token = nuevo
}

/** Hace una petición al API y devuelve el cuerpo JSON ya tipado, o lanza ApiError. */
export async function solicitar<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  const headers = new Headers(opciones.headers)
  headers.set('Accept', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (opciones.body && !(opciones.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  let respuesta: Response
  try {
    respuesta = await fetch(`${API_URL}${ruta}`, { ...opciones, headers })
  } catch {
    throw new ApiError(0, { codigo: 'SIN_CONEXION', mensaje: 'No se pudo conectar con el servidor' })
  }

  return interpretar<T>(respuesta)
}

/** Lee una respuesta: JSON si es exitosa, ApiError con el esquema del contrato si no. */
export async function interpretar<T>(respuesta: Response): Promise<T> {
  if (respuesta.status === 204) return undefined as T

  const esJson = respuesta.headers.get('Content-Type')?.includes('application/json')
  const cuerpo: unknown = esJson ? await respuesta.json() : undefined

  if (!respuesta.ok) {
    const error =
      cuerpo && typeof cuerpo === 'object' && 'codigo' in cuerpo
        ? (cuerpo as ErrorApi)
        : { codigo: 'ERROR_HTTP', mensaje: `El servidor respondió ${respuesta.status}` }
    throw new ApiError(respuesta.status, error)
  }
  return cuerpo as T
}
