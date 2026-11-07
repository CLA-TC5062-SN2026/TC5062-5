import { ApiError, interpretar } from './apiClient'
import { HEALTH_URL } from './config'

/** Respuesta de `GET /health` del backend (diagnóstico, fuera del contrato OpenAPI). */
export interface EstadoServidor {
  estado: string
  baseDeDatos: string
  tablas: number
  llavesForaneas: boolean
}

/** Verifica que el backend responde y que su base de datos está accesible. */
export async function consultarSalud(): Promise<EstadoServidor> {
  try {
    const respuesta = await fetch(HEALTH_URL, { headers: { Accept: 'application/json' } })
    return await interpretar<EstadoServidor>(respuesta)
  } catch (e) {
    if (e instanceof ApiError) throw e
    throw new ApiError(0, { codigo: 'SIN_CONEXION', mensaje: 'No se pudo conectar con el servidor' })
  }
}
