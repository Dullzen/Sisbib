import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const { pathname } = useLocation()
  const isAdminFlow = pathname.startsWith('/admin')

  return (
    <header className="navbar">
      <div className="navbar__brand">Bec</div>
      <nav className="navbar__links">
        <Link to="/" className={!isAdminFlow ? 'active' : ''}>Inicio</Link>
    <Link to="/login" className={pathname === '/login' ? 'active' : ''}>Ingresar</Link>
      </nav>
    </header>
  )
}
