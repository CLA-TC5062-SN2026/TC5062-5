import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import Alerta from '../components/Alerta.jsx'
import Button from '../components/Button.jsx'
import Card from '../components/Card.jsx'
import Input from '../components/Input.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function Login() {
  const { token, login, aviso } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const destino = location.state?.desde ?? '/'
  const [correo, setCorreo] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [cargando, setCargando] = useState(false)

  if (token) return <Navigate to={destino} replace />

  async function entrar(e) {
    e.preventDefault()
    setCargando(true)
    setError(null)
    try {
      await login(correo, password)
      navigate(destino, { replace: true })
    } catch (err) {
      setError(err) // ApiError: trae un mensaje listo para el usuario
    } finally {
      setCargando(false)
    }
  }

  const errorDe = (campo) => error?.errores?.find((x) => x.campo === campo)?.mensaje

  return (
    <main className="mx-auto max-w-md p-4 sm:p-8">
      <h1 className="mb-6 text-2xl font-bold sm:text-3xl">Iniciar sesión</h1>
      {aviso && !error && <div className="mb-4"><Alerta titulo="Sesión cerrada">{aviso}</Alerta></div>}
      <Card>
        <form onSubmit={entrar} className="flex flex-col gap-4" noValidate>
          <Input id="correo" label="Correo" type="email" autoComplete="username" required
            value={correo} onChange={(e) => setCorreo(e.target.value)} error={errorDe('correo')} />
          <Input id="password" label="Contraseña" type="password" autoComplete="current-password" required
            value={password} onChange={(e) => setPassword(e.target.value)} error={errorDe('password')} />
          {error && <Alerta titulo="No se pudo iniciar sesión">{error.message}</Alerta>}
          <Button type="submit" cargando={cargando}>Entrar</Button>
        </form>
      </Card>
    </main>
  )
}
