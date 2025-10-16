import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function SiteLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('admin')
  const navigate = useNavigate()

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (email && password) {
      if (role === 'admin') navigate('/admin/dashboard')
      else if (role === 'bibliotecario') navigate('/bibliotecario/home')
      else if (role === 'cliente') navigate('/cliente/home')
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
        <button className="btn primary" type="submit">Ingresar</button>
        <a className="muted" href="#">¿Olvidaste tu contraseña?</a>
      </form>
    </main>
  )
}
