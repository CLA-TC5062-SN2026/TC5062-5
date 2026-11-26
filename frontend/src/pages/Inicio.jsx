import { Link } from 'react-router-dom'
import Card from '../components/Card.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { ROLES } from '../lib/etiquetas.js'

// Destino después del login: atajos según el rol.
const ATAJOS = {
  Residente: [['/reportes/nuevo', 'Reportar una falla', 'Desde tu departamento o un área común, con fotos.'],
    ['/reportes', 'Mis reportes', 'Estado, visita programada y confirmación de la reparación.'], ['/avisos', 'Avisos', 'Novedades de tus reportes.']],
  Vigilancia: [['/reportes/nuevo', 'Registrar un reporte', 'Avisos de la caseta o de residentes sin cuenta.'], ['/reportes', 'Reportes que registré', '']],
  Mantenimiento: [['/reportes', 'Mis asignados', 'Ordenados por prioridad y antigüedad.'], ['/avisos', 'Avisos', 'Asignaciones nuevas.']],
  Administracion: [['/reportes', 'Reportes', 'Buscar, asignar, cerrar y dar seguimiento.'], ['/reportes/nuevo', 'Capturar un reporte', 'Recibido por WhatsApp, llamada o en persona.'],
    ['/tablero', 'Tablero', 'Tiempos, cumplimiento, recurrencia y adopción.'], ['/usuarios', 'Usuarios', 'Altas y enlaces de activación.'], ['/avisos', 'Avisos y correos', '']],
}

export default function Inicio() {
  const { usuario } = useAuth()
  return (
    <main className="mx-auto max-w-5xl p-4 sm:p-8">
      <h1 className="text-2xl font-bold sm:text-3xl">Hola, {usuario?.nombre}</h1>
      <p className="mt-1 text-slate-600">{ROLES[usuario?.rol]}{usuario?.unidad && ` · ${usuario.unidad.etiqueta}`}{usuario?.perfilAdministracion && ` · ${usuario.perfilAdministracion}`}</p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {(ATAJOS[usuario?.rol] ?? []).map(([to, titulo, texto]) => (
          <Card key={to} titulo={titulo} pie={<Link to={to} className="font-medium text-blue-700 underline">Abrir</Link>}>
            <p>{texto}</p>
          </Card>
        ))}
      </div>
    </main>
  )
}
