// Activación de la cuenta y recuperación de contraseña (RF-14). Los enlaces llegan por correo.
import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import Alerta from '../components/Alerta.jsx'
import Button from '../components/Button.jsx'
import Card from '../components/Card.jsx'
import { Exito } from '../components/Estados.jsx'
import Input from '../components/Input.jsx'
import { authService } from '../services/authService.js'

function DefinirPassword({ titulo, descripcion, accion, textoBoton, exito }) {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''
  const [password, setPassword] = useState('')
  const [confirmacion, setConfirmacion] = useState('')
  const [error, setError] = useState(null)
  const [listo, setListo] = useState(false)
  const [cargando, setCargando] = useState(false)

  async function enviar(e) {
    e.preventDefault()
    setError(null)
    if (password !== confirmacion) {
      setError({ message: 'Las contraseñas no coinciden.', errores: [{ campo: 'confirmacion', mensaje: 'Escribe la misma contraseña' }] })
      return
    }
    setCargando(true)
    try {
      await accion(token, password)
      setListo(true)
    } catch (err) {
      setError(err)
    } finally {
      setCargando(false)
    }
  }
  const errorDe = (c) => error?.errores?.find((x) => x.campo === c)?.mensaje

  return (
    <main className="mx-auto max-w-md p-4 sm:p-8">
      <h1 className="mb-2 text-2xl font-bold sm:text-3xl">{titulo}</h1>
      <p className="mb-6 text-slate-700">{descripcion}</p>
      {!token && <Alerta titulo="Falta el enlace">Abre el enlace que llegó a tu correo.</Alerta>}
      {listo ? (
        <Exito>{exito} <Link to="/login" className="font-medium underline">Iniciar sesión</Link></Exito>
      ) : token && (
        <Card>
          <form onSubmit={enviar} className="flex flex-col gap-4" noValidate>
            <Input id="password" label="Contraseña nueva" type="password" autoComplete="new-password" required minLength={8}
              value={password} onChange={(e) => setPassword(e.target.value)} error={errorDe('password')} />
            <Input id="confirmacion" label="Confirma la contraseña" type="password" autoComplete="new-password" required
              value={confirmacion} onChange={(e) => setConfirmacion(e.target.value)} error={errorDe('confirmacion')} />
            <p className="text-sm text-slate-600">Mínimo 8 caracteres.</p>
            {error && <Alerta titulo="No se pudo guardar">{error.message}</Alerta>}
            <Button type="submit" cargando={cargando}>{textoBoton}</Button>
          </form>
        </Card>
      )}
    </main>
  )
}

export function Activar() {
  return <DefinirPassword titulo="Activa tu cuenta" textoBoton="Activar cuenta" accion={authService.activar}
    descripcion="La Administración del condominio te creó una cuenta en ReportaYa. Define tu contraseña para entrar."
    exito="Tu cuenta quedó activa." />
}

export function Restablecer() {
  return <DefinirPassword titulo="Nueva contraseña" textoBoton="Guardar contraseña" accion={authService.restablecer}
    descripcion="Define una contraseña nueva. El enlace funciona una sola vez y vence en 1 hora."
    exito="Tu contraseña se actualizó." />
}

export function Recuperar() {
  const [correo, setCorreo] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [error, setError] = useState(null)
  const [cargando, setCargando] = useState(false)
  async function enviar(e) {
    e.preventDefault()
    setCargando(true)
    setError(null)
    try {
      setMensaje((await authService.pedirRecuperacion(correo)).mensaje)
    } catch (err) {
      setError(err)
    } finally {
      setCargando(false)
    }
  }
  return (
    <main className="mx-auto max-w-md p-4 sm:p-8">
      <h1 className="mb-6 text-2xl font-bold sm:text-3xl">Recuperar contraseña</h1>
      {mensaje ? <Exito>{mensaje}</Exito> : (
        <Card>
          <form onSubmit={enviar} className="flex flex-col gap-4" noValidate>
            <Input id="correo" label="Correo" type="email" autoComplete="email" required value={correo} onChange={(e) => setCorreo(e.target.value)}
              error={error?.errores?.find((x) => x.campo === 'correo')?.mensaje} />
            {error && <Alerta titulo="No se pudo enviar">{error.message}</Alerta>}
            <Button type="submit" cargando={cargando}>Enviar enlace</Button>
          </form>
        </Card>
      )}
      <p className="mt-4"><Link to="/login" className="text-blue-700 underline">Volver a iniciar sesión</Link></p>
    </main>
  )
}
