import { Outlet } from 'react-router'

/** Estructura común: encabezado, contenido de la ruta activa y pie. Diseñada desde 360 px (RNF-01). */
export function Layout() {
  return (
    <div className="flex min-h-dvh flex-col">
      <header className="bg-primario text-white">
        <div className="mx-auto flex max-w-5xl items-center px-4 py-3">
          <span className="text-lg font-semibold">ReportaYa</span>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-borde">
        <p className="mx-auto max-w-5xl px-4 py-3 text-sm text-texto-suave">
          Incidencias de mantenimiento del condominio
        </p>
      </footer>
    </div>
  )
}
