import Alerta from './Alerta.jsx'
import Button from './Button.jsx'

export function Cargando({ texto = 'Cargando…' }) {
  return (
    <p className="flex items-center gap-3 text-slate-700" role="status">
      <span aria-hidden="true" className="h-5 w-5 animate-spin rounded-full border-2 border-blue-700 border-t-transparent" />
      {texto}
    </p>
  )
}

export function ErrorCarga({ error, onReintentar, titulo = 'No se pudo cargar la información' }) {
  return <Alerta titulo={titulo} accion={onReintentar && <Button onClick={onReintentar}>Reintentar</Button>}>{error.message}</Alerta>
}

export function Exito({ children }) {
  return <div role="status" className="rounded-lg border border-emerald-300 bg-emerald-50 p-4 text-emerald-900">{children}</div>
}

export function Pagina({ titulo, acciones, children, ancho = 'max-w-5xl' }) {
  return (
    <main className={`mx-auto ${ancho} p-4 sm:p-8`}>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold sm:text-3xl">{titulo}</h1>
        {acciones && <div className="flex flex-wrap gap-2">{acciones}</div>}
      </div>
      {children}
    </main>
  )
}
