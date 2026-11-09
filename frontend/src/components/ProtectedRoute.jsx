import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext.jsx'

// Envuelve rutas que requieren sesión. Sin token, manda al login y recuerda a dónde se quería ir.
// (La autorización real por rol la sigue aplicando el backend: RNF-05.)
export default function ProtectedRoute() {
  const { token } = useAuth()
  const location = useLocation()
  if (!token) return <Navigate to="/login" replace state={{ desde: location.pathname }} />
  return <Outlet />
}
