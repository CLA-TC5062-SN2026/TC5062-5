export default function Card({ titulo, subtitulo, pie, children }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
      {titulo && <h2 className="text-lg font-semibold">{titulo}</h2>}
      {subtitulo && <p className="text-sm text-slate-400">{subtitulo}</p>}
      <div className="mt-3">{children}</div>
      {pie && <div className="mt-4 border-t border-slate-100 pt-3">{pie}</div>}
    </div>
  )
}
