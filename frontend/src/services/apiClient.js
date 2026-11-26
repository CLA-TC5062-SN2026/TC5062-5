// Cliente HTTP de la aplicación: envuelve fetch con un "interceptor" de petición (URL base + JWT)
// y uno de respuesta (manejo de errores centralizado). Los servicios por recurso usan solo este módulo.
import { borrarSesion, leerSesion, leerToken, renovarToken } from './tokenStorage.js'

const API_URL = import.meta.env.VITE_API_URL ?? '/api/v1'
const TIEMPO_LIMITE_MS = 60000 // las fotos de hasta 10 MB tardan en subir con mala señal (RNF-04)
export const EVENTO_SESION_EXPIRADA = 'reportaya:sesion-expirada'

// Error único que ven los componentes: siempre trae un `mensaje` listo para mostrarse al usuario.
export class ApiError extends Error {
  constructor(mensaje, { status = 0, codigo = 'ERROR_DE_RED', errores = [] } = {}) {
    super(mensaje)
    this.name = 'ApiError'
    this.status = status
    this.codigo = codigo
    this.errores = errores // [{ campo, mensaje }] en errores de validación (422)
  }
}

// Mensajes por código HTTP cuando el backend no manda uno propio (esquema Error del openapi: { codigo, mensaje }).
const MENSAJES = {
  400: 'La solicitud no es válida. Revisa los datos e inténtalo de nuevo.',
  401: 'Tu sesión expiró o no es válida. Inicia sesión de nuevo.',
  403: 'No tienes permiso para realizar esta acción con tu rol.',
  404: 'No encontramos lo que buscas. Puede que ya no exista.',
  409: 'La acción no está permitida en el estado actual del reporte.',
  412: 'Alguien más modificó este registro. Recarga la página e inténtalo de nuevo.',
  422: 'Hay datos inválidos en el formulario.',
  429: 'Demasiadas solicitudes. Espera un momento e inténtalo de nuevo.',
  500: 'Ocurrió un error en el servidor. Inténtalo más tarde.',
  503: 'El servidor no está disponible en este momento. Inténtalo más tarde.',
}

// --- Interceptor de petición -------------------------------------------------------------------
function prepararPeticion(ruta, { auth = true, body, headers, conEncabezados, binario, ...opciones }) { // eslint-disable-line no-unused-vars
  const h = { Accept: 'application/json', ...headers }
  const token = auth ? leerToken() : null
  if (token) h.Authorization = `Bearer ${token}`
  if (body !== undefined && !(body instanceof FormData)) {
    h['Content-Type'] ??= 'application/json'
    body = JSON.stringify(body)
  }
  return { url: `${API_URL}${ruta}`, init: { ...opciones, headers: h, body }, conToken: Boolean(token) }
}

// --- Interceptor de respuesta ------------------------------------------------------------------
async function procesarRespuesta(res, conToken, { conEncabezados = false, binario = false } = {}) {
  // RNF-06: cada respuesta autenticada trae un token renovado; así la sesión vence por inactividad.
  const renovado = res.headers.get('X-Token-Renovado')
  if (renovado && conToken) renovarToken(renovado)
  if (res.ok && binario) return res.blob()
  const datos = res.status === 204 ? null : await res.json().catch(() => null)
  if (res.ok) return conEncabezados ? { datos, etag: res.headers.get('ETag') } : datos

  // 401 con token = sesión vencida o inválida: se limpia y se avisa a la app (AuthContext redirige al login).
  // 401 sin token (p. ej. credenciales incorrectas en /auth/login) se muestra tal cual.
  if (res.status === 401 && conToken) {
    borrarSesion()
    window.dispatchEvent(new Event(EVENTO_SESION_EXPIRADA))
  }
  const mensaje = datos?.mensaje && res.status < 500 ? datos.mensaje : (MENSAJES[res.status] ?? `Error inesperado (${res.status}).`)
  throw new ApiError(mensaje, { status: res.status, codigo: datos?.codigo ?? 'HTTP_' + res.status, errores: datos?.errores ?? [] })
}

function errorDeRed(e) {
  if (e.name === 'AbortError') {
    return new ApiError('El servidor tardó demasiado en responder. Revisa tu conexión e inténtalo de nuevo.', { codigo: 'TIEMPO_AGOTADO' })
  }
  return new ApiError('No se pudo conectar con el servidor. Revisa tu conexión a internet e inténtalo de nuevo.')
}

