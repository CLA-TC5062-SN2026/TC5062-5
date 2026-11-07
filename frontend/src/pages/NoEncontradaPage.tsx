import { Link } from 'react-router'

export function NoEncontradaPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Página no encontrada</h1>
      <p className="text-texto-suave">La dirección que abrió no existe.</p>
      <Link to="/" className="font-medium text-primario underline">
        Volver al inicio
      </Link>
    </div>
  )
}
