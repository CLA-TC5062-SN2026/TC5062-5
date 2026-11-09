// Mensaje de error visible para el usuario. role="alert" hace que el lector de pantalla lo anuncie.
export default function Alerta({ titulo = 'Algo salió mal', children, accion }) {
  return (
    <div role="alert" className="rounded-lg border border-red-300 bg-red-50 p-4 text-red-800">
      <p className="font-semibold">{titulo}</p>
      <p className="mt-1">{children}</p>
      {accion && <div className="mt-3">{accion}</div>}
    </div>
  )
}
