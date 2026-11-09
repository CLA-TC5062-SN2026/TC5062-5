import { useCallback, useEffect, useState } from 'react'
import Alerta from '../components/Alerta.jsx'
import Button from '../components/Button.jsx'
import Card from '../components/Card.jsx'
import { reportesService } from '../services/reportesService.js'

const ESTADOS = { Reportado: 'Reportado', Asignado: 'Asignado', EnProceso: 'En proceso', Terminado: 'Terminado',
  Cerrado: 'Cerrado', Cancelado: 'Cancelado', Unido: 'Unido' }

const fecha = (iso) => new Date(iso).toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' })

// Flujo de negocio E2E: listar reportes (GET /reports, RF-12).
export default function Reportes() {
  const [estado, setEstado] = useState({ cargando: true, error: null, datos: null })

  // Pide los datos y guarda el resultado (el estado de "cargando" se activa antes de llamarla).
  const cargar = useCallback(async (signal) => {
    try {
      const datos = await reportesService.listar({ pageSize: 20 }, { signal })
      setEstado({ cargando: false, error: null, datos })
    } catch (error) {
      if (signal?.aborted) return
      setEstado({ cargando: false, error, datos: null })
    }
  }, [])

  useEffect(() => {
    const control = new AbortController()
    cargar(control.signal)
    return () => control.abort()
  }, [cargar])

  function recargar() {
    setEstado((e) => ({ ...e, cargando: true, error: null }))
    cargar()
  }

  const { cargando, error, datos } = estado

  return (
    <main className="mx-auto max-w-5xl p-4 sm:p-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold sm:text-3xl">Reportes</h1>
        <Button variante="secundario" onClick={recargar} disabled={cargando}>Actualizar</Button>
      </div>

      <div aria-live="polite" className="mt-6">
        {cargando && (
          <p className="flex items-center gap-3 text-slate-700">
            <span aria-hidden="true" className="h-5 w-5 animate-spin rounded-full border-2 border-blue-700 border-t-transparent" />
            Cargando reportes…
          </p>
        )}

        {!cargando && error && (
          <Alerta titulo="No se pudieron cargar los reportes"
            accion={<Button onClick={recargar}>Reintentar</Button>}>
            {error.message}
          </Alerta>
        )}

        {!cargando && datos && datos.items.length === 0 && (
          <p className="text-slate-700">Todavía no hay reportes registrados.</p>
        )}

        {!cargando && datos?.items.length > 0 && (
          <>
            <p className="mb-4 text-sm text-slate-600">{datos.pagination.total} reporte(s)</p>
            <ul className="grid gap-4 sm:grid-cols-2">
              {datos.items.map((r) => (
                <li key={r.folio}>
                  <Card titulo={r.categoria + (r.subtipo ? ` · ${r.subtipo}` : '')}
                    subtitulo={`${r.folio} · ${r.ubicacion?.etiqueta ?? ''} · ${fecha(r.fechaAviso)}`}>
                    <p>{r.descripcion}</p>
                    <p className="mt-2 text-sm font-medium text-blue-800">
                      {ESTADOS[r.estado] ?? r.estado}{r.prioridad && ` · Prioridad ${r.prioridad}`}
                    </p>
                  </Card>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </main>
  )
}
