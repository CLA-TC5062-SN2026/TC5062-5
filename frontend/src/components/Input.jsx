import { useId } from 'react'

export default function Input({ label, id, error, required = false, ...props }) {
  // Si no se pasa id, se genera uno para que el label siempre quede ligado al campo.
  const idGenerado = useId()
  const idCampo = id ?? idGenerado
  const idError = `${idCampo}-error`
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={idCampo} className="text-sm font-medium text-slate-700">
        {label}
        {required && <span aria-hidden="true" className="text-red-700"> *</span>}
      </label>
      <input
        id={idCampo}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? idError : undefined}
        className={`rounded-lg border px-3 py-2 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-blue-700 ${error ? 'border-red-700' : 'border-slate-500'}`}
        {...props}
      />
      {error && <p id={idError} className="text-sm text-red-700">{error}</p>}
    </div>
  )
}
