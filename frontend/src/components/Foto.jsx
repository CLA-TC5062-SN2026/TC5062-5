import { useEffect, useState } from 'react'
import { reportesService } from '../services/reportesService.js'

// Las fotos se piden con el token (no son públicas, RD-08): se descargan como blob y se muestran con una URL local.
export default function Foto({ folio, archivo }) {
  const [url, setUrl] = useState(null)
  const [error, setError] = useState(false)
  useEffect(() => {
    let local
    const control = new AbortController()
    reportesService.archivo(folio, archivo.id, { signal: control.signal })
      .then((blob) => { local = URL.createObjectURL(blob); setUrl(local) })
      .catch(() => !control.signal.aborted && setError(true))
    return () => { control.abort(); if (local) URL.revokeObjectURL(local) }
  }, [folio, archivo.id])

  if (error) return <div className="flex h-28 w-28 items-center justify-center rounded-lg bg-slate-100 p-2 text-center text-xs text-slate-600">No se pudo cargar</div>
  if (!url) return <div className="h-28 w-28 animate-pulse rounded-lg bg-slate-100" aria-label="Cargando foto" />
  if (archivo.tipo === 'Video') return <video src={url} controls className="h-28 rounded-lg" aria-label={archivo.nombre} />
  return (
    <a href={url} target="_blank" rel="noreferrer" className="block">
      <img src={url} alt={`Foto ${archivo.nombre}`} className="h-28 w-28 rounded-lg object-cover" />
    </a>
  )
}
