import { createBrowserRouter } from 'react-router'
import { Layout } from './components/Layout'
import { InicioPage } from './pages/InicioPage'
import { NoEncontradaPage } from './pages/NoEncontradaPage'

/** Rutas de la aplicación. Las guardas por rol se agregan con el login (tarea 01.3). */
export const router = createBrowserRouter([
  {
    element: <Layout />,
    children: [
      { path: '/', element: <InicioPage /> },
      { path: '*', element: <NoEncontradaPage /> },
    ],
  },
])
