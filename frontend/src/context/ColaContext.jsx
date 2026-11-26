// Envíos pendientes (RNF-11): procesa la cola al recuperar señal, al iniciar sesión y cada 20 s.
// El usuario distingue «Pendiente», «Enviado» y «Rechazado» en /pendientes; un envío confirmado no se pierde.
import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { actualizar, encolar as guardar, esFallaDeRed, listar, quitar } from '../lib/cola.js'
import { reportesService } from '../services/reportesService.js'
import { useAuth } from './AuthContext.jsx'

const ColaContext = createContext(null)

export function ColaProvider({ children }) {
  const { usuario } = useAuth()
  const [items, setItems] = useState([])
  const [enLinea, setEnLinea] = useState(() => navigator.onLine)
  const procesando = useRef(false)

  const refrescar = useCallback(async () => setItems((await listar()).sort((a, b) => a.creado.localeCompare(b.creado))), [])

  const procesar = useCallback(async () => {
    if (procesando.current || !usuario) return
    procesando.current = true
    try {
      for (const item of (await listar()).filter((i) => i.estado === 'Pendiente' && i.usuarioId === usuario.id)) {
        try {
          const op = { headers: { 'Idempotency-Key': item.id } }
          const res = item.tipo === 'reporte'
            ? await reportesService.crear(item.datos, item.fotos, item.video, op)
            : await reportesService.terminar(item.folio, item.datos, item.fotos, op)
          await actualizar({ ...item, estado: 'Enviado', folio: res.folio, enviado: new Date().toISOString(), fotos: [], video: null })
        } catch (e) {
          if (esFallaDeRed(e)) break                          // sigue sin señal: se intenta después
          if (e.status === 401) break                         // sesión vencida: se envía al volver a entrar
          await actualizar({ ...item, estado: 'Rechazado', error: e.message, intentos: item.intentos + 1 })
        }
      }
    } finally {
      procesando.current = false
      refrescar()
    }
  }, [usuario, refrescar])

  useEffect(() => {
    const arriba = () => { setEnLinea(true); procesar() }
    const abajo = () => setEnLinea(false)
    window.addEventListener('online', arriba)
    window.addEventListener('offline', abajo)
    const t = setInterval(procesar, 20000)
    procesar()
    return () => { window.removeEventListener('online', arriba); window.removeEventListener('offline', abajo); clearInterval(t) }
  }, [procesar, refrescar])

  const encolar = useCallback(async (item) => { await guardar({ ...item, usuarioId: usuario.id }); await refrescar() }, [usuario, refrescar])
  const descartar = useCallback(async (id) => { await quitar(id); await refrescar() }, [refrescar])
  const mios = items.filter((i) => i.usuarioId === usuario?.id)

  return (
    <ColaContext.Provider value={{ items: mios, pendientes: mios.filter((i) => i.estado === 'Pendiente').length, enLinea, encolar, procesar, descartar }}>
      {children}
    </ColaContext.Provider>
  )
}

// eslint-disable-next-line react/only-export-components -- el hook vive junto a su proveedor
export const useCola = () => useContext(ColaContext)
