import { useState } from 'react'
import Button from '../components/Button.jsx'
import Card from '../components/Card.jsx'
import Input from '../components/Input.jsx'
import { useAuth } from '../context/AuthContext.jsx'

// Página de muestra de los 4 componentes (S07-S08-A1, Parte 2).
export default function Inicio() {
  const { login } = useAuth()
  const [correo, setCorreo] = useState('admin@reportaya.demo')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  async function entrar(e) {
    e.preventDefault()
    setCargando(true)
    setError('')
    try {
      await login(correo, password)
    } catch (err) {
      setError(err.message)
    } finally {
      setCargando(false)
    }
  }

  return (
    <main className="mx-auto max-w-5xl p-4 sm:p-8">
      <h1 className="text-2xl font-bold sm:text-3xl">ReportaYa</h1>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card titulo="Fuga en baño común" subtitulo="Folio R-0012 · Torre B" pie={<Button variante="secundario">Ver detalle</Button>}>
          <p>Prioridad alta · En proceso</p>
        </Card>
        <Card titulo="Botones">
          <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap">
            <Button>Primario</Button>
            <Button variante="secundario">Secundario</Button>
            <Button cargando>Guardando</Button>
          </div>
        </Card>
        <Card titulo="Iniciar sesión" subtitulo="Prueba del Navbar autenticado">
          <form onSubmit={entrar} className="flex flex-col gap-3">
            <Input id="correo" label="Correo" type="email" value={correo} onChange={(e) => setCorreo(e.target.value)} />
            <Input id="password" label="Contraseña" type="password" value={password}
              onChange={(e) => setPassword(e.target.value)} error={error} />
            <Button type="submit" cargando={cargando}>Entrar</Button>
          </form>
        </Card>
      </div>
    </main>
  )
}
