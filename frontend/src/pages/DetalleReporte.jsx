// Detalle de un reporte y sus acciones según el rol y el estado (flujo de RF-07).
// El backend ya recorta lo que cada rol puede ver (matriz 2.3); aquí solo se ofrecen las acciones que tienen sentido.
import { useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import Alerta from '../components/Alerta.jsx'
import Button from '../components/Button.jsx'
import { AreaTexto, Archivos, Select } from '../components/Campos.jsx'
import Card from '../components/Card.jsx'
import { Cargando, ErrorCarga, Exito, Pagina } from '../components/Estados.jsx'
import Foto from '../components/Foto.jsx'
import Input from '../components/Input.jsx'
import { Estado, Etiqueta, Prioridad } from '../components/Insignias.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useCola } from '../context/ColaContext.jsx'
import { esFallaDeRed, nuevaClave } from '../lib/cola.js'
import { ESTADOS, MOTIVOS_DETENCION, PAGADOR, PRIORIDADES, RESPONSABILIDAD, RESPUESTAS, aIsoLocal, fecha, soloFecha } from '../lib/etiquetas.js'
import { useCarga } from '../lib/useCarga.js'
import { catalogoService } from '../services/catalogoService.js'
import { reportesService } from '../services/reportesService.js'

// ----------------------------------------------------------------- piezas
function Dato({ titulo, children }) {
  if (children === undefined || children === null || children === '' || children === false) return null
  return (
    <div>
      <dt className="text-sm text-slate-600">{titulo}</dt>
      <dd className="font-medium">{children}</dd>
    </div>
  )
}

// Una acción del flujo: formulario propio, botón con estado de carga y error visible (con el mensaje del SRS).
function Accion({ titulo, descripcion, boton, variante, onEnviar, onHecho, children, abiertaInicial = false }) {
  const [abierta, setAbierta] = useState(abiertaInicial)
  const [error, setError] = useState(null)
  const [cargando, setCargando] = useState(false)
  async function enviar(e) {
    e.preventDefault()
    setCargando(true)
    setError(null)
    try {
      await onEnviar()
      setAbierta(false)
      onHecho(`${titulo}: listo.`)
    } catch (err) {
      if (err.guardado) { setAbierta(false); onHecho(err.message) } // sin señal: quedó en la cola del dispositivo
      else setError(err)
    } finally {
      setCargando(false)
    }
  }
  if (!abierta) return <Button variante={variante ?? 'secundario'} onClick={() => setAbierta(true)}>{titulo}</Button>
  return (
    <form onSubmit={enviar} noValidate className="flex w-full flex-col gap-3 rounded-lg border border-slate-300 bg-slate-50 p-4">
      <p className="font-semibold">{titulo}</p>
      {descripcion && <p className="text-sm text-slate-700">{descripcion}</p>}
      {children}
      {error && <Alerta titulo="No se pudo completar">{error.message}</Alerta>}
      <div className="flex flex-wrap gap-2">
        <Button type="submit" cargando={cargando}>{boton ?? titulo}</Button>
        <Button variante="secundario" onClick={() => { setAbierta(false); setError(null) }}>Cancelar</Button>
      </div>
    </form>
  )
}

// ----------------------------------------------------------------- acciones de la Administración
function Asignar({ r, onHecho }) {
  const resp = useCarga(() => catalogoService.responsables(), [])
  const [d, setD] = useState({ prioridad: r.prioridadSugerida ?? '', responsableId: '', responsabilidad: 'PorDeterminar', responsableCosto: '' })
  const op = (resp.datos ?? []).map((x) => ({ valor: x.id, texto: `${x.nombre}${x.especialidad ? ` · ${x.especialidad}` : ''}${x.sinAcceso ? ' · Sin acceso al sistema' : ''}` }))
  return (
    <Accion titulo="Asignar" variante="primario" onHecho={onHecho} descripcion={`Prioridad sugerida: ${r.prioridadSugerida}. La decisión final es de la Administración.`}
      onEnviar={() => reportesService.asignar(r.folio, Object.fromEntries(Object.entries(d).filter(([, v]) => v)))}>
      <Select label="Prioridad" required value={d.prioridad} onChange={(e) => setD({ ...d, prioridad: e.target.value })} opciones={PRIORIDADES.map((p) => ({ valor: p, texto: p }))} />
      <Select label="Responsable" required value={d.responsableId} onChange={(e) => setD({ ...d, responsableId: e.target.value })} opciones={op} />
      <Select label="Responsabilidad" value={d.responsabilidad} vacio={null} onChange={(e) => setD({ ...d, responsabilidad: e.target.value })}
        opciones={Object.entries(RESPONSABILIDAD).map(([valor, texto]) => ({ valor, texto }))} />
      <Select label="Responsable del costo" value={d.responsableCosto} vacio="Sin definir" onChange={(e) => setD({ ...d, responsableCosto: e.target.value })}
        opciones={Object.entries(PAGADOR).map(([valor, texto]) => ({ valor, texto }))} />
    </Accion>
  )
}

function Reclasificar({ r, etag, onHecho }) {
  const resp = useCarga(() => catalogoService.responsables(), [])
  const [d, setD] = useState({ prioridad: r.prioridad ?? '', responsableId: r.responsable?.id ?? '', responsabilidad: r.responsabilidad ?? '' })
  const puedeCambiarResponsable = ['Asignado', 'EnProceso'].includes(r.estado)
  function cambios() {
    const c = {}
    if (d.prioridad && d.prioridad !== r.prioridad) c.prioridad = d.prioridad
    if (puedeCambiarResponsable && d.responsableId && d.responsableId !== r.responsable?.id) c.responsableId = d.responsableId
    if (d.responsabilidad && d.responsabilidad !== r.responsabilidad) c.responsabilidad = d.responsabilidad
    return c
  }
  return (
    <Accion titulo="Reclasificar" onHecho={onHecho} descripcion="No cambia el estado. Cada cambio queda en el historial con el valor anterior."
      onEnviar={() => reportesService.reclasificar(r.folio, cambios(), etag)}>
      <Select label="Prioridad" vacio={null} value={d.prioridad} onChange={(e) => setD({ ...d, prioridad: e.target.value })} opciones={PRIORIDADES.map((p) => ({ valor: p, texto: p }))} />
      {puedeCambiarResponsable && (
        <Select label="Responsable" vacio={null} value={d.responsableId} onChange={(e) => setD({ ...d, responsableId: e.target.value })}
          opciones={(resp.datos ?? []).map((x) => ({ valor: x.id, texto: x.nombre + (x.sinAcceso ? ' · Sin acceso' : '') }))} />
      )}
      <Select label="Responsabilidad" vacio={null} value={d.responsabilidad} onChange={(e) => setD({ ...d, responsabilidad: e.target.value })}
        opciones={Object.entries(RESPONSABILIDAD).map(([valor, texto]) => ({ valor, texto }))} />
    </Accion>
  )
}

function Cancelar({ r, esResidente, onHecho }) {
  const [motivo, setMotivo] = useState(esResidente ? 'Ya se resolvió' : '')
  return (
    <Accion titulo="Cancelar reporte" onHecho={onHecho} boton="Confirmar cancelación"
      descripcion={esResidente ? 'Solo puede cancelar un reporte que ya se resolvió.' : 'El motivo es obligatorio.'}
      onEnviar={() => reportesService.cancelar(r.folio, motivo)}>
      {esResidente ? <p className="font-medium">Motivo: «Ya se resolvió»</p>
        : <Input label="Motivo" required value={motivo} onChange={(e) => setMotivo(e.target.value)} />}
    </Accion>
  )
}

function Cerrar({ r, ciclo, onHecho }) {
  const [motivo, setMotivo] = useState('')
  const sigue = ciclo?.confirmacion?.respuesta === 'SigueFallando'
  return (
    <Accion titulo="Cerrar" variante="primario" onHecho={onHecho} boton="Cerrar reporte"
      descripcion={sigue ? 'El residente respondió «Sigue fallando»: para cerrar escriba el motivo.' : 'Se revisó el trabajo y la evidencia.'}
      onEnviar={() => reportesService.cerrar(r.folio, motivo)}>
      <AreaTexto label={sigue ? 'Motivo del cierre' : 'Comentario (opcional)'} required={sigue} value={motivo} onChange={(e) => setMotivo(e.target.value)} />
    </Accion>
  )
}

function Reabrir({ r, onHecho }) {
  const [comentario, setComentario] = useState('')
  return (
    <Accion titulo="Reabrir" onHecho={onHecho} descripcion="Vuelve a «En proceso» con el mismo folio y un ciclo de atención nuevo."
      onEnviar={() => reportesService.reabrir(r.folio, comentario)}>
      <AreaTexto label="Motivo de la reapertura" required value={comentario} onChange={(e) => setComentario(e.target.value)} />
    </Accion>
  )
}

function Duplicado({ r, onHecho }) {
  const [principal, setPrincipal] = useState('')
  return (
    <div className="flex w-full flex-col gap-2 rounded-lg border border-violet-300 bg-violet-50 p-4">
      <p className="font-semibold text-violet-900">Posible duplicado</p>
      <p className="text-sm text-violet-900">Hay otro reporte abierto de la misma categoría en la misma ubicación. Decide si es el mismo caso.</p>
      <div className="flex flex-wrap gap-2">
        <Accion titulo="Unir al reporte principal" onHecho={onHecho} boton="Unir" onEnviar={() => reportesService.unir(r.folio, principal)}>
          <Input label="Folio del reporte principal" placeholder="RY-000123" value={principal} onChange={(e) => setPrincipal(e.target.value.toUpperCase())} />
        </Accion>
        <Accion titulo="Es independiente" onHecho={onHecho} boton="Confirmar" onEnviar={() => reportesService.mantenerIndependiente(r.folio)}>
          <p className="text-sm">Se retira la marca y los dos reportes siguen por separado.</p>
        </Accion>
      </div>
    </div>
  )
}

function Costo({ r, onHecho }) {
  const [d, setD] = useState({ monto: '', pagador: 'Condominio' })
  return (
    <Accion titulo="Registrar costo" onHecho={onHecho} onEnviar={() => reportesService.registrarCosto(r.folio, { pagador: d.pagador, ...(d.monto !== '' ? { monto: Number(d.monto) } : {}) })}>
      <Input label="Monto en pesos (opcional)" type="number" min="0" step="0.01" value={d.monto} onChange={(e) => setD({ ...d, monto: e.target.value })} />
      <Select label="Quién pagó" vacio={null} value={d.pagador} onChange={(e) => setD({ ...d, pagador: e.target.value })} opciones={Object.entries(PAGADOR).map(([valor, texto]) => ({ valor, texto }))} />
    </Accion>
  )
}

// ----------------------------------------------------------------- acciones de Mantenimiento (o la Administración)
function Iniciar({ r, onHecho }) {
  const [comentario, setComentario] = useState('')
  const proveedorSinAcceso = r.responsable?.sinAcceso
  return (
    <Accion titulo="Iniciar atención" variante="primario" onHecho={onHecho} boton="Iniciar"
      descripcion={proveedorSinAcceso ? `Se registrará en nombre de ${r.responsable.nombre}, que no usa el sistema.` : 'El reporte pasa a «En proceso».'}
      onEnviar={() => reportesService.iniciar(r.folio, comentario)}>
      {proveedorSinAcceso && <Input label="Comentario" value={comentario} onChange={(e) => setComentario(e.target.value)} placeholder="El proveedor confirmó que ya inició" />}
    </Accion>
  )
}

function Terminar({ r, esAdmin, onHecho }) {
  const { encolar } = useCola()
  const [fotos, setFotos] = useState([])
  const [d, setD] = useState({ notaTrabajo: '', pendientes: '', justificacionSinEvidencia: '', garantiaVencimiento: '' })
  const excepcion = esAdmin && r.responsable?.sinAcceso
  const datos = () => Object.fromEntries(Object.entries(d).filter(([, v]) => v))
  return (
    <Accion titulo="Marcar terminado" variante="primario" onHecho={onHecho} boton="Terminar"
      descripcion={excepcion ? 'Proveedor sin acceso: puede terminar sin fotos si escribe la justificación (RD-09).' : 'Adjunte de 1 a 5 fotos del trabajo terminado. La nota es opcional.'}
      onEnviar={async () => {
        const clave = nuevaClave()
        const sinSenal = () => encolar({ id: clave, tipo: 'terminado', folio: r.folio, datos: datos(), fotos, resumen: `Terminar ${r.folio}: ${r.categoria}` })
          .then(() => { throw Object.assign(new Error('Sin señal: el terminado se guardó en el dispositivo y se enviará solo al recuperar la conexión (ver «Envíos sin conexión»).'), { guardado: true }) })
        if (!navigator.onLine) return sinSenal()
        try {
          const res = await reportesService.terminar(r.folio, datos(), fotos, { headers: { 'Idempotency-Key': clave } })
          if (res.archivosRechazados?.length) alert(res.archivosRechazados.map((x) => `${x.nombre}: ${x.motivo}`).join('\n'))
        } catch (e) {
          if (esFallaDeRed(e)) return sinSenal()
          throw e
        }
      }}>
      <Archivos label="Fotos de evidencia" accept="image/jpeg,image/png" multiple capture="environment" onChange={(a) => setFotos(a.slice(0, 5))}
        ayuda={fotos.length ? `${fotos.length} foto(s)` : undefined} />
      <AreaTexto label="Nota del trabajo (opcional)" maxLength={1000} value={d.notaTrabajo} onChange={(e) => setD({ ...d, notaTrabajo: e.target.value })} />
      <AreaTexto label="Lo que quedó pendiente (si solo se atendió lo urgente)" maxLength={1000} value={d.pendientes} onChange={(e) => setD({ ...d, pendientes: e.target.value })} />
      <Input label="Garantía hasta (opcional)" type="date" value={d.garantiaVencimiento} onChange={(e) => setD({ ...d, garantiaVencimiento: e.target.value })} />
      {excepcion && <AreaTexto label="Justificación sin evidencia" value={d.justificacionSinEvidencia} onChange={(e) => setD({ ...d, justificacionSinEvidencia: e.target.value })} />}
    </Accion>
  )
}

function Nota({ r, onHecho }) {
  const [texto, setTexto] = useState('')
  return (
    <Accion titulo="Agregar nota" onHecho={onHecho} descripcion="Nota interna (no la ve el residente). De 1 a 500 caracteres."
      onEnviar={() => reportesService.agregarNota(r.folio, texto)}>
      <AreaTexto label="Nota" maxLength={500} value={texto} onChange={(e) => setTexto(e.target.value)} />
    </Accion>
  )
}

function Visita({ r, etag, onHecho }) {
  const [cuando, setCuando] = useState('')
  return (
    <Accion titulo={r.fechaVisita ? 'Cambiar visita' : 'Programar visita'} onHecho={onHecho} descripcion="El residente verá la fecha y recibirá un aviso."
      onEnviar={() => reportesService.programarVisita(r.folio, aIsoLocal(cuando), etag)}>
      <Input label="Fecha y hora" type="datetime-local" value={cuando} onChange={(e) => setCuando(e.target.value)} />
    </Accion>
  )
}

function Detener({ r, onHecho }) {
  const [d, setD] = useState({ motivo: '', textoOtro: '' })
  if (r.detencionAbierta) {
    return <Accion titulo="Reanudar" onHecho={onHecho} boton="Reanudar atención" onEnviar={() => reportesService.reanudar(r.folio, r.detencionAbierta.id)}>
      <p className="text-sm">Detenido por «{MOTIVOS_DETENCION[r.detencionAbierta.motivo]}» desde {fecha(r.detencionAbierta.fechaInicio)}.</p>
    </Accion>
  }
  return (
    <Accion titulo="Marcar detenido" onHecho={onHecho} boton="Detener" descripcion="No cambia el estado; el residente verá el motivo."
      onEnviar={() => reportesService.detener(r.folio, d.motivo, d.textoOtro)}>
      <Select label="Motivo" required value={d.motivo} onChange={(e) => setD({ ...d, motivo: e.target.value })}
        opciones={Object.entries(MOTIVOS_DETENCION).map(([valor, texto]) => ({ valor, texto }))} />
      {d.motivo === 'Otro' && <Input label="¿Cuál?" value={d.textoOtro} onChange={(e) => setD({ ...d, textoOtro: e.target.value })} />}
    </Accion>
  )
}

// ----------------------------------------------------------------- acciones del Residente
function Confirmar({ r, ciclo, onHecho }) {
  const [respuesta, setRespuesta] = useState('YaQuedo')
  const [comentario, setComentario] = useState('')
  return (
    <Accion titulo="¿Quedó bien la reparación?" variante="primario" onHecho={onHecho} boton="Enviar respuesta" abiertaInicial
      descripcion={`Puede responder una vez, hasta el ${fecha(ciclo?.plazoConfirmacionHasta)}.`}
      onEnviar={() => reportesService.responder(r.folio, respuesta, comentario)}>
      <fieldset className="flex flex-wrap gap-6">
        <legend className="sr-only">Respuesta</legend>
        {Object.entries(RESPUESTAS).map(([v, t]) => (
          <label key={v} className="flex items-center gap-2">
            <input type="radio" name="respuesta" checked={respuesta === v} onChange={() => setRespuesta(v)} className="h-5 w-5" />{t}
          </label>
        ))}
      </fieldset>
      <AreaTexto label={respuesta === 'SigueFallando' ? '¿Qué sigue fallando?' : 'Comentario (opcional)'} required={respuesta === 'SigueFallando'}
        value={comentario} onChange={(e) => setComentario(e.target.value)} />
    </Accion>
  )
}

function Persiste({ r, onHecho }) {
  const [comentario, setComentario] = useState('')
  return (
    <Accion titulo="El problema persiste" onHecho={onHecho} boton="Avisar a la Administración"
      descripcion="Dentro de los 30 días posteriores al cierre. La Administración decide si lo reabre."
      onEnviar={() => reportesService.indicarPersistencia(r.folio, comentario)}>
      <AreaTexto label="Comentario (opcional)" value={comentario} onChange={(e) => setComentario(e.target.value)} />
    </Accion>
  )
}

// ----------------------------------------------------------------- página
function Acciones({ r, etag, usuario, onHecho }) {
  const [ahora] = useState(() => Date.now())
  const rol = usuario.rol
  const esAdmin = rol === 'Administracion'
  const esResponsable = rol === 'Mantenimiento' && r.responsable?.id === usuario.id
  const esReportante = rol === 'Residente' && r.reportante?.id === usuario.id
  const ciclo = r.ciclos?.at(-1)
  const opera = esAdmin || esResponsable
  const props = { r, etag, onHecho }
  const lista = []
  if (esAdmin && r.posibleDuplicado && ['Reportado', 'Asignado'].includes(r.estado)) lista.push(<Duplicado key="dup" {...props} />)
  if (esAdmin && r.estado === 'Reportado') lista.push(<Asignar key="asig" {...props} />)
  if (opera && r.estado === 'Asignado') lista.push(<Iniciar key="ini" {...props} />)
  if (opera && r.estado === 'EnProceso') lista.push(<Terminar key="ter" {...props} esAdmin={esAdmin} />)
  if (esReportante && r.estado === 'Terminado' && !ciclo?.confirmacion && new Date(ciclo?.plazoConfirmacionHasta).getTime() > ahora) lista.push(<Confirmar key="conf" {...props} ciclo={ciclo} />)
  if (esAdmin && r.estado === 'Terminado') lista.push(<Cerrar key="cer" {...props} ciclo={ciclo} />)
  if (esAdmin && ['Terminado', 'Cerrado'].includes(r.estado)) lista.push(<Reabrir key="reab" {...props} />)
  if (esAdmin && ['Asignado', 'EnProceso', 'Terminado'].includes(r.estado)) lista.push(<Reclasificar key="recl" {...props} />)
  if (opera && ['Asignado', 'EnProceso'].includes(r.estado)) lista.push(<Nota key="nota" {...props} />, <Visita key="vis" {...props} />, <Detener key="det" {...props} />)
  if ((esAdmin || esReportante) && ['Reportado', 'Asignado'].includes(r.estado)) lista.push(<Cancelar key="can" {...props} esResidente={!esAdmin} />)
  if (esReportante && r.estado === 'Cerrado') lista.push(<Persiste key="per" {...props} />)
  if (esAdmin && !['Cancelado', 'Unido'].includes(r.estado)) lista.push(<Costo key="costo" {...props} />)
  if (!lista.length) return null
  return <Card titulo="Acciones"><div className="flex flex-wrap gap-2">{lista}</div></Card>
}

const CAMPOS = { prioridad: 'Prioridad', responsable: 'Responsable', responsabilidad: 'Responsabilidad', responsableCosto: 'Responsable del costo',
  ubicacionOrigen: 'Ubicación de origen', descripcion: 'Descripción', categoria: 'Categoría', subtipo: 'Subtipo', ubicacion: 'Ubicación',
  prioridadSugerida: 'Prioridad sugerida', fechaVisita: 'Visita', garantiaVencimiento: 'Garantía', posibleDuplicado: 'Posible duplicado', costo: 'Costo' }
const TIPOS = { Nota: 'Nota', Detencion: 'Detenido', Reanudacion: 'Reanudado', Confirmacion: 'Respuesta del residente',
  PersistenciaIndicada: 'El problema persiste', Costo: 'Costo' }
const legible = (v) => ESTADOS[v] ?? RESPUESTAS[v] ?? MOTIVOS_DETENCION[v] ?? PAGADOR[v] ?? v

function Historial({ folio }) {
  const h = useCarga(() => reportesService.historial(folio), [folio])
  const [ver, setVer] = useState(false)
  const [conAvisos, setConAvisos] = useState(false)
  if (!ver) return <Button variante="secundario" onClick={() => setVer(true)}>Ver historial</Button>
  if (h.cargando) return <Cargando />
  if (h.error) return <ErrorCarga error={h.error} onReintentar={h.recargar} />
  const avisos = h.datos.items.filter((x) => x.tipo === 'AvisoEnviado').length
  const items = h.datos.items.filter((x) => conAvisos || x.tipo !== 'AvisoEnviado')
  return (
    <div className="flex flex-col gap-3">
      {avisos > 0 && (
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={conAvisos} onChange={(e) => setConAvisos(e.target.checked)} className="h-4 w-4" />
          Mostrar la constancia de los {avisos} avisos enviados (sistema y correo)
        </label>
      )}
      <ol className="flex flex-col gap-2 border-l-2 border-slate-200 pl-4">
        {items.map((x) => {
          const titulo = x.tipo === 'CambioEstado' ? 'Estado' : x.tipo === 'AvisoEnviado' ? `Aviso por ${x.canal === 'Correo' ? 'correo' : 'el sistema'}`
            : TIPOS[x.tipo] ?? CAMPOS[x.campo] ?? x.campo ?? x.tipo
          return (
            <li key={x.id}>
              <p className="text-sm text-slate-600">{fecha(x.fecha)} · {x.autor}</p>
              <p>
                <span className="font-medium">{titulo}</span>
                {x.tipo !== 'Nota' && (x.valorAnterior ? <>: {legible(x.valorAnterior)} → {legible(x.valorNuevo)}</> : x.valorNuevo && <>: {legible(x.valorNuevo)}</>)}
                {x.comentario && <span className="text-slate-700"> — {x.comentario}</span>}
              </p>
            </li>
          )
        })}
      </ol>
    </div>
  )
}

export default function DetalleReporte() {
  const { folio } = useParams()
  const { usuario } = useAuth()
  const location = useLocation()
  const [aviso, setAviso] = useState(location.state?.creado ? 'Reporte registrado.' : '')
  const { cargando, error, datos, recargar } = useCarga((signal) => reportesService.obtener(folio, { signal }), [folio])
  const hecho = (msg) => { setAviso(msg); recargar(); window.scrollTo({ top: 0, behavior: 'smooth' }) }

  if (cargando && !datos) return <Pagina titulo={folio}><Cargando /></Pagina>
  if (error) return <Pagina titulo={folio}><ErrorCarga error={error} onReintentar={recargar} titulo="No se pudo abrir el reporte" /></Pagina>
  const { datos: r, etag } = datos
  const rechazados = location.state?.rechazados ?? []

  return (
    <Pagina titulo={<span className="font-mono">{r.folio}</span>} acciones={<Link to="/reportes" className="text-blue-700 underline">Volver a la lista</Link>}>
      <div className="flex flex-col gap-4">
        {aviso && <Exito>{aviso}</Exito>}
        {datos.sinConexion && (
          <div role="status" className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-amber-950">
            <p className="font-semibold">Sin conexión</p>
            <p className="mt-1">«Marcar terminado» se guarda en el dispositivo; las demás acciones necesitan señal. Información guardada el {fecha(new Date(datos.guardado).toISOString())}</p>
          </div>
        )}
        {rechazados.length > 0 && <Alerta titulo="Algunos archivos no se guardaron">{rechazados.map((x) => `${x.nombre}: ${x.motivo}`).join(' · ')}</Alerta>}
        <div className="flex flex-wrap items-center gap-2">
          <Estado estado={r.estado} />
          {r.prioridad ? <Prioridad prioridad={r.prioridad} /> : <Prioridad prioridad={r.prioridadSugerida} sugerida />}
          {r.detenido && <Etiqueta color="bg-orange-100 text-orange-900">Detenido: {MOTIVOS_DETENCION[r.detencionAbierta?.motivo] ?? ''}</Etiqueta>}
          {r.reportePrincipal && <Etiqueta color="bg-violet-100 text-violet-900">Unido a {r.reportePrincipal}</Etiqueta>}
        </div>
        {r.mensajeAcceso && <Alerta titulo="Acceso">{r.mensajeAcceso}</Alerta>}

        <Acciones r={r} etag={etag} usuario={usuario} onHecho={hecho} />

        <Card titulo={`${r.categoria}${r.subtipo ? ` · ${r.subtipo}` : ''}`}>
          <p className="mb-4 whitespace-pre-line">{r.descripcion}</p>
          <dl className="grid gap-3 sm:grid-cols-2">
            <Dato titulo="Ubicación">{r.ubicacion?.etiqueta}{r.ubicacion?.parteAfectada && ` · ${r.ubicacion.parteAfectada}`}{r.ubicacion?.referencia && ` · ${r.ubicacion.referencia}`}</Dato>
            <Dato titulo="Ubicación de origen">{r.ubicacionOrigen?.etiqueta}</Dato>
            <Dato titulo="Fecha de aviso">{fecha(r.fechaAviso)}</Dato>
            <Dato titulo="Medio de origen">{r.medioOrigen}</Dato>
            <Dato titulo="¿Peligroso o empeorando?">{r.esPeligroso === undefined ? null : r.esPeligroso ? 'Sí' : 'No'}</Dato>
            <Dato titulo="Reportante">{r.reportante && (r.reportante.sinCuenta ? `${r.reportante.nombre} (sin cuenta)` : r.reportante.nombre)}</Dato>
            <Dato titulo="Capturado por">{r.capturadoPor?.nombre}</Dato>
            <Dato titulo="Responsable">{r.responsable && `${r.responsable.nombre}${r.responsable.sinAcceso ? ' (sin acceso al sistema)' : ''}`}</Dato>
            <Dato titulo="Responsabilidad">{RESPONSABILIDAD[r.responsabilidad]}</Dato>
            <Dato titulo="Responsable del costo">{PAGADOR[r.responsableCosto]}</Dato>
            <Dato titulo="Pagó">{PAGADOR[r.pagador]}</Dato>
            <Dato titulo="Monto">{r.montoCosto !== undefined && `$${Number(r.montoCosto).toLocaleString('es-MX', { minimumFractionDigits: 2 })}`}</Dato>
            <Dato titulo="Autoriza acceso">{r.autorizaAcceso === undefined ? null : r.autorizaAcceso ? 'Sí' : 'No'}</Dato>
            <Dato titulo="Horarios de acceso">{r.horariosAcceso}</Dato>
            <Dato titulo="Visita programada">{r.fechaVisita && fecha(r.fechaVisita)}</Dato>
            <Dato titulo="Desde cuándo">{r.desdeCuando}</Dato>
            <Dato titulo="Propietario">{r.propietario && `${r.propietario.nombre} · ${r.propietario.correo}${r.propietario.viveEnCondominio ? '' : ' (no vive en el condominio)'}`}</Dato>
          </dl>
          {r.fotosAlta?.length > 0 && (
            <div className="mt-4">
              <p className="mb-2 text-sm text-slate-600">Fotos y video del alta</p>
              <div className="flex flex-wrap gap-2">{r.fotosAlta.map((a) => <Foto key={a.id} folio={r.folio} archivo={a} />)}</div>
            </div>
          )}
        </Card>

        {r.ciclos?.map((c) => (
          <Card key={c.numero} titulo={`Atención ${r.ciclos.length > 1 ? `— ciclo ${c.numero}` : ''}`}
            subtitulo={`Inicio ${fecha(c.inicio)}${c.fin ? ` · Terminado ${fecha(c.fin)}` : ' · en curso'}`}>
            <dl className="grid gap-3 sm:grid-cols-2">
              <Dato titulo="Nota del trabajo">{c.notaTrabajo}</Dato>
              <Dato titulo="Pendiente">{c.pendientes}</Dato>
              <Dato titulo="Garantía hasta">{c.garantiaVencimiento && soloFecha(c.garantiaVencimiento)}</Dato>
              <Dato titulo="Respuesta del residente">{c.confirmacion && `${RESPUESTAS[c.confirmacion.respuesta]}${c.confirmacion.comentario ? ` — «${c.confirmacion.comentario}»` : ''}`}</Dato>
              <Dato titulo="Puede responder hasta">{!c.confirmacion && c.plazoConfirmacionHasta && fecha(c.plazoConfirmacionHasta)}</Dato>
            </dl>
            {c.sinEvidenciaFotografica && <p className="mt-2 font-medium text-amber-900">Terminado sin evidencia fotográfica: {c.justificacionSinEvidencia}</p>}
            {c.fotosEvidencia?.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">{c.fotosEvidencia.map((a) => <Foto key={a.id} folio={r.folio} archivo={a} />)}</div>
            )}
          </Card>
        ))}

        {r.notas?.length > 0 && (
          <Card titulo="Notas internas">
            <ul className="flex flex-col gap-2">{r.notas.map((n) => <li key={n.id}><span className="text-sm text-slate-600">{fecha(n.fecha)} · {n.autor}:</span> {n.texto}</li>)}</ul>
          </Card>
        )}

        {usuario.rol !== 'Vigilancia' && <Card titulo="Historial"><Historial folio={r.folio} /></Card>}
      </div>
    </Pagina>
  )
}
