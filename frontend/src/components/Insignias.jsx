import { COLOR_ESTADO, COLOR_PRIORIDAD, ESTADOS } from '../lib/etiquetas.js'

export function Estado({ estado }) {
  return <span className={`rounded-full px-2.5 py-0.5 text-sm font-medium ${COLOR_ESTADO[estado] ?? 'bg-slate-100'}`}>{ESTADOS[estado] ?? estado}</span>
}

export function Prioridad({ prioridad, sugerida = false }) {
  if (!prioridad) return null
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-sm font-medium ${COLOR_PRIORIDAD[prioridad]}`}>
      {prioridad}{sugerida && ' (sugerida)'}
    </span>
  )
}

export function Etiqueta({ children, color = 'bg-slate-100 text-slate-800' }) {
  return <span className={`rounded-full px-2.5 py-0.5 text-sm font-medium ${color}`}>{children}</span>
}
