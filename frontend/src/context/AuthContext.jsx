import { createContext, useContext, useState } from 'react'
import { api } from '../services/api.js'

const AuthContext = createContext(null)
const CLAVE = 'reportaya.sesion'

// sessionStorage: sobrevive a recargar la página, pero se borra al cerrar la pestaña.
function leerSesion() {
  try {
    return JSON.parse(sessionStorage.getItem(CLAVE))
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [sesion, setSesion] = useState(leerSesion) // { token, usuario }

  async function login(correo, password) {
    const datos = await api('/auth/login', { method: 'POST', body: JSON.stringify({ correo, password }) })
    const nueva = { token: datos.token, usuario: datos.usuario }
    sessionStorage.setItem(CLAVE, JSON.stringify(nueva))
    setSesion(nueva)
  }

  function logout() {
    sessionStorage.removeItem(CLAVE)
    setSesion(null)
  }

  return (
    <AuthContext.Provider value={{ token: sesion?.token, usuario: sesion?.usuario, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

// eslint-disable-next-line react/only-export-components -- el hook vive junto a su proveedor
export const useAuth = () => useContext(AuthContext)
