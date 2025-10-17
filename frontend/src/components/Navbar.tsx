import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'

export default function Navbar() {
  const { pathname } = useLocation()
  const isAdminFlow = pathname.startsWith('/admin')
  const { auth, roleHome, displayName, logout } = useAuth()
  const navigate = useNavigate()

  const onLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="navbar">
      <Link to={auth ? roleHome : '/'} className="navbar__brand">Bec</Link>
      <nav className="navbar__links">
        <Link to={auth ? roleHome : '/'} className={!isAdminFlow ? 'active' : ''}>Inicio</Link>
        {!auth && (
          <Link to="/login" className={pathname === '/login' ? 'active' : ''}>Ingresar</Link>
        )}
        {auth && (
          <>
            <span className="navbar__user" title={auth.user.email} style={{ marginRight: 12 }}>{displayName}</span>
            <button className="btn" onClick={onLogout}>Cerrar sesión</button>
          </>
        )}
      </nav>
    </header>
  )
}
