export default function Inicio() {
  return (
    <main className="mx-auto max-w-3xl p-4 sm:p-8">
      <h1 className="text-2xl font-bold sm:text-3xl">ReportaYa</h1>
      <p className="mt-2 text-slate-700">Reporte y seguimiento de incidencias de mantenimiento.</p>
      <p className="mt-4 text-sm text-slate-600">
        API: <code className="rounded bg-slate-100 px-1">{import.meta.env.VITE_API_URL}</code>
      </p>
    </main>
  )
}
