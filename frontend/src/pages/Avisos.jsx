// Avisos en el sistema (RF-11) y, para la Administración, la bitácora de correos con su estado.
import { useState } from 'react'
import { Link } from 'react-router-dom'
import Button from '../components/Button.jsx'
import Card from '../components/Card.jsx'
import { Cargando, ErrorCarga, Pagina } from '../components/Estados.jsx'
import { Etiqueta } from '../components/Insignias.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { fecha } from '../lib/etiquetas.js'
import { useCarga } from '../lib/useCarga.js'
import { avisosService } from '../services/avisosService.js'

const COLOR_CORREO = { Enviado: 'bg-emerald-100 text-emerald-900', Pendiente: 'bg-amber-100 text-amber-900', Fallido: 'bg-rose-100 text-rose-900' }

function Correos() {
  const [estado, setEstado] = useState('')
  const c = useCarga(() => avisosService.correos(estado ? { estado } : {}), [estado])
  return (
    <Card titulo="Correos enviados" subtitulo="Si el servicio de correo falla, se reintenta 3 veces cada 10 minutos; después queda «Fallido».">
      <div className="mb-3 flex flex-wrap gap-2">
        {['', 'Enviado', 'Pendiente', 'Fallido'].map((e) => (
          <Button key={e || 'todos'} variante={estado === e ? 'primario' : 'secundario'} onClick={() => setEstado(e)}>{e || 'Todos'}</Button>
        ))}
      </div>
      {c.cargando && <Cargando />}
      {c.error && <ErrorCarga error={c.error} onReintentar={c.recargar} />}
      {c.datos && (
        <ul className="divide-y divide-slate-100">
          {c.datos.items.map((x) => (
            <li key={x.id} className="flex flex-wrap items-center gap-2 py-2">
              <Etiqueta color={COLOR_CORREO[x.estado]}>{x.estado}</Etiqueta>
              <span>{x.destinatario}</span>
              <span className="text-sm text-slate-600">{x.evento} · {x.folio} · {fecha(x.fecha)} · {x.intentos} intento(s)</span>
            </li>
          ))}
          {c.datos.items.length === 0 && <li className="py-2 text-slate-700">Sin correos.</li>}
        </ul>
      )}
    </Card>
  )
}

export default function Avisos() {
  const { usuario } = useAuth()
  const a = useCarga(() => avisosService.listar(), [])
  async function leer(id) {
    await avisosService.marcarLeido(id)
    a.recargar()
  }
  return (
    <Pagina titulo="Avisos" acciones={<Button variante="secundario" onClick={a.recargar}>Actualizar</Button>}>
      <div className="flex flex-col gap-4">
        {a.cargando && <Cargando />}
        {a.error && <ErrorCarga error={a.error} onReintentar={a.recargar} />}
        {a.datos && (
          <Card titulo="Mis avisos">
            <ul className="divide-y divide-slate-100">
              {a.datos.items.map((n) => (
                <li key={n.id} className={`flex flex-wrap items-start justify-between gap-2 py-3 ${n.leido ? 'text-slate-600' : ''}`}>
                  <div>
                    <p className={n.leido ? '' : 'font-medium'}>{n.mensaje}</p>
                    <p className="text-sm text-slate-600">{fecha(n.fecha)}{n.folio && <> · <Link className="text-blue-700 underline" to={`/reportes/${n.folio}`}>{n.folio}</Link></>}</p>
                  </div>
                  {!n.leido && <Button variante="secundario" onClick={() => leer(n.id)}>Marcar leído</Button>}
                </li>
              ))}
              {a.datos.items.length === 0 && <li className="py-2 text-slate-700">No tienes avisos.</li>}
            </ul>
          </Card>
        )}
        {usuario?.rol === 'Administracion' && <Correos />}
      </div>
    </Pagina>
  )
}
