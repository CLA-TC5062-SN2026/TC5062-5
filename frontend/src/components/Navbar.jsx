import { useState } from 'react'
import { Link } from 'react-router-dom'

// enlaces: [{ to, label, roles? }] — sin `roles`, el enlace lo ve cualquier usuario autenticado.
export default function Navbar({ marca = 'ReportaYa', enlaces = [], usuario, onLogout }) {
  const [abierto, setAbierto] = useState(false)
  const visibles = enlaces.filter((e) => !e.roles || e.roles.includes(usuario?.rol))
  const cerrar = () => setAbierto(false)

  return (
    <nav aria-label="Principal" className="bg-blue-700 text-white [&_a]:rounded [&_a]:focus-visible:outline-2 [&_a]:focus-visible:outline-offset-2 [&_a]:focus-visible:outline-white">
      <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-bold" onClick={cerrar}>{marca}</Link>
        <button
          className="rounded md:hidden focus-visible:outline-2 focus-visible:outline-white"
          onClick={() => setAbierto(!abierto)}
          aria-label={abierto ? 'Cerrar menú' : 'Abrir menú'}
          aria-expanded={abierto}
          aria-controls="menu-principal"
        >
          <svg aria-hidden="true" className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <div id="menu-principal" className={`${abierto ? 'flex' : 'hidden'} w-full flex-col gap-2 pt-3 md:flex md:w-auto md:flex-row md:items-center md:gap-6 md:pt-0`}>
          {usuario ? (
            <>
              {visibles.map((e) => <Link key={e.to} to={e.to} onClick={cerrar}>{e.label}</Link>)}
              <span className="text-sm text-blue-50">{usuario.nombre} · {usuario.rol}</span>
              <button onClick={() => { cerrar(); onLogout() }} className="rounded bg-white px-3 py-1 text-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white">Salir</button>
            </>
          ) : (
            <Link to="/login" className="rounded bg-white px-3 py-1 text-blue-700" onClick={cerrar}>Iniciar sesión</Link>
          )}
        </div>
      </div>
    </nav>
  )
}
