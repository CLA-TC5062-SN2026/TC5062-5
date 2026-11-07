import { EstadoApi } from '../components/EstadoApi'

/** Página inicial provisional; la sustituyen el login y la vista de cada rol (tareas 06.3 y 01.3). */
export function InicioPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Bienvenido a ReportaYa</h1>
        <p className="mt-2 text-texto-suave">
          Reporte y dé seguimiento a las incidencias de mantenimiento del condominio.
        </p>
      </div>
      <EstadoApi />
    </div>
  )
}
