// Recurso /auth del openapi_equipo.yaml.
import { apiClient } from './apiClient.js'
import { borrarSesion, guardarSesion, leerSesion } from './tokenStorage.js'

export const authService = {
  // POST /auth/login → { token, tipo, expiraEn, usuario: SesionUsuario }
  async login(correo, password) {
    const datos = await apiClient.post('/auth/login', { correo, password }, { auth: false })
    const sesion = { token: datos.token, usuario: datos.usuario, expiraEn: Date.now() + datos.expiraEn * 1000 }
    guardarSesion(sesion)
    return sesion
  },

  // GET /auth/me → SesionUsuario (valida que el token siga vigente)
  me: () => apiClient.get('/auth/me'),

  logout() {
    borrarSesion()
  },

  // Sesión guardada si el token no ha expirado; si expiró, se descarta sin esperar al 401 del backend.
  sesionActual() {
    const s = leerSesion()
    if (s?.expiraEn && s.expiraEn <= Date.now()) {
      borrarSesion()
      return null
    }
    return s
  },
}
