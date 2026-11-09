import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'
import Inicio from './pages/Inicio.jsx'

const enlaces = [
  { to: '/', label: 'Inicio' },
  { to: '/reportes', label: 'Reportes' },
  { to: '/usuarios', label: 'Usuarios', roles: ['Administracion'] },
]

function Layout() {
  const { usuario, logout } = useAuth()
  return (
    <>
      <Navbar enlaces={enlaces} usuario={usuario} onLogout={logout} />
      <Routes>
        <Route path="*" element={<Inicio />} />
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
