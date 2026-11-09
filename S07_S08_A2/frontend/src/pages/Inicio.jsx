import { Link } from 'react-router-dom'
import Card from '../components/Card.jsx'
import { useAuth } from '../context/AuthContext.jsx'

// Dashboard: destino después del login (ruta protegida).
export default function Inicio() {
  const { usuario } = useAuth()
  return (
    <main className="mx-auto max-w-5xl p-4 sm:p-8">
      <h1 className="text-2xl font-bold sm:text-3xl">Hola, {usuario?.nombre}</h1>
      <p className="mt-1 text-slate-600">Rol: {usuario?.rol}</p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card titulo="Reportes" subtitulo="Consulta los reportes de mantenimiento"
          pie={<Link to="/reportes" className="font-medium text-blue-700 underline">Ver reportes</Link>}>
          <p>Fugas, luminarias, daños y su estado de atención.</p>
        </Card>
      </div>
    </main>
  )
}
