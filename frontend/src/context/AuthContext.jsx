import { createContext, useContext, useState } from 'react'
import { api } from '../services/api.js'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [sesion, setSesion] = useState(null) // { token, usuario }

  async function login(correo, password) {
    const datos = await api('/auth/login', { method: 'POST', body: JSON.stringify({ correo, password }) })
    setSesion({ token: datos.token, usuario: datos.usuario })
  }

  const logout = () => setSesion(null)

  return (
    <AuthContext.Provider value={{ token: sesion?.token, usuario: sesion?.usuario, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
