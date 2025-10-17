import { Navigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Landing() {
  const { auth, roleHome } = useAuth()
  if (auth) return <Navigate to={roleHome} replace />
  return (
    <main className="container center">
      <h1>Biblioteca</h1>
      <p>Bienvenido al sistema bibliotecario.</p>

    </main>
  )
}
