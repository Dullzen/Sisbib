import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth, Role, AuthState } from '../auth'

export default function SiteLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('admin')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { login } = useAuth()

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, role })
      })
      const data = await res.json()
      if (!res.ok || !data.ok) {
        throw new Error(data?.error || 'Error de autenticación')
      }
      const finalRole = (data.role || role) as Role
      const nextAuth: AuthState = {
        role: finalRole,
        user: data.user
      }
  login(nextAuth)
  const dest = finalRole === 'admin' ? '/admin/dashboard' : finalRole === 'bibliotecario' ? '/bibliotecario/home' : '/cliente/home'
  navigate(dest, { replace: true })
    } catch (err: any) {
      setError(err?.message || 'No se pudo iniciar sesión')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container center">
      <h1>Bienvenido</h1>
      <form className="card form" onSubmit={onSubmit}>
        <label>
          Email
          <input type="email" placeholder="Value" value={email} onChange={e => setEmail(e.target.value)} required />
        </label>
        <label>
          Password
          <input type="password" placeholder="Value" value={password} onChange={e => setPassword(e.target.value)} required />
        </label>
        {error && <div className="error" role="alert" style={{color: 'crimson', marginBottom: 8}}>{error}</div>}
        <button className="btn primary" type="submit" disabled={loading}>{loading ? 'Ingresando…' : 'Ingresar'}</button>
        <a className="muted" href="#">¿Olvidaste tu contraseña?</a>
      </form>
    </main>
  )
}
