// Alta de reporte: el Residente desde su celular (RF-03) o la Administración / Vigilancia a nombre de un tercero (RF-04).
// Si el servidor rechaza un dato, lo capturado sigue en el formulario (RF-03-AC-5).
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Alerta from '../components/Alerta.jsx'
import Button from '../components/Button.jsx'
import { AreaTexto, Archivos, Select, SiNo } from '../components/Campos.jsx'
import Card from '../components/Card.jsx'
import { Cargando, ErrorCarga, Pagina } from '../components/Estados.jsx'
import Input from '../components/Input.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { useCola } from '../context/ColaContext.jsx'
import { esFallaDeRed, nuevaClave } from '../lib/cola.js'
import { MEDIOS, aIsoLocal } from '../lib/etiquetas.js'
import { useCarga } from '../lib/useCarga.js'
import { catalogoService } from '../services/catalogoService.js'
import { reportesService } from '../services/reportesService.js'

const ahoraLocal = () => {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

export default function NuevoReporte() {
  const { usuario } = useAuth()
  const { encolar } = useCola()
  const navigate = useNavigate()
  const esResidente = usuario?.rol === 'Residente'
  const esAdmin = usuario?.rol === 'Administracion'
  const catalogos = useCarga(async (signal) => {
    const [categorias, areas, unidades, residentes] = await Promise.all([
      catalogoService.categorias({ signal }),
      catalogoService.areasComunes({ signal }),
      esResidente ? Promise.resolve({ items: [] }) : catalogoService.unidades({ signal }),
      esAdmin ? catalogoService.usuarios({ rol: 'Residente', estadoCuenta: 'Activa' }) : Promise.resolve({ items: [] }),
    ])
    return { categorias, areas, unidades: unidades.items, residentes: residentes.items }
  }, [esResidente, esAdmin])

  const [f, setF] = useState({
    categoriaId: '', subtipo: '', descripcion: '', tipoUbicacion: esResidente ? 'Unidad' : 'AreaComun', unidadId: '', areaComunId: '',
    parteAfectada: '', referencia: '', esPeligroso: null, autorizaAcceso: null, horariosAcceso: '', desdeCuando: '', habiaPasadoAntes: null,
    medioOrigen: '', fechaAviso: ahoraLocal(), residenteReportanteId: '', nombreReferencia: '', contactoReferencia: '',
  })
  const [fotos, setFotos] = useState([])
  const [video, setVideo] = useState(null)
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const [pedirFotos, setPedirFotos] = useState(false)
  const poner = (k) => (e) => setF({ ...f, [k]: e?.target ? e.target.value : e })

  const categoria = useMemo(() => catalogos.datos?.categorias.find((c) => c.id === f.categoriaId), [catalogos.datos, f.categoriaId])
  const unidadId = esResidente ? usuario?.unidad?.id : f.unidadId
  const enUnidad = f.tipoUbicacion === 'Unidad'

  function armarDatos() {
    const d = { categoriaId: f.categoriaId || undefined, descripcion: f.descripcion, esPeligroso: f.esPeligroso ?? undefined }
    if (categoria?.subtipos.length) d.subtipo = f.subtipo || undefined
    d.ubicacion = enUnidad
      ? { tipo: 'Unidad', unidadId: unidadId || undefined, parteAfectada: f.parteAfectada || undefined }
      : { tipo: 'AreaComun', areaComunId: f.areaComunId || undefined, referencia: f.referencia || undefined }
    if (enUnidad) {
      if (f.autorizaAcceso !== null) d.autorizaAcceso = f.autorizaAcceso
      if (f.horariosAcceso) d.horariosAcceso = f.horariosAcceso
    }
    if (f.desdeCuando) d.desdeCuando = f.desdeCuando
    if (f.habiaPasadoAntes !== null) d.habiaPasadoAntes = f.habiaPasadoAntes
    if (!esResidente) {
      d.medioOrigen = f.medioOrigen || undefined
      d.fechaAviso = f.fechaAviso ? aIsoLocal(f.fechaAviso) : undefined
      if (f.residenteReportanteId) d.residenteReportanteId = f.residenteReportanteId
      else {
        d.nombreReferencia = f.nombreReferencia || undefined
        if (f.contactoReferencia) d.contactoReferencia = f.contactoReferencia
      }
    }
    return d
  }

  async function enviar(e) {
    e?.preventDefault()
    if (fotos.length === 0 && !pedirFotos) { // RF-03-AC-7 [UI]: antes de enviar, se piden fotografías
      setPedirFotos(true)
      return
    }
    setPedirFotos(false)
    setEnviando(true)
    setError(null)
    const datos = armarDatos()
    const clave = nuevaClave() // la misma clave en cada reintento: nunca se duplica (RNF-11)
    const guardarSinConexion = async () => {
      await encolar({ id: clave, tipo: 'reporte', datos, fotos, video, resumen: `${categoria?.nombre ?? 'Reporte'}: ${f.descripcion.slice(0, 60)}` })
      navigate('/pendientes')
    }
    try {
      if (!navigator.onLine) return await guardarSinConexion()
      const creado = await reportesService.crear(datos, fotos, video, { headers: { 'Idempotency-Key': clave } })
      navigate(`/reportes/${creado.folio}`, { state: { creado: true, rechazados: creado.archivosRechazados ?? [] } })
    } catch (err) {
      if (esFallaDeRed(err)) return await guardarSinConexion()
      setError(err)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } finally {
      setEnviando(false)
    }
  }

  const errorDe = (...campos) => error?.errores?.find((x) => campos.some((c) => x.campo === c || x.campo.startsWith(c + '.')))?.mensaje

  if (catalogos.error && esFallaDeRed(catalogos.error)) {
    return <Pagina titulo="Nuevo reporte"><ErrorCarga error={catalogos.error} onReintentar={catalogos.recargar}
      titulo="Sin conexión: abre el formulario una vez con señal para poder capturar sin ella" /></Pagina>
  }
  if (catalogos.cargando) return <Pagina titulo="Nuevo reporte"><Cargando /></Pagina>
  if (catalogos.error) return <Pagina titulo="Nuevo reporte"><ErrorCarga error={catalogos.error} onReintentar={catalogos.recargar} /></Pagina>
  const { categorias, areas, unidades, residentes } = catalogos.datos

  return (
    <Pagina titulo="Nuevo reporte" ancho="max-w-2xl">
      {error && <div className="mb-4"><Alerta titulo="Revisa el reporte">{error.message}</Alerta></div>}
      <form onSubmit={enviar} className="flex flex-col gap-6" noValidate>
        {!esResidente && (
          <Card titulo="¿Cómo llegó el aviso?" subtitulo="Captura a nombre de un tercero (RF-04)">
            <div className="grid gap-4 sm:grid-cols-2">
              <Select label="Medio" required value={f.medioOrigen} onChange={poner('medioOrigen')} error={errorDe('medioOrigen')}
                opciones={MEDIOS.map((m) => ({ valor: m, texto: m }))} />
              <Input label="Fecha y hora del aviso" type="datetime-local" required value={f.fechaAviso} onChange={poner('fechaAviso')} error={errorDe('fechaAviso')} />
              {esAdmin && (
                <Select label="Residente que reporta (si tiene cuenta)" value={f.residenteReportanteId} onChange={poner('residenteReportanteId')}
                  vacio="Sin cuenta: indicar nombre" error={errorDe('residenteReportanteId')}
                  opciones={residentes.map((u) => ({ valor: u.id, texto: `${u.nombre}${u.vinculacion ? ` · ${u.vinculacion.unidad.etiqueta}` : ''}` }))} />
              )}
              {!f.residenteReportanteId && <>
                <Input label="Nombre de quien reporta" required value={f.nombreReferencia} onChange={poner('nombreReferencia')} error={errorDe('nombreReferencia')} />
                <Input label="Contacto (opcional)" value={f.contactoReferencia} onChange={poner('contactoReferencia')} />
              </>}
            </div>
          </Card>
        )}

        <Card titulo="¿Qué pasa?">
          <div className="flex flex-col gap-4">
            <Select label="Categoría" required value={f.categoriaId} onChange={(e) => setF({ ...f, categoriaId: e.target.value, subtipo: '' })}
              error={errorDe('categoriaId')} opciones={categorias.map((c) => ({ valor: c.id, texto: c.nombre }))} />
            {categoria?.subtipos.length > 0 && (
              <Select label="Subtipo" required value={f.subtipo} onChange={poner('subtipo')} error={errorDe('subtipo')}
                opciones={categoria.subtipos.map((s) => ({ valor: s.nombre, texto: s.nombre }))} />
            )}
            <AreaTexto label="Descripción" required maxLength={1000} value={f.descripcion} onChange={poner('descripcion')}
              ayuda="Entre 10 y 1,000 caracteres." error={errorDe('descripcion')} />
            <SiNo pregunta="¿El problema es peligroso o está empeorando?" nombre="peligro" required value={f.esPeligroso}
              onChange={poner('esPeligroso')} error={errorDe('esPeligroso')} />
            <p className="text-sm text-slate-600">Una emergencia real (persona en riesgo, incendio, inundación fuerte) se avisa por teléfono o en la caseta.</p>
          </div>
        </Card>

        <Card titulo="¿Dónde?">
          <div className="flex flex-col gap-4">
            <fieldset className="flex flex-wrap gap-6">
              <legend className="sr-only">Tipo de ubicación</legend>
              {[['Unidad', esResidente ? `Mi departamento (${usuario?.unidad?.etiqueta ?? 'sin unidad'})` : 'Un departamento'], ['AreaComun', 'Un área común']].map(([v, t]) => (
                <label key={v} className="flex items-center gap-2">
                  <input type="radio" name="tipoUbicacion" checked={f.tipoUbicacion === v} onChange={() => setF({ ...f, tipoUbicacion: v })} className="h-5 w-5" />{t}
                </label>
              ))}
            </fieldset>
            {enUnidad && !esResidente && (
              <Select label="Departamento" required value={f.unidadId} onChange={poner('unidadId')} error={errorDe('ubicacion')}
                opciones={unidades.map((u) => ({ valor: u.id, texto: u.etiqueta }))} />
            )}
            {!enUnidad && (
              <Select label="Área común" required value={f.areaComunId} onChange={poner('areaComunId')} error={errorDe('ubicacion')}
                opciones={areas.map((a) => ({ valor: a.id, texto: a.nombre }))} />
            )}
            {enUnidad ? (
              <>
                <Input label="Parte afectada (opcional)" placeholder="Baño, cocina…" maxLength={200} value={f.parteAfectada} onChange={poner('parteAfectada')} />
                <SiNo pregunta={esResidente ? '¿Autoriza el acceso a su departamento para revisar la falla?' : '¿El ocupante autoriza el acceso?'}
                  nombre="acceso" required value={f.autorizaAcceso} onChange={poner('autorizaAcceso')} error={errorDe('autorizaAcceso')} />
                {f.autorizaAcceso !== null && <Input label="Horarios en que hay alguien (opcional)" value={f.horariosAcceso} onChange={poner('horariosAcceso')} />}
              </>
            ) : (
              <Input label="Referencia (opcional)" placeholder="Junto a la entrada…" maxLength={200} value={f.referencia} onChange={poner('referencia')} />
            )}
          </div>
        </Card>

        <Card titulo="Más detalles (opcional)">
          <div className="flex flex-col gap-4">
            <Input label="¿Desde cuándo pasa?" value={f.desdeCuando} onChange={poner('desdeCuando')} />
            <SiNo pregunta="¿Ya había pasado antes?" nombre="antes" value={f.habiaPasadoAntes} onChange={poner('habiaPasadoAntes')} />
            <Archivos label="Fotografías (hasta 5, JPEG o PNG de 10 MB máximo)" accept="image/jpeg,image/png" multiple capture="environment"
              onChange={(a) => setFotos(a.slice(0, 5))} ayuda={fotos.length ? `${fotos.length} foto(s) seleccionada(s)` : 'Las fotos ayudan a atender más rápido.'}
              error={errorDe('fotos')} />
            <Archivos label="Video (opcional, MP4 de 50 MB máximo)" accept="video/mp4" onChange={(a) => setVideo(a[0] ?? null)} />
          </div>
        </Card>

        {pedirFotos && (
          <div role="alertdialog" aria-labelledby="sin-fotos" className="rounded-lg border border-amber-300 bg-amber-50 p-4 text-amber-900">
            <p id="sin-fotos" className="font-semibold">No adjuntaste fotografías</p>
            <p className="mt-1">Una foto ayuda a Mantenimiento a saber qué llevar. ¿Quieres adjuntar una antes de enviar?</p>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button onClick={() => setPedirFotos(false)}>Adjuntar fotos</Button>
              <Button variante="secundario" onClick={() => enviar()} cargando={enviando}>Enviar sin fotos</Button>
            </div>
          </div>
        )}
        {!pedirFotos && <Button type="submit" cargando={enviando}>Enviar reporte</Button>}
      </form>
    </Pagina>
  )
}
