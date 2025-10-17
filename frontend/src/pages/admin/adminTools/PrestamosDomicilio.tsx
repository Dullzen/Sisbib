import { useEffect, useMemo, useState } from 'react'

type Item = {
  prestamo_id: number
  fecha_reserva: string
  fecha_vencimiento: string
  tipo_prestamo: 'Sala' | 'Domicilio'
  user_id: number
  nombre: string
  apellido1: string
  apellido2: string
  email: string
  id_libro: number
  titulo: string
  autor: string
  categoria?: string
}

export default function PrestamosDomicilio() {
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [items, setItems] = useState<Item[]>([])

  const fetchItems = async (signal?: AbortSignal) => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ tipo: 'Domicilio' })
      if (q.trim()) params.set('q', q.trim())
      const res = await fetch(`/api/prestamos?${params.toString()}`, { signal })
      const data = await res.json()
      if (!data.ok) throw new Error(data.error || 'Error al cargar préstamos')
      setItems(data.items as Item[])
    } catch (e: any) {
      if (e.name !== 'AbortError') setError(e.message || 'Error inesperado')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const ctrl = new AbortController()
    fetchItems(ctrl.signal)
    return () => ctrl.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const onSubmit = (ev: React.FormEvent) => {
    ev.preventDefault()
    const ctrl = new AbortController()
    fetchItems(ctrl.signal)
  }

  const rows = useMemo(() => items, [items])

  return (
    <main className="container">
      <h2>Préstamos domicilio</h2>
      <form className="filterbar" onSubmit={onSubmit}>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Buscar por usuario, libro o email" />
        <button className="btn" type="submit" disabled={loading}>Buscar</button>
      </form>
      {error && <p className="error">{error}</p>}
      <div className="tablewrap">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Usuario</th>
              <th>Email</th>
              <th>Libro</th>
              <th>Autor</th>
              <th>Reserva</th>
              <th>Vence</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7}>Cargando…</td></tr>
            ) : rows.length ? rows.map(p => (
              <tr key={p.prestamo_id}>
                <td>{p.prestamo_id}</td>
                <td>{p.nombre} {p.apellido1} {p.apellido2}</td>
                <td>{p.email}</td>
                <td>{p.titulo}</td>
                <td>{p.autor}</td>
                <td>{new Date(p.fecha_reserva).toLocaleDateString()}</td>
                <td>{new Date(p.fecha_vencimiento).toLocaleDateString()}</td>
              </tr>
            )) : (
              <tr><td colSpan={7}>Sin resultados</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  )
}
