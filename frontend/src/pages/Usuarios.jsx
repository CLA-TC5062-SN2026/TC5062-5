// Padrón de usuarios (RF-02): la Administración crea las cuentas y la persona la activa con el enlace (RF-14).
import { useState } from 'react'
import Alerta from '../components/Alerta.jsx'
import Button from '../components/Button.jsx'
import { Select } from '../components/Campos.jsx'
import Card from '../components/Card.jsx'
import { Cargando, ErrorCarga, Exito, Pagina } from '../components/Estados.jsx'
import Input from '../components/Input.jsx'
import { Etiqueta } from '../components/Insignias.jsx'
import { ROLES } from '../lib/etiquetas.js'
import { useCarga } from '../lib/useCarga.js'
import { catalogoService } from '../services/catalogoService.js'

const ESTADO_CUENTA = { PendienteActivacion: ['Pendiente de activación', 'bg-amber-100 text-amber-900'], Activa: ['Activa', 'bg-emerald-100 text-emerald-900'],
  Desactivada: ['Desactivada', 'bg-slate-200 text-slate-800'] }

function Alta({ onCreado }) {
  const unidades = useCarga(() => catalogoService.unidades(), [])
  const [d, setD] = useState({ nombre: '', correo: '', rol: 'Residente', unidadId: '', ocupacion: 'Inquilino', tipo: 'PersonalPropio', especialidad: '', telefono: '', perfil: 'Auxiliar' })
  const [error, setError] = useState(null)
  const [cargando, setCargando] = useState(false)
  const p = (k) => (e) => setD({ ...d, [k]: e.target.value })
  async function crear(e) {
    e.preventDefault()
    setCargando(true)
    setError(null)
    const cuerpo = { nombre: d.nombre, correo: d.correo, rol: d.rol }
    if (d.rol === 'Residente') cuerpo.vinculacion = { unidadId: d.unidadId || undefined, ocupacion: d.ocupacion, fechaInicio: new Date().toISOString() }
    if (d.rol === 'Mantenimiento') cuerpo.mantenimiento = { tipo: d.tipo, ...(d.especialidad && { especialidad: d.especialidad }), ...(d.telefono && { telefono: d.telefono }) }
    if (d.rol === 'Administracion') cuerpo.perfilAdministracion = d.perfil
    try {
      const u = await catalogoService.crearUsuario(cuerpo)
      onCreado(`Se creó la cuenta de ${u.nombre} y se le envió el enlace de activación a ${u.correo}.`)
      setD({ ...d, nombre: '', correo: '' })
    } catch (err) {
      setError(err)
    } finally {
      setCargando(false)
    }
  }
  const errorDe = (c) => error?.errores?.find((x) => x.campo.startsWith(c))?.mensaje
  return (
    <Card titulo="Dar de alta una cuenta">
      <form onSubmit={crear} className="grid gap-3 sm:grid-cols-2" noValidate>
        <Input label="Nombre" required value={d.nombre} onChange={p('nombre')} error={errorDe('nombre')} />
        <Input label="Correo" type="email" required value={d.correo} onChange={p('correo')} error={errorDe('correo')} />
        <Select label="Rol" vacio={null} value={d.rol} onChange={p('rol')} opciones={Object.entries(ROLES).map(([valor, texto]) => ({ valor, texto }))} />
        {d.rol === 'Residente' && <>
          <Select label="Departamento" required value={d.unidadId} onChange={p('unidadId')} error={errorDe('vinculacion')}
            opciones={(unidades.datos?.items ?? []).map((u) => ({ valor: u.id, texto: u.etiqueta }))} />
          <Select label="Ocupación" vacio={null} value={d.ocupacion} onChange={p('ocupacion')} opciones={[{ valor: 'Inquilino', texto: 'Inquilino' }, { valor: 'Propietario', texto: 'Propietario' }]} />
        </>}
        {d.rol === 'Mantenimiento' && <>
          <Select label="Tipo" vacio={null} value={d.tipo} onChange={p('tipo')} opciones={[{ valor: 'PersonalPropio', texto: 'Personal propio' }, { valor: 'ProveedorExterno', texto: 'Proveedor externo' }]} />
          <Input label="Especialidad" value={d.especialidad} onChange={p('especialidad')} error={errorDe('mantenimiento.especialidad')} />
          <Input label="Teléfono" value={d.telefono} onChange={p('telefono')} error={errorDe('mantenimiento.telefono')} />
        </>}
        {d.rol === 'Administracion' && <Select label="Perfil" vacio={null} value={d.perfil} onChange={p('perfil')} opciones={[{ valor: 'Auxiliar', texto: 'Auxiliar' }, { valor: 'Administrador', texto: 'Administrador' }]} />}
        {error && <div className="sm:col-span-2"><Alerta titulo="No se pudo crear la cuenta">{error.message}</Alerta></div>}
        <div className="sm:col-span-2"><Button type="submit" cargando={cargando}>Crear cuenta y enviar enlace</Button></div>
      </form>
    </Card>
  )
}

export default function Usuarios() {
  const [aviso, setAviso] = useState('')
  const lista = useCarga(() => catalogoService.usuarios(), [aviso])
  async function reenviar(u) {
    try {
      setAviso((await catalogoService.reenviarActivacion(u.id)).mensaje)
    } catch (e) {
      setAviso(e.message)
    }
  }
  return (
    <Pagina titulo="Usuarios">
      <div className="flex flex-col gap-4">
        {aviso && <Exito>{aviso}</Exito>}
        <Alta onCreado={setAviso} />
        {lista.cargando && <Cargando />}
        {lista.error && <ErrorCarga error={lista.error} onReintentar={lista.recargar} />}
        {lista.datos && (
          <Card titulo="Cuentas">
            <ul className="divide-y divide-slate-100">
              {lista.datos.items.map((u) => (
                <li key={u.id} className="flex flex-wrap items-center justify-between gap-2 py-2">
                  <div>
                    <p className="font-medium">{u.nombre} <span className="text-sm text-slate-600">· {ROLES[u.rol]}{u.perfilAdministracion && ` (${u.perfilAdministracion})`}{u.vinculacion && ` · ${u.vinculacion.unidad.etiqueta}`}</span></p>
                    <p className="text-sm text-slate-600">{u.correo}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Etiqueta color={ESTADO_CUENTA[u.estadoCuenta][1]}>{ESTADO_CUENTA[u.estadoCuenta][0]}</Etiqueta>
                    {u.estadoCuenta === 'PendienteActivacion' && <Button variante="secundario" onClick={() => reenviar(u)}>Reenviar enlace</Button>}
                  </div>
                </li>
              ))}
            </ul>
          </Card>
        )}
      </div>
    </Pagina>
  )
}
