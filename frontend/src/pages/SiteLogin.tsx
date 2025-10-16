import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function SiteLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('admin')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

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
      const finalRole = (data.role || role) as string
      if (finalRole === 'admin') navigate('/admin/dashboard')
      else if (finalRole === 'bibliotecario') navigate('/bibliotecario/home')
      else navigate('/cliente/home')
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
        <div className="roles">
          <label><input type="radio" name="role" value="admin" checked={role==='admin'} onChange={()=>setRole('admin')} /> Admin</label>
          <label><input type="radio" name="role" value="bibliotecario" checked={role==='bibliotecario'} onChange={()=>setRole('bibliotecario')} /> Bibliotecario</label>
          <label><input type="radio" name="role" value="cliente" checked={role==='cliente'} onChange={()=>setRole('cliente')} /> Cliente</label>
        </div>
        {error && <div className="error" role="alert" style={{color: 'crimson', marginBottom: 8}}>{error}</div>}
        <button className="btn primary" type="submit" disabled={loading}>{loading ? 'Ingresando…' : 'Ingresar'}</button>
        <a className="muted" href="#">¿Olvidaste tu contraseña?</a>
      </form>
    </main>
  )
}
