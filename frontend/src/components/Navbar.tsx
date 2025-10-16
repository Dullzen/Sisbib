import { Link, useLocation } from 'react-router-dom'

export default function Navbar() {
  const { pathname } = useLocation()
  const isAdminFlow = pathname.startsWith('/admin')

  return (
    <header className="navbar">
      <div className="navbar__brand">Beco Admin</div>
      <nav className="navbar__links">
        <Link to="/" className={!isAdminFlow ? 'active' : ''}>Inicio</Link>
        <div className="navbar__roles">
          <span>Roles:</span>
          <Link to="/admin/login" className={pathname.includes('/admin') ? 'active' : ''}>Admin</Link>
          <button className="link" disabled title="Próximamente">Bibliotecario</button>
          <button className="link" disabled title="Próximamente">Cliente</button>
        </div>
      </nav>
    </header>
  )
}
