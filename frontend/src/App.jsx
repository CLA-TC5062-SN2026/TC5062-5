import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'
import { ColaProvider, useCola } from './context/ColaContext.jsx'
import Avisos from './pages/Avisos.jsx'
import { Activar, Recuperar, Restablecer } from './pages/Cuenta.jsx'
import DetalleReporte from './pages/DetalleReporte.jsx'
import Inicio from './pages/Inicio.jsx'
import Login from './pages/Login.jsx'
import NuevoReporte from './pages/NuevoReporte.jsx'
import Pendientes from './pages/Pendientes.jsx'
import Reportes from './pages/Reportes.jsx'
import Tablero from './pages/Tablero.jsx'
import Usuarios from './pages/Usuarios.jsx'

const enlaces = [
  { to: '/', label: 'Inicio' },
  { to: '/reportes', label: 'Reportes' },
  { to: '/reportes/nuevo', label: 'Nuevo reporte', roles: ['Residente', 'Vigilancia', 'Administracion'] },
  { to: '/tablero', label: 'Tablero', roles: ['Administracion'] },
  { to: '/usuarios', label: 'Usuarios', roles: ['Administracion'] },
  { to: '/avisos', label: 'Avisos' },
]

function Layout() {
  const { usuario, logout } = useAuth()
  const { enLinea, pendientes } = useCola()
  return (
    <>
      <Navbar enlaces={enlaces} usuario={usuario} onLogout={logout}
        extra={usuario && pendientes > 0 && <Link to="/pendientes" className="rounded bg-amber-300 px-2 py-0.5 font-semibold text-slate-900">{pendientes} sin enviar</Link>} />
      {!enLinea && (
        <p role="status" className="bg-amber-100 px-4 py-2 text-center text-amber-950">
          Sin conexión. Puedes consultar lo ya cargado y capturar reportes o terminados: se enviarán solos al volver la señal.
        </p>
      )}
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/activar" element={<Activar />} />
        <Route path="/recuperar" element={<Recuperar />} />
        <Route path="/restablecer" element={<Restablecer />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Inicio />} />
          <Route path="/reportes" element={<Reportes />} />
          <Route path="/reportes/nuevo" element={<NuevoReporte />} />
          <Route path="/reportes/:folio" element={<DetalleReporte />} />
          <Route path="/avisos" element={<Avisos />} />
          <Route path="/pendientes" element={<Pendientes />} />
          <Route path="/tablero" element={<Tablero />} />
          <Route path="/usuarios" element={<Usuarios />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <ColaProvider>
        <BrowserRouter>
          <Layout />
        </BrowserRouter>
      </ColaProvider>
    </AuthProvider>
  )
}
