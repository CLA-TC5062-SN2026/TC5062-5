import { useQuery } from '@tanstack/react-query'
import { API_URL } from '../services/config'
import { consultarSalud } from '../services/saludService'

/** Muestra si el frontend alcanza al backend. Sirve para verificar la configuración de VITE_API_URL y del proxy. */
export function EstadoApi() {
  const { data, error, isPending, refetch, isFetching } = useQuery({
    queryKey: ['salud'],
    queryFn: consultarSalud,
    retry: false,
  })

  return (
    <section aria-live="polite" className="rounded-lg border border-borde bg-superficie p-4">
      <h2 className="text-base font-semibold">Conexión con el servidor</h2>
      <p className="mt-1 text-sm text-texto-suave">
        API: <code>{API_URL}</code>
      </p>

      {isPending && <p className="mt-3">Verificando…</p>}

      {data && (
        <p className="mt-3 font-medium text-exito">
          Conectado · base de datos «{data.baseDeDatos}» con {data.tablas} tablas
        </p>
      )}

      {error && (
        <p className="mt-3 font-medium text-error">
          Sin conexión: {error.message}. Verifique que el backend esté corriendo.
        </p>
      )}

      <button
        type="button"
        onClick={() => refetch()}
        disabled={isFetching}
        className="mt-4 min-h-11 rounded-md bg-primario px-4 font-medium text-white hover:bg-primario-oscuro disabled:opacity-60"
      >
        {isFetching ? 'Verificando…' : 'Verificar de nuevo'}
      </button>
    </section>
  )
}
