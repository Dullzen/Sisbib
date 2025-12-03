import { Link } from 'react-router-dom'

export default function BibliotecarioHome() {
  return (
    <main className="container">
      <h1 className="center">Panel de Bibliotecario</h1>
      <p className="center muted">
        Gestiona el catálogo, solicitudes, préstamos y sanciones de la biblioteca.
      </p>

      <div className="grid">
        <Link to="/bibliotecario/dashboard?tab=libros" className="tile">
          <div className="tile__icon" aria-hidden>📚</div>
          <div className="tile__title">Libros</div>
        </Link>

        <Link to="/bibliotecario/dashboard?tab=solicitudes" className="tile">
          <div className="tile__icon" aria-hidden>📥</div>
          <div className="tile__title">Solicitudes</div>
        </Link>

        <Link to="/bibliotecario/dashboard?tab=prestamos" className="tile">
          <div className="tile__icon" aria-hidden>🏦</div>
          <div className="tile__title">Préstamos</div>
        </Link>

        <Link to="/bibliotecario/dashboard?tab=sanciones" className="tile">
          <div className="tile__icon" aria-hidden>⚠️</div>
          <div className="tile__title">Sanciones</div>
        </Link>
      </div>
    </main>
  )
}
