// Cliente HTTP mínimo: antepone la URL base del API y, si hay token, la cabecera Authorization.
const API_URL = import.meta.env.VITE_API_URL ?? '/api/v1'

export async function api(ruta, { token, ...opciones } = {}) {
  const headers = { 'Content-Type': 'application/json', ...opciones.headers }
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(`${API_URL}${ruta}`, { ...opciones, headers })
  const datos = res.status === 204 ? null : await res.json().catch(() => null)
  if (!res.ok) {
    // El backend responde con el esquema Error del openapi: { codigo, mensaje }
    throw Object.assign(new Error(datos?.mensaje ?? `Error ${res.status}`), { status: res.status, datos })
  }
  return datos
}
