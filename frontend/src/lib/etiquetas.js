// Textos legibles para los valores del contrato (enums del openapi_equipo.yaml).
export const ESTADOS = { Reportado: 'Reportado', Asignado: 'Asignado', EnProceso: 'En proceso', Terminado: 'Terminado',
  Cerrado: 'Cerrado', Cancelado: 'Cancelado', Unido: 'Unido' }
export const ROLES = { Residente: 'Residente', Vigilancia: 'Vigilancia', Mantenimiento: 'Mantenimiento', Administracion: 'Administración' }
export const PRIORIDADES = ['Urgente', 'Normal', 'Menor']
export const RESPONSABILIDAD = { Comun: 'Común', Privada: 'Privada', PorDeterminar: 'Por determinar' }
export const PAGADOR = { Condominio: 'Condominio (fondo de mantenimiento)', Condomino: 'Condómino (propietario de la unidad)' }
export const MEDIOS = ['WhatsApp', 'Llamada', 'Caseta', 'Correo', 'Presencial']
export const MOTIVOS_DETENCION = { AccesoAlDepartamento: 'Acceso al departamento', EsperaDeProveedor: 'Espera de proveedor',
  EsperaDePieza: 'Espera de pieza', EsperaDeAutorizacionDeGasto: 'Espera de autorización de gasto', Otro: 'Otro' }
export const RESPUESTAS = { YaQuedo: 'Ya quedó', SigueFallando: 'Sigue fallando' }

// Colores con contraste AA sobre fondo claro (RNF-09).
export const COLOR_ESTADO = {
  Reportado: 'bg-amber-100 text-amber-900', Asignado: 'bg-sky-100 text-sky-900', EnProceso: 'bg-indigo-100 text-indigo-900',
  Terminado: 'bg-emerald-100 text-emerald-900', Cerrado: 'bg-slate-200 text-slate-800', Cancelado: 'bg-rose-100 text-rose-900',
  Unido: 'bg-violet-100 text-violet-900',
}
export const COLOR_PRIORIDAD = { Urgente: 'bg-red-700 text-white', Normal: 'bg-blue-700 text-white', Menor: 'bg-slate-600 text-white' }

export const fecha = (iso) => (iso ? new Date(iso).toLocaleString('es-MX', { dateStyle: 'medium', timeStyle: 'short' }) : '—')
export const soloFecha = (iso) => (iso ? new Date(iso + (iso.length === 10 ? 'T12:00:00' : '')).toLocaleDateString('es-MX', { dateStyle: 'medium' }) : '—')

// Fecha local para <input type="datetime-local"> → ISO con la zona del navegador.
export function aIsoLocal(valor) {
  if (!valor) return ''
  const d = new Date(valor)
  const off = -d.getTimezoneOffset()
  const s = off >= 0 ? '+' : '-'
  const p = (n) => String(Math.floor(Math.abs(n))).padStart(2, '0')
  return `${valor.length === 16 ? valor + ':00' : valor}${s}${p(off / 60)}:${p(off % 60)}`
}
export const hoyIso = () => new Date().toISOString().slice(0, 10)
