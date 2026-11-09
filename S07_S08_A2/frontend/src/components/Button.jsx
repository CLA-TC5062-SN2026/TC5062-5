const variantes = {
  primario: 'bg-blue-600 text-white hover:bg-blue-700 focus-visible:outline-blue-700',
  secundario: 'bg-white text-blue-700 border border-blue-700 hover:bg-blue-50 focus-visible:outline-blue-700',
}

export default function Button({
  children,
  variante = 'primario',
  cargando = false,
  disabled = false,
  type = 'button',
  className = '',
  ...props
}) {
  // Una variante inexistente cae en la primaria en lugar de dejar el botón sin estilos.
  const estilo = variantes[variante] ?? variantes.primario
  return (
    <button
      type={type}
      disabled={disabled || cargando}
      className={`inline-flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2 font-medium disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-2 sm:w-auto ${estilo} ${className}`}
      aria-busy={cargando || undefined}
      {...props}
    >
      {cargando && <span aria-hidden="true" className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />}
      {children}
      {cargando && <span className="sr-only"> (cargando)</span>}
    </button>
  )
}
