import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'
import Inicio from './pages/Inicio.jsx'
import Login from './pages/Login.jsx'
import Reportes from './pages/Reportes.jsx'

const enlaces = [
  { to: '/', label: 'Inicio' },
  { to: '/reportes', label: 'Reportes' },
]

function Layout() {
  const { usuario, logout } = useAuth()
  return (
    <>
      <Navbar enlaces={enlaces} usuario={usuario} onLogout={logout} />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<Inicio />} />
          <Route path="/reportes" element={<Reportes />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Layout />
      </BrowserRouter>
    </AuthProvider>
  )
}
