import { useId } from 'react'

export default function Input({ label, id, error, required = false, ...props }) {
  // Si no se pasa id, se genera uno para que el label siempre quede ligado al campo.
  const idGenerado = useId()
  const idCampo = id ?? idGenerado
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={idCampo} className="text-sm font-medium text-slate-700">
        {label}
        {required && <span className="text-red-500"> *</span>}
      </label>
      <input
        id={idCampo}
        required={required}
        className={`rounded-lg border px-3 py-2 outline-none ${error ? 'border-red-500' : 'border-slate-300 focus:border-blue-500'}`}
        {...props}
      />
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  )
}
