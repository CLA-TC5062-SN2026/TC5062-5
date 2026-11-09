const variantes = {
  primario: 'bg-blue-600 text-white hover:bg-blue-700',
  secundario: 'bg-white text-blue-600 border border-blue-600 hover:bg-blue-50',
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
      className={`inline-flex w-full items-center justify-center gap-2 rounded-lg px-4 py-2 font-medium disabled:opacity-60 sm:w-auto ${estilo} ${className}`}
      {...props}
    >
      {cargando && <span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />}
      {children}
    </button>
  )
}
