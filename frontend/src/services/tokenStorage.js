// Único lugar que sabe dónde vive la sesión en el cliente.
// sessionStorage: sobrevive a recargar la página, pero se borra al cerrar la pestaña (ver capa_servicios.md).
const CLAVE = 'reportaya.sesion'

export function leerSesion() {
  try {
    return JSON.parse(sessionStorage.getItem(CLAVE))
  } catch {
    return null
  }
}

export function guardarSesion(sesion) {
  sessionStorage.setItem(CLAVE, JSON.stringify(sesion))
}

export function borrarSesion() {
  sessionStorage.removeItem(CLAVE)
}

export const leerToken = () => leerSesion()?.token ?? null

// RNF-06: el backend devuelve un token nuevo en cada respuesta; el plazo de 30 min corre desde la última actividad.
export function renovarToken(token) {
  const s = leerSesion()
  if (!s) return
  guardarSesion({ ...s, token, expiraEn: Date.now() + 30 * 60 * 1000 })
}
