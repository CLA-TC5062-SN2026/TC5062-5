// Envíos guardados en el dispositivo sin señal (RNF-11): el usuario distingue «Pendiente» de «Enviado».
import { Link } from 'react-router-dom'
import Button from '../components/Button.jsx'
import Card from '../components/Card.jsx'
import { Pagina } from '../components/Estados.jsx'
import { Etiqueta } from '../components/Insignias.jsx'
import { useCola } from '../context/ColaContext.jsx'
import { fecha } from '../lib/etiquetas.js'

const COLOR = { Pendiente: 'bg-amber-100 text-amber-900', Enviado: 'bg-emerald-100 text-emerald-900', Rechazado: 'bg-rose-100 text-rose-900' }

export default function Pendientes() {
  const { items, enLinea, procesar, descartar } = useCola()
  return (
    <Pagina titulo="Envíos sin conexión" acciones={<Button variante="secundario" onClick={procesar} disabled={!enLinea}>Reintentar ahora</Button>}>
      <p className="mb-4 text-slate-700">
        Lo que captures sin señal se guarda en este dispositivo, con sus fotos, y se envía solo cuando vuelve la conexión.
        {!enLinea && <strong> Ahora no hay conexión.</strong>}
      </p>
      {items.length === 0 ? <p className="text-slate-700">No hay envíos guardados.</p> : (
        <Card>
          <ul className="divide-y divide-slate-100">
            {[...items].reverse().map((i) => (
              <li key={i.id} className="flex flex-wrap items-start justify-between gap-2 py-3">
                <div>
                  <p className="font-medium">{i.resumen}</p>
                  <p className="text-sm text-slate-600">
                    {i.tipo === 'reporte' ? 'Reporte nuevo' : `Terminar ${i.folio}`} · capturado {fecha(i.creado)}
                    {i.enviado && ` · enviado ${fecha(i.enviado)}`}
                  </p>
                  {i.error && <p className="text-sm text-red-800">{i.error}</p>}
                </div>
                <div className="flex items-center gap-2">
                  <Etiqueta color={COLOR[i.estado]}>{i.estado}</Etiqueta>
                  {i.estado === 'Enviado' && i.folio && <Link className="whitespace-nowrap font-mono text-blue-700 underline" to={`/reportes/${i.folio}`}>{i.folio}</Link>}
                  {i.estado !== 'Pendiente' && <Button variante="secundario" onClick={() => descartar(i.id)}>Quitar de la lista</Button>}
                </div>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </Pagina>
  )
}
