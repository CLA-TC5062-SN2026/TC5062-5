// Cola de envíos sin conexión (RNF-11) en IndexedDB: guarda lo capturado, incluidas las fotos (Blob), en el
// dispositivo. Cada envío lleva una Idempotency-Key fija, así reintentarlo nunca duplica el reporte.
const BD = 'reportaya'
const ALMACEN = 'pendientes'

function abrir() {
  return new Promise((ok, mal) => {
    const req = indexedDB.open(BD, 1)
    req.onupgradeneeded = () => req.result.createObjectStore(ALMACEN, { keyPath: 'id' })
    req.onsuccess = () => ok(req.result)
    req.onerror = () => mal(req.error)
  })
}

async function operar(modo, fn) {
  const db = await abrir()
  return new Promise((ok, mal) => {
    const t = db.transaction(ALMACEN, modo)
    const r = fn(t.objectStore(ALMACEN))
    t.oncomplete = () => ok(r?.result)
    t.onerror = () => mal(t.error)
  })
}

export const nuevaClave = () => (crypto.randomUUID ? crypto.randomUUID() : `${Date.now()}-${Math.random().toString(36).slice(2)}`)

// item: { tipo: 'reporte' | 'terminado', usuarioId, folio?, datos, fotos: File[], video?: File, resumen }
export const encolar = (item) =>
  operar('readwrite', (s) => s.put({ ...item, id: item.id ?? nuevaClave(), estado: 'Pendiente', creado: new Date().toISOString(), intentos: 0 }))
export const listar = () => operar('readonly', (s) => s.getAll())
export const actualizar = (item) => operar('readwrite', (s) => s.put(item))
export const quitar = (id) => operar('readwrite', (s) => s.delete(id))

// Sin señal o sin respuesta del servidor: el envío se guarda en la cola en lugar de mostrarse como error.
export const esFallaDeRed = (e) => ['ERROR_DE_RED', 'TIEMPO_AGOTADO'].includes(e?.codigo)
