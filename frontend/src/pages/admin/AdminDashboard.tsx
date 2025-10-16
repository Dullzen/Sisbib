import { Link } from 'react-router-dom'

export default function AdminDashboard() {
  return (
    <main className="container">
      <h1 className="center">Dashboard</h1>
      <div className="grid">
        <Link to="/admin/usuarios" className="tile">
          <div className="tile__icon" aria-hidden>👥</div>
          <div className="tile__title">Usuarios</div>
        </Link>
        <Link to="/admin/registro-ficha" className="tile">
          <div className="tile__icon" aria-hidden>🗂️</div>
          <div className="tile__title">Registro de ficha</div>
        </Link>
        <Link to="/admin/prestamos-domicilio" className="tile">
          <div className="tile__icon" aria-hidden>🏠</div>
          <div className="tile__title">Prestamos domicilio</div>
        </Link>
        <Link to="/admin/prestamos-sala" className="tile">
          <div className="tile__icon" aria-hidden>🏢</div>
          <div className="tile__title">Prestamos sala</div>
        </Link>
      </div>
    </main>
  )
}
