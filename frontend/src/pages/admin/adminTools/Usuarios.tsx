import { useEffect, useMemo, useState } from 'react'

type User = {
  user_id: number
  nombre: string
  apellido1: string
  apellido2: string
  rut_numero: number
  rut_dv: string
  email: string
  role: 'Cliente' | 'Bibliotecario' | 'Admin'
  created_at?: string
}

export default function Usuarios() {
  const [q, setQ] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [items, setItems] = useState<User[]>([])

  const fetchUsers = async (signal?: AbortSignal) => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (q.trim()) params.set('q', q.trim())
      const res = await fetch(`/api/users?${params.toString()}`, { signal })
      const data = await res.json()
      if (!data.ok) throw new Error(data.error || 'Error al cargar usuarios')
      setItems(data.items as User[])
    } catch (e: any) {
      if (e.name !== 'AbortError') setError(e.message || 'Error inesperado')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const ctrl = new AbortController()
    fetchUsers(ctrl.signal)
    return () => ctrl.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const onSubmit = (ev: React.FormEvent) => {
    ev.preventDefault()
    const ctrl = new AbortController()
    fetchUsers(ctrl.signal)
  }

  const rows = useMemo(() => items, [items])

  return (
    <main className="container">
      <h2>Usuarios</h2>
      <form className="filterbar" onSubmit={onSubmit}>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Buscar por nombre, email o RUT" />
        <button className="btn" type="submit" disabled={loading}>Buscar</button>
      </form>
      {error && <p className="error">{error}</p>}
      <div className="tablewrap">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>RUT</th>
              <th>Email</th>
              <th>Rol</th>
              <th>Creado</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6}>Cargando…</td></tr>
            ) : rows.length ? rows.map(u => (
              <tr key={u.user_id}>
                <td>{u.user_id}</td>
                <td>{u.nombre} {u.apellido1} {u.apellido2}</td>
                <td>{u.rut_numero}-{u.rut_dv}</td>
                <td>{u.email}</td>
                <td>{u.role}</td>
                <td>{u.created_at ? new Date(u.created_at).toLocaleDateString() : '-'}</td>
              </tr>
            )) : (
              <tr><td colSpan={6}>Sin resultados</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  )
}
