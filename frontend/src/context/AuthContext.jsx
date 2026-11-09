import { createContext, useContext, useEffect, useState } from 'react'
import { EVENTO_SESION_EXPIRADA } from '../services/apiClient.js'
import { authService } from '../services/authService.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [sesion, setSesion] = useState(() => authService.sesionActual()) // { token, usuario, expiraEn }
  const [aviso, setAviso] = useState('') // motivo por el que se cerró la sesión, para mostrarlo en el login

  // El apiClient emite este evento cuando el backend responde 401 a una petición con token.
  useEffect(() => {
    const expirar = () => {
      setSesion(null)
      setAviso('Tu sesión expiró. Inicia sesión de nuevo.')
    }
    window.addEventListener(EVENTO_SESION_EXPIRADA, expirar)
    return () => window.removeEventListener(EVENTO_SESION_EXPIRADA, expirar)
  }, [])

  async function login(correo, password) {
    setSesion(await authService.login(correo, password))
    setAviso('')
  }

  function logout() {
    authService.logout()
    setSesion(null)
  }

  return (
    <AuthContext.Provider value={{ token: sesion?.token, usuario: sesion?.usuario, aviso, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react/only-export-components -- el hook vive junto a su proveedor
export const useAuth = () => useContext(AuthContext)
