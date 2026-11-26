import { useCallback, useEffect, useState } from 'react'

// Carga datos con cancelación al desmontar y permite recargar. `fn(signal)` devuelve una promesa.
export function useCarga(fn, deps = []) {
  const [estado, setEstado] = useState({ cargando: true, error: null, datos: null })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const cargar = useCallback(fn, deps)
  const ejecutar = useCallback(async (signal) => {
    try {
      const datos = await cargar(signal)
      if (!signal?.aborted) setEstado({ cargando: false, error: null, datos })
    } catch (error) {
      if (!signal?.aborted) setEstado({ cargando: false, error, datos: null })
    }
  }, [cargar])
  useEffect(() => {
    const control = new AbortController()
    setEstado((e) => ({ ...e, cargando: true }))
    ejecutar(control.signal)
    return () => control.abort()
  }, [ejecutar])
  const recargar = useCallback(() => ejecutar(), [ejecutar])
  return { ...estado, recargar }
}
