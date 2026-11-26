import { useId } from 'react'

const base = 'rounded-lg border px-3 py-2 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-blue-700'

function Envoltura({ label, idCampo, error, required, ayuda, children }) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={idCampo} className="text-sm font-medium text-slate-700">
        {label}
        {required && <span aria-hidden="true" className="text-red-700"> *</span>}
      </label>
      {children}
      {ayuda && !error && <p id={`${idCampo}-ayuda`} className="text-sm text-slate-600">{ayuda}</p>}
      {error && <p id={`${idCampo}-error`} className="text-sm text-red-700">{error}</p>}
    </div>
  )
}

export function Select({ label, id, error, required, ayuda, opciones, vacio = 'Selecciona…', ...props }) {
  const gen = useId()
  const idCampo = id ?? gen
  return (
    <Envoltura {...{ label, idCampo, error, required, ayuda }}>
      <select id={idCampo} required={required} aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${idCampo}-error` : ayuda ? `${idCampo}-ayuda` : undefined}
        className={`${base} bg-white ${error ? 'border-red-700' : 'border-slate-500'}`} {...props}>
        {vacio !== null && <option value="">{vacio}</option>}
        {opciones.map((o) => <option key={o.valor} value={o.valor}>{o.texto}</option>)}
      </select>
    </Envoltura>
  )
}

export function AreaTexto({ label, id, error, required, ayuda, ...props }) {
  const gen = useId()
  const idCampo = id ?? gen
  return (
    <Envoltura {...{ label, idCampo, error, required, ayuda }}>
      <textarea id={idCampo} required={required} rows={3} aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${idCampo}-error` : ayuda ? `${idCampo}-ayuda` : undefined}
        className={`${base} ${error ? 'border-red-700' : 'border-slate-500'}`} {...props} />
    </Envoltura>
  )
}

// Pregunta Sí / No con radios (RF-03: peligro y autorización de acceso).
export function SiNo({ pregunta, nombre, value, onChange, error, required }) {
  return (
    <fieldset className="flex flex-col gap-1" aria-invalid={error ? true : undefined}>
      <legend className="text-sm font-medium text-slate-700">
        {pregunta}{required && <span aria-hidden="true" className="text-red-700"> *</span>}
      </legend>
      <div className="flex gap-6 pt-1">
        {[['si', 'Sí', true], ['no', 'No', false]].map(([k, t, v]) => (
          <label key={k} className="flex items-center gap-2">
            <input type="radio" name={nombre} checked={value === v} onChange={() => onChange(v)} className="h-5 w-5" />
            {t}
          </label>
        ))}
      </div>
      {error && <p className="text-sm text-red-700">{error}</p>}
    </fieldset>
  )
}

export function Archivos({ label, id, ayuda, error, onChange, ...props }) {
  const gen = useId()
  const idCampo = id ?? gen
  return (
    <Envoltura {...{ label, idCampo, error, ayuda }}>
      <input id={idCampo} type="file" onChange={(e) => onChange(Array.from(e.target.files ?? []))}
        className="rounded-lg border border-slate-500 px-3 py-2 file:mr-3 file:rounded file:border-0 file:bg-blue-50 file:px-3 file:py-1 file:text-blue-800" {...props} />
    </Envoltura>
  )
}
