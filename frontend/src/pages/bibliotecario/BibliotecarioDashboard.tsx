import { useEffect, useState } from 'react'
import { useLocation } from "react-router-dom";

type Tab = 'libros' | 'solicitudes' | 'prestamos' | 'sanciones'

type Libro = {
  id_libro: number
  titulo: string
  autor: string
  categoria?: string
  ejemplares_disponibles?: number
}

type Solicitud = {
  solicitud_id: number
  nombre: string
  estado: 'pending' | 'ready' | 'served'
}

type Prestamo = {
  prestamo_id: number
  nombre: string
  titulo: string
  tipo_prestamo: 'Sala' | 'Domicilio'
  fecha_vencimiento: string
}

type Sancion = {
  sancion_id: number
  nombre: string
  motivo: string
  hasta: string
}

type ApiResult<T> = {
  ok: boolean
  error?: string
  items?: T[]
}

async function api<T>(path: string, options: RequestInit = {}): Promise<ApiResult<T>> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  })
  return res.json()
}

export default function BibliotecarioDashboard() {
  const location = useLocation();

  const [tab, setTab] = useState<Tab>("libros");
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // leer ?tab=... del dashboard
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const q = params.get("tab");

    if (q === "libros" || q === "solicitudes" || q === "prestamos" || q === "sanciones") {
      setTab(q as Tab);
    }
  }, [location.search]);

  // ------------------ carga según pestaña ------------------
  const loadCurrentTab = async (t: Tab = tab) => {
  setLoading(true)
  setError(null)
  // ❌ NO borremos message aquí, para no perder los mensajes de acciones
  // setMessage(null)
  let result: ApiResult<any>

  if (t === 'libros') {
    result = await api<Libro>('/api/libros')
  } else if (t === 'solicitudes') {
    result = await api<Solicitud>('/api/solicitudes?estado=pending,ready')
  } else if (t === 'prestamos') {
    result = await api<Prestamo>('/api/prestamos?solo_activos=1')
  } else {
    result = await api<Sancion>('/api/sanciones')
  }

  if (!result.ok) {
    setError(result.error || 'Error al cargar datos')
    setData([])
  } else {
    setData(result.items || [])
  }
  setLoading(false)
}

  useEffect(() => {
    loadCurrentTab()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab])

  // ------------------ acciones ------------------
  const agregarLibro = async () => {
    const titulo = prompt('Título del libro:')
    const autor = prompt('Autor:')
    const categoria = prompt('Categoría (opcional):')
    const editorial = prompt('Editorial (opcional):')
    const edicion = prompt('Edición (opcional):')
    const anioStr = prompt('Año (opcional):')
    const ubicacion = prompt('Ubicación en biblioteca (opcional):')

    if (!titulo || !autor) return

    const anio = anioStr ? Number(anioStr) : null

    const res = await api('/api/libros', {
      method: 'POST',
      body: JSON.stringify({
        titulo,
        autor,
        categoria,
        editorial,
        edicion,
        anio,
        ubicacion,
      })
    })

    setMessage(res.ok ? 'Libro agregado.' : res.error || 'Error al agregar libro')
    await loadCurrentTab('libros')
  }

    const agregarEjemplar = async (id_libro: number) => {
      const res = await api('/api/ejemplares', {
        method: 'POST',
        body: JSON.stringify({ id_libro })
      })

      setMessage(res.ok ? 'Ejemplar agregado.' : res.error || 'Error al agregar ejemplar')
      await loadCurrentTab('libros')
    }




  const cambiarEstadoSolicitud = async (id: number, estado: string) => {
    const res = await api(`/api/solicitudes/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ estado })
    })
    setMessage(res.ok ? `Solicitud ${id} → ${estado}` : res.error || 'Error al actualizar solicitud')
    await loadCurrentTab('solicitudes')
  }

  const crearPrestamo = async () => {
  const user_id = prompt('ID usuario:')
  const id_ejemplar = prompt('ID ejemplar:')
  const tipo = prompt('Tipo (Sala o Domicilio):', 'Sala') || 'Sala'
  if (!user_id || !id_ejemplar) return

  const res = await api('/api/prestamos', {
    method: 'POST',
    body: JSON.stringify({
      user_id: Number(user_id),
      id_ejemplar: Number(id_ejemplar),
      tipo
    })
  })

  if (!res.ok) {
    setMessage(res.error || 'Error al registrar préstamo')
    return      // no recargamos tabla si falló
  }

  setMessage('Préstamo registrado.')
  await loadCurrentTab('prestamos')
}

    const devolverEjemplar = async () => {
      const id_ejemplar = prompt('ID del ejemplar a devolver:')
      if (!id_ejemplar) return

      const res = await api('/api/devoluciones', {
        method: 'POST',
        body: JSON.stringify({ id_ejemplar: Number(id_ejemplar) })
      })

      setMessage(res.ok ? 'Devolución registrada.' : res.error || 'Error al registrar devolución')

      if (res.ok) {
        // 👇 recarga solo la pestaña de préstamos
        await loadCurrentTab('prestamos')
      }
    }


  // ------------------ render ------------------
  const renderTabs = () => (
  <div className="tabbar">
    <button
      type="button"
      onClick={() => setTab('libros')}
      className={`tab-btn ${tab === 'libros' ? 'tab-btn--active' : ''}`}
    >
      Libros
    </button>

    <button
      type="button"
      onClick={() => setTab('solicitudes')}
      className={`tab-btn ${tab === 'solicitudes' ? 'tab-btn--active' : ''}`}
    >
      Solicitudes
    </button>

    <button
      type="button"
      onClick={() => setTab('prestamos')}
      className={`tab-btn ${tab === 'prestamos' ? 'tab-btn--active' : ''}`}
    >
      Préstamos
    </button>

    <button
      type="button"
      onClick={() => setTab('sanciones')}
      className={`tab-btn ${tab === 'sanciones' ? 'tab-btn--active' : ''}`}
    >
      Sanciones
    </button>
  </div>
);



  return (
    <main className="container">
      <h1 className="center">Panel de Bibliotecario</h1>

      {/* Pestañas + botones de acción */}
      <div className="tabbar-row">
        {renderTabs()}
        <div className="tab-actions">
          {tab === 'libros' && (
            <button className="action-btn action-btn--primary" type="button" onClick={agregarLibro}>
              + Agregar libro
            </button>
          )}
          {tab === 'prestamos' && (
            <>
              <button className="action-btn action-btn--primary" type="button" onClick={crearPrestamo}>
                + Crear préstamo
              </button>
              <button className="action-btn action-btn--primary" type="button" onClick={devolverEjemplar}>
                Registrar devolución
              </button>
            </>
          )}
        </div>
      </div>

      {message && <p className="success">{message}</p>}
      {error && <p className="error">{error}</p>}

      {/* LIBROS */}
      {tab === 'libros' && (
        <div className="tablewrap">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Título</th>
                <th>Autor</th>
                <th>Categoría</th>
                <th>Ejemplares disp.</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6}>Cargando…</td></tr>
              ) : data.length ? (
                (data as Libro[]).map(l => (
                  <tr key={l.id_libro}>
                    <td>{l.id_libro}</td>
                    <td>{l.titulo}</td>
                    <td>{l.autor}</td>
                    <td>{l.categoria || '-'}</td>
                    <td>{l.ejemplares_disponibles ?? 0}</td>
                    <td>
                      <button
                        className="btn"
                        type="button"
                        onClick={() => agregarEjemplar(l.id_libro)}
                      >
                        + Ejemplar
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={6}>Sin resultados</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}


      {/* SOLICITUDES */}
      {tab === 'solicitudes' && (
        <div className="tablewrap">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Usuario</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={4}>Cargando…</td></tr>
              ) : data.length ? (
                (data as Solicitud[]).map(s => (
                  <tr key={s.solicitud_id}>
                    <td>{s.solicitud_id}</td>
                    <td>{s.nombre}</td>
                    <td>{s.estado}</td>
                    <td>
                      {s.estado === 'pending' && (
                        <button
                          className="btn"
                          type="button"
                          onClick={() => cambiarEstadoSolicitud(s.solicitud_id, 'ready')}
                        >
                          Marcar ready
                        </button>
                      )}
                      {s.estado === 'ready' && (
                        <button
                          className="btn"
                          type="button"
                          onClick={() => cambiarEstadoSolicitud(s.solicitud_id, 'served')}
                        >
                          Servida
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={4}>Sin resultados</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* PRÉSTAMOS */}
      {tab === 'prestamos' && (
        <div className="tablewrap">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Usuario</th>
                <th>Libro</th>
                <th>Tipo</th>
                <th>Vence</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5}>Cargando…</td></tr>
              ) : data.length ? (
                (data as Prestamo[]).map(p => (
                  <tr key={p.prestamo_id}>
                    <td>{p.prestamo_id}</td>
                    <td>{p.nombre}</td>
                    <td>{p.titulo}</td>
                    <td>{p.tipo_prestamo}</td>
                    <td>{new Date(p.fecha_vencimiento).toLocaleDateString()}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={5}>Sin resultados</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* SANCIONES */}
      {tab === 'sanciones' && (
        <div className="tablewrap">
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Usuario</th>
                <th>Motivo</th>
                <th>Hasta</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={4}>Cargando…</td></tr>
              ) : data.length ? (
                (data as Sancion[]).map(s => (
                  <tr key={s.sancion_id}>
                    <td>{s.sancion_id}</td>
                    <td>{s.nombre}</td>
                    <td>{s.motivo}</td>
                    <td>{new Date(s.hasta).toLocaleDateString()}</td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={4}>Sin resultados</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </main>

  )
}
