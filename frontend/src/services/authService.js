// Recurso /auth del openapi_equipo.yaml.
import { apiClient, borrarCache } from './apiClient.js'
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

  // RF-14: activar la cuenta y recuperar la contraseña con los enlaces de un solo uso que llegan por correo.
  activar: (token, password) => apiClient.post('/account-activations', { token, password }, { auth: false }),
  pedirRecuperacion: (correo) => apiClient.post('/password-reset-requests', { correo }, { auth: false }),
  restablecer: (token, password) => apiClient.post('/password-resets', { token, password }, { auth: false }),

  logout() {
    borrarSesion()
    borrarCache() // los datos guardados para consultar sin señal son del usuario que salió
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
