// Tablero de tiempos, incidencias recurrentes y adopción (RF-13) y exportación a PDF para el comité (RF-23).
import { useState } from 'react'
import Alerta from '../components/Alerta.jsx'
import Button from '../components/Button.jsx'
import Card from '../components/Card.jsx'
import { Cargando, ErrorCarga, Pagina } from '../components/Estados.jsx'
import Input from '../components/Input.jsx'
import { ESTADOS } from '../lib/etiquetas.js'
import { useCarga } from '../lib/useCarga.js'
import { metricasService } from '../services/metricasService.js'

const iso = (d) => d.toISOString().slice(0, 10)
const hace30 = () => { const d = new Date(); d.setDate(d.getDate() - 30); return iso(d) }
const pct = (b) => (b?.porcentaje === null || b?.porcentaje === undefined ? '—' : `${b.porcentaje} % (${b.cumplen} de ${b.reportes})`)
const num = (x, u) => (x === null || x === undefined ? '—' : `${x} ${u}`)

function Indicador({ titulo, valor, detalle }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <p className="text-sm text-slate-600">{titulo}</p>
      <p className="text-2xl font-bold">{valor}</p>
      {detalle && <p className="text-sm text-slate-600">{detalle}</p>}
    </div>
  )
}

export default function Tablero() {
  const [rango, setRango] = useState(() => ({ desde: hace30(), hasta: iso(new Date()) }))
  const [consulta, setConsulta] = useState(() => rango)
  const [errorPdf, setErrorPdf] = useState(null)
  const [bajando, setBajando] = useState(false)
  const t = useCarga(() => metricasService.tablero(consulta.desde, consulta.hasta), [consulta])

  async function pdf() {
    setBajando(true)
    setErrorPdf(null)
    try {
      const blob = await metricasService.pdf(consulta.desde, consulta.hasta)
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `tablero_${consulta.desde}_${consulta.hasta}.pdf`
      a.click()
      URL.revokeObjectURL(a.href)
    } catch (e) {
      setErrorPdf(e)
    } finally {
      setBajando(false)
    }
  }

  const d = t.datos
  return (
    <Pagina titulo="Tablero" acciones={<Button variante="secundario" onClick={pdf} cargando={bajando} disabled={!d}>Exportar PDF</Button>}>
      <form className="mb-6 flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); setConsulta(rango) }}>
        <Input label="Aviso desde" type="date" value={rango.desde} onChange={(e) => setRango({ ...rango, desde: e.target.value })} />
        <Input label="Aviso hasta" type="date" value={rango.hasta} onChange={(e) => setRango({ ...rango, hasta: e.target.value })} />
        <Button type="submit">Consultar</Button>
      </form>
      {errorPdf && <div className="mb-4"><Alerta titulo="No se pudo exportar">{errorPdf.message}</Alerta></div>}
      {t.cargando && <Cargando />}
      {t.error && <ErrorCarga error={t.error} onReintentar={t.recargar} />}
      {d && (
        <div className="flex flex-col gap-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <Indicador titulo="Reportes en el periodo" valor={Object.values(d.porEstado).reduce((a, b) => a + b, 0)} />
            <Indicador titulo="Adopción (reportados por el sistema)" valor={d.adopcionPorcentaje === null || d.adopcionPorcentaje === undefined ? '—' : `${d.adopcionPorcentaje} %`} />
            <Indicador titulo="Reaperturas" valor={d.reaperturas} detalle="No cuentan como reportes nuevos" />
          </div>
          <Card titulo="Tiempos y cumplimiento por prioridad" subtitulo="Medidos desde la fecha de aviso, contra los objetivos configurados.">
            <div className="overflow-x-auto rounded focus-visible:outline-2 focus-visible:outline-blue-700" tabIndex={0} role="region" aria-label="Tabla de tiempos por prioridad (desplazable)">
              <table className="w-full text-left text-sm">
                <thead><tr className="border-b"><th className="py-2 pr-3">Prioridad</th><th className="pr-3">1.ª atención prom.</th><th className="pr-3">Resolución prom.</th>
                  <th className="pr-3">Cumpl. 1.ª atención · propio / externos</th><th>Cumpl. resolución · propio / externos</th></tr></thead>
                <tbody>
                  {d.porPrioridad.map((p) => (
                    <tr key={p.prioridad} className="border-b border-slate-100">
                      <td className="py-2 pr-3 font-medium">{p.prioridad}</td>
                      <td className="pr-3">{num(p.primeraAtencionPromedioMin, 'min')}</td>
                      <td className="pr-3">{num(p.resolucionPromedioHoras, 'h')}</td>
                      <td className="pr-3">{p.cumplimientoPrimeraAtencion ? `${pct(p.cumplimientoPrimeraAtencion.personalPropio)} / ${pct(p.cumplimientoPrimeraAtencion.proveedoresExternos)}` : 'Sin objetivo'}</td>
                      <td>{pct(p.cumplimientoResolucion.personalPropio)} / {pct(p.cumplimientoResolucion.proveedoresExternos)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          <div className="grid gap-4 sm:grid-cols-2">
            <Card titulo="Por estado">
              <ul>{Object.entries(d.porEstado).map(([k, v]) => <li key={k} className="flex justify-between"><span>{ESTADOS[k]}</span><span className="font-medium">{v}</span></li>)}</ul>
            </Card>
            <Card titulo="Por categoría">
              <ul>{Object.entries(d.porCategoria).map(([k, v]) => <li key={k} className="flex justify-between gap-2"><span>{k}</span><span className="font-medium">{v}</span></li>)}</ul>
            </Card>
          </div>
          <Card titulo="Incidencias recurrentes" subtitulo="Misma categoría y ubicación de origen, 3 o más veces en los últimos 90 días.">
            {d.recurrentes.length === 0 ? <p className="text-slate-700">No hay incidencias recurrentes.</p> : (
              <ul className="flex flex-col gap-1">{d.recurrentes.map((x) => <li key={x.categoria + x.ubicacionOrigen}><span className="font-medium">{x.categoria} — {x.ubicacionOrigen}</span>: {x.folios.join(', ')}</li>)}</ul>
            )}
          </Card>
          {d.detenciones.length > 0 && (
            <Card titulo="Tiempo detenido">
              <ul>{d.detenciones.map((x) => <li key={x.folio}>{x.folio}: {x.horasDetenido} h · {x.motivos.join(', ')}</li>)}</ul>
            </Card>
          )}
        </div>
      )}
    </Pagina>
  )
}
