// Lista de reportes. El backend decide qué ve cada rol y en qué orden (RNF-05):
// Residente: los suyos, los de su unidad y los de áreas comunes (RF-10); Vigilancia: los que registró (RF-04-AC-7);
// Mantenimiento: sus asignados por prioridad y antigüedad (RF-16); Administración: todos, con búsqueda (RF-12).
import { useState } from 'react'
import { Link } from 'react-router-dom'
import Button from '../components/Button.jsx'
import { Select } from '../components/Campos.jsx'
import { Cargando, ErrorCarga, Pagina } from '../components/Estados.jsx'
import Input from '../components/Input.jsx'
import { Estado, Etiqueta, Prioridad } from '../components/Insignias.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { ESTADOS, PRIORIDADES, fecha } from '../lib/etiquetas.js'
import { useCarga } from '../lib/useCarga.js'
import { reportesService } from '../services/reportesService.js'

const TITULOS = { Residente: 'Mis reportes', Vigilancia: 'Reportes que registré', Mantenimiento: 'Mis reportes asignados',
  Administracion: 'Reportes' }

function Filtros({ alBuscar }) {
  const [f, setF] = useState({ texto: '', estado: '', prioridad: '', avisoDesde: '', avisoHasta: '' })
  const cambiar = (k) => (e) => setF({ ...f, [k]: e.target.value })
  return (
    <form className="mb-6 grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 sm:grid-cols-2 lg:grid-cols-5"
      onSubmit={(e) => { e.preventDefault(); alBuscar(f) }} aria-label="Buscar reportes">
      <Input label="Texto en la descripción" value={f.texto} onChange={cambiar('texto')} />
      <Select label="Estado" value={f.estado} onChange={cambiar('estado')} vacio="Todos"
        opciones={Object.entries(ESTADOS).map(([valor, texto]) => ({ valor, texto }))} />
      <Select label="Prioridad" value={f.prioridad} onChange={cambiar('prioridad')} vacio="Todas"
        opciones={PRIORIDADES.map((p) => ({ valor: p, texto: p }))} />
      <Input label="Aviso desde" type="date" value={f.avisoDesde} onChange={cambiar('avisoDesde')} />
      <Input label="Aviso hasta" type="date" value={f.avisoHasta} onChange={cambiar('avisoHasta')} />
      <div className="flex gap-2 sm:col-span-2 lg:col-span-5">
        <Button type="submit">Buscar</Button>
        <Button variante="secundario" type="reset" onClick={() => { const v = { texto: '', estado: '', prioridad: '', avisoDesde: '', avisoHasta: '' }; setF(v); alBuscar(v) }}>Limpiar</Button>
      </div>
    </form>
  )
}

export default function Reportes() {
  const { usuario } = useAuth()
  const rol = usuario?.rol
  const [filtros, setFiltros] = useState({})
  const { cargando, error, datos, recargar } = useCarga((signal) => reportesService.listar({ pageSize: 50, ...filtros }, { signal }), [filtros])
  const puedeReportar = ['Residente', 'Vigilancia', 'Administracion'].includes(rol)

  return (
    <Pagina titulo={TITULOS[rol] ?? 'Reportes'}
      acciones={<>
        {puedeReportar && <Link to="/reportes/nuevo" className="rounded-lg bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700">Nuevo reporte</Link>}
        <Button variante="secundario" onClick={recargar} disabled={cargando}>Actualizar</Button>
      </>}>
      {rol === 'Administracion' && <Filtros alBuscar={(f) => setFiltros(Object.fromEntries(Object.entries(f).filter(([, v]) => v)))} />}
      {rol === 'Mantenimiento' && <p className="mb-4 text-slate-700">Ordenados por prioridad y, a igual prioridad, del aviso más antiguo al más reciente.</p>}
      <div aria-live="polite">
        {cargando && <Cargando texto="Cargando reportes…" />}
        {!cargando && error && <ErrorCarga error={error} onReintentar={recargar} titulo="No se pudieron cargar los reportes" />}
        {!cargando && datos?.items.length === 0 && <p className="text-slate-700">No hay reportes para mostrar.</p>}
        {!cargando && datos?.sinConexion && (
          <p className="mb-3 rounded-lg bg-amber-50 p-3 text-amber-900" role="status">Sin conexión: lista guardada el {fecha(new Date(datos.guardado).toISOString())}</p>
        )}
        {!cargando && datos?.items.length > 0 && (
          <>
            <p className="mb-3 text-sm text-slate-600">{datos.pagination.total} reporte(s)</p>
            <ul className="flex flex-col gap-3">
              {datos.items.map((r) => (
                <li key={r.folio}>
                  <Link to={`/reportes/${r.folio}`}
                    className="block rounded-xl border border-slate-200 bg-white p-4 shadow-sm hover:border-blue-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono font-semibold">{r.folio}</span>
                      <Estado estado={r.estado} />
                      <Prioridad prioridad={r.prioridad} />
                      {r.detenido && <Etiqueta color="bg-orange-100 text-orange-900">Detenido</Etiqueta>}
                      {r.posibleDuplicado && rol === 'Administracion' && <Etiqueta color="bg-violet-100 text-violet-900">Posible duplicado</Etiqueta>}
                    </div>
                    <p className="mt-2 font-medium">{r.categoria}{r.subtipo && ` · ${r.subtipo}`} — {r.ubicacion?.etiqueta}</p>
                    <p className="mt-1 text-slate-700">{r.descripcion}</p>
                    <p className="mt-1 text-sm text-slate-600">Aviso: {fecha(r.fechaAviso)}</p>
                    {r.mensajeAcceso && <p className="mt-2 text-sm font-medium text-red-800">{r.mensajeAcceso}</p>}
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </Pagina>
  )
}
