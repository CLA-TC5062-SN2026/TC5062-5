import { useState } from 'react'
import { Link } from 'react-router-dom'

// enlaces: [{ to, label, roles? }] — sin `roles`, el enlace lo ve cualquier usuario autenticado.
export default function Navbar({ marca = 'ReportaYa', enlaces = [], usuario, onLogout }) {
  const [abierto, setAbierto] = useState(false)
  const visibles = enlaces.filter((e) => !e.roles || e.roles.includes(usuario?.rol))
  const cerrar = () => setAbierto(false)

  return (
    <nav className="bg-blue-600 text-white">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-bold" onClick={cerrar}>{marca}</Link>
        <button className="md:hidden" onClick={() => setAbierto(!abierto)}>
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <div className={`${abierto ? 'flex' : 'hidden'} w-full flex-col gap-2 pt-3 md:flex md:w-auto md:flex-row md:items-center md:gap-6 md:pt-0`}>
          {usuario ? (
            <>
              {visibles.map((e) => <Link key={e.to} to={e.to} onClick={cerrar}>{e.label}</Link>)}
              <span className="text-sm text-blue-200">{usuario.nombre} · {usuario.rol}</span>
              <button onClick={() => { cerrar(); onLogout() }} className="rounded bg-white px-3 py-1 text-blue-600">Salir</button>
            </>
          ) : (
            <Link to="/login" className="rounded bg-white px-3 py-1 text-blue-600" onClick={cerrar}>Iniciar sesión</Link>
          )}
        </div>
      </div>
    </nav>
  )
}