// --- Lectura sin conexión (RNF-11) ------------------------------------------------------------------
// Las consultas de reportes que ya se cargaron se guardan por usuario; sin señal se devuelven marcadas.
const PREFIJO_CACHE = 'reportaya.cache:'
// Lo que se consulta en campo: reportes (lista y detalle) y los catálogos del formulario de alta.
const RUTAS_EN_CACHE = ['/reports', '/categories', '/common-areas', '/units', '/assignees']
const cacheable = (ruta, opciones) => (opciones.method ?? 'GET') === 'GET' && !opciones.binario && RUTAS_EN_CACHE.some((r) => ruta.startsWith(r))
const claveCache = (ruta) => `${PREFIJO_CACHE}${leerSesion()?.usuario?.id ?? 'anonimo'}:${ruta}`

function guardarEnCache(ruta, datos) {
  try {
    localStorage.setItem(claveCache(ruta), JSON.stringify({ datos, guardado: Date.now() }))
  } catch {
    // almacenamiento lleno: la lectura sin conexión es un extra, nunca bloquea
  }
}

export function leerDeCache(ruta) {
  try {
    return JSON.parse(localStorage.getItem(claveCache(ruta)))
  } catch {
    return null
  }
}

export function borrarCache() {
  Object.keys(localStorage).filter((k) => k.startsWith(PREFIJO_CACHE)).forEach((k) => localStorage.removeItem(k))
}

export async function request(ruta, opciones = {}) {
  try {
    const datos = await requestEnRed(ruta, opciones)
    if (cacheable(ruta, opciones)) guardarEnCache(ruta, datos)
    return datos
  } catch (e) {
    const guardado = cacheable(ruta, opciones) && ['ERROR_DE_RED', 'TIEMPO_AGOTADO'].includes(e.codigo) ? leerDeCache(ruta) : null
    if (!guardado) throw e
    const datos = guardado.datos
    // Marca la respuesta para que la pantalla avise «sin conexión: datos del …».
    const marca = { sinConexion: true, guardado: guardado.guardado }
    return Array.isArray(datos) ? Object.assign([...datos], marca) : { ...datos, ...marca }
  }
}

async function requestEnRed(ruta, opciones = {}) {
  const { url, init, conToken } = prepararPeticion(ruta, opciones)
  const control = new AbortController()
  const temporizador = setTimeout(() => control.abort(), TIEMPO_LIMITE_MS)
  if (opciones.signal) opciones.signal.addEventListener('abort', () => control.abort())
  let res
  try {
    res = await fetch(url, { ...init, signal: control.signal })
  } catch (e) {
    if (opciones.signal?.aborted) throw e // la canceló el componente (se desmontó): no es un error para el usuario
    throw errorDeRed(e)
  } finally {
    clearTimeout(temporizador)
  }
  return procesarRespuesta(res, conToken, opciones)
}

// Convierte un objeto de filtros en query string, omitiendo vacíos.
export function query(params = {}) {
  const q = new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ''))
  return q.size ? `?${q}` : ''
}

export const apiClient = {
  get: (ruta, op) => request(ruta, { ...op, method: 'GET' }),
  post: (ruta, body, op) => request(ruta, { ...op, method: 'POST', body }),
  patch: (ruta, body, op) => request(ruta, { ...op, method: 'PATCH', body }),
  put: (ruta, body, op) => request(ruta, { ...op, method: 'PUT', body }),
  delete: (ruta, op) => request(ruta, { ...op, method: 'DELETE' }),
  // PATCH con application/merge-patch+json (RFC 7396) e If-Match con el ETag del último GET.
  mergePatch: (ruta, body, etag, op) =>
    request(ruta, { ...op, method: 'PATCH', body, headers: { 'Content-Type': 'application/merge-patch+json', 'If-Match': etag ?? '*' } }),
  putConVersion: (ruta, body, etag, op) =>
    request(ruta, { ...op, method: 'PUT', body, headers: { 'If-Match': etag ?? '*' } }),
  blob: (ruta, op) => request(ruta, { ...op, method: 'GET', binario: true }),
}
