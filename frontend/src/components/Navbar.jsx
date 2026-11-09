import { useState } from 'react'
import { Link } from 'react-router-dom'

export default function Navbar({ enlaces = [], usuario, onLogout }) {
  const [abierto, setAbierto] = useState(false)

  return (
    <nav className="bg-blue-600 text-white">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-bold">ReportaYa</Link>
        <button className="md:hidden" onClick={() => setAbierto(!abierto)}>
          <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <div className={`${abierto ? 'flex' : 'hidden'} w-full flex-col gap-2 pt-3 md:flex md:w-auto md:flex-row md:items-center md:gap-6 md:pt-0`}>
          {usuario ? (
            <>
              {enlaces.map((e) => <Link key={e.to} to={e.to}>{e.label}</Link>)}
              <span className="text-sm text-blue-200">{usuario.nombre}</span>
              <button onClick={onLogout} className="rounded bg-white px-3 py-1 text-blue-600">Salir</button>
            </>
          ) : (
            <Link to="/login" className="rounded bg-white px-3 py-1 text-blue-600">Iniciar sesión</Link>
          )}
        </div>
      </div>
    </nav>
  )
}
