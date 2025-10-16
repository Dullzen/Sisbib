import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'

export default function AdminLogin() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    // Fake auth for prototype
    if (email && password) {
      navigate('/admin/dashboard')
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
        <button className="btn primary" type="submit">Sign In</button>
        <a className="muted" href="#">Forgot password?</a>
      </form>
    </main>
  )
}
