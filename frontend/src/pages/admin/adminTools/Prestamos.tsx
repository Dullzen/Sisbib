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
  vencido?: boolean
}

export default function Prestamos() {
  const [q, setQ] = useState('')
  const [tipos, setTipos] = useState<('Sala' | 'Domicilio')[]>(['Sala', 'Domicilio'])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [items, setItems] = useState<Item[]>([])
  const [soloVencidos, setSoloVencidos] = useState(false)
  const [notifying, setNotifying] = useState(false)
  const [notificationMessage, setNotificationMessage] = useState<string | null>(null)

  const fetchItems = async (signal?: AbortSignal) => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (tipos.length > 0) {
        params.set('tipo', tipos.join(','))
      } else {
        // Si no hay tipos seleccionados, no mostrar nada
        setItems([])
        setLoading(false)
        return
      }
      if (q.trim()) params.set('q', q.trim())
      const res = await fetch(`/api/prestamos?${params.toString()}`, { signal })
      const data = await res.json()
      if (!data.ok) throw new Error(data.error || 'Error al cargar préstamos')
      let prestamos = data.items as Item[]
      // Agrega campo vencido
      const hoy = new Date()
      prestamos = prestamos.map(p => ({
        ...p,
        vencido: new Date(p.fecha_vencimiento) < hoy
      }))
      if (soloVencidos) {
        prestamos = prestamos.filter(p => p.vencido)
      }
      setItems(prestamos)
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
  }, [tipos, soloVencidos])

  const onSubmit = (ev: React.FormEvent) => {
    ev.preventDefault()
    const ctrl = new AbortController()
    fetchItems(ctrl.signal)
  }

  const handleNotifyOverdue = async () => {
    setNotifying(true)
    setNotificationMessage(null)
    try {
      const res = await fetch('/api/notify-overdue', { method: 'POST' })
      const data = await res.json()
      if (!data.ok) throw new Error(data.error || 'Error al enviar notificaciones')
      setNotificationMessage(data.message || 'Notificaciones enviadas con éxito.')
      // Re-fetch items to update vencido status
      fetchItems()
    } catch (e: any) {
      setNotificationMessage(e.message || 'Error inesperado al notificar')
    } finally {
      setNotifying(false)
    }
  }

  const handleTipoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value, checked } = e.target as { value: 'Sala' | 'Domicilio'; checked: boolean }
    setTipos(prev =>
      checked ? [...prev, value] : prev.filter(t => t !== value)
    )
  }

  const handleVencidosChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSoloVencidos(e.target.checked)
  }

  const rows = useMemo(() => items, [items])

  return (
    <main className="container">
      <h2>Préstamos</h2>
      <form className="filterbar" onSubmit={onSubmit}>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Buscar por usuario, libro o email" />
        <div className="filterbar__controls">
          <div className="checkbox-group">
            <label>
              <input type="checkbox" value="Sala" checked={tipos.includes('Sala')} onChange={handleTipoChange} />
              Sala
            </label>
            <label>
              <input type="checkbox" value="Domicilio" checked={tipos.includes('Domicilio')} onChange={handleTipoChange} />
              Domicilio
            </label>
            <label style={{ marginLeft: '1em' }}>
              <input type="checkbox" checked={soloVencidos} onChange={handleVencidosChange} />
              Solo vencidos
            </label>
          </div>
          <button className="btn" type="submit" disabled={loading}>Buscar</button>
          <button
            className="btn"
            type="button"
            onClick={handleNotifyOverdue}
            disabled={notifying}
            style={{ marginLeft: '1em' }}
          >
            {notifying ? 'Notificando...' : 'Notificar Vencidos'}
          </button>
        </div>
      </form>
      {notificationMessage && <p className={notificationMessage.startsWith('Error') ? 'error' : 'success'}>{notificationMessage}</p>}
      {error && <p className="error">{error}</p>}
      <div className="tablewrap">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Tipo</th>
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
              <tr><td colSpan={8}>Cargando…</td></tr>
            ) : rows.length ? rows.map(p => (
              <tr key={p.prestamo_id} style={p.vencido ? { background: '#ffe5e5' } : {}}>
                <td>{p.prestamo_id}</td>
                <td>{p.tipo_prestamo}</td>
                <td>{p.nombre} {p.apellido1} {p.apellido2}</td>
                <td>{p.email}</td>
                <td>{p.titulo}</td>
                <td>{p.autor}</td>
                <td>{new Date(p.fecha_reserva).toLocaleDateString()}</td>
                <td>{new Date(p.fecha_vencimiento).toLocaleDateString()}</td>
              </tr>
            )) : (
              <tr><td colSpan={8}>Sin resultados</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  )
}
