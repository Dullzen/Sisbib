import { Link } from 'react-router-dom'

export default function Landing() {
  return (
    <main className="container center">
      <h1>Biblioteca</h1>
      <p>Bienvenido al sistema bibliotecario.</p>
      <div className="card">
        <h2>Acceso</h2>
        <div className="roles">
          <Link to="/admin/login" className="btn">Admin</Link>
          <button className="btn" disabled title="Próximamente">Bibliotecario</button>
          <button className="btn" disabled title="Próximamente">Cliente</button>
        </div>
      </div>
    </main>
  )
}
