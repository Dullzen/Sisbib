import { useEffect, useState } from "react";

const API = "http://127.0.0.1:5000";

export default function BibliotecarioDashboard() {
  const [tab, setTab] = useState<"libros" | "solicitudes" | "prestamos" | "sanciones">("libros");
  const [data, setData] = useState<any[]>([]);
  const [msg, setMsg] = useState<string>("");

  //  helper
  async function api(path: string, options: RequestInit = {}) {
    const r = await fetch(`${API}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    const j = await r.json();
    return j;
  }

  // -------------------------------
  // LIBROS
  // -------------------------------
  async function cargarLibros() {
    const res = await api("/api/libros");
    if (res.ok) setData(res.items);
  }

  async function agregarLibro() {
    const titulo = prompt("Título del libro:");
    const autor = prompt("Autor:");
    if (!titulo || !autor) return;
    const res = await api("/api/libros", {
      method: "POST",
      body: JSON.stringify({ titulo, autor }),
    });
    setMsg(res.ok ? "Libro agregado" : res.error);
    cargarLibros();
  }

  // -------------------------------
  // SOLICITUDES
  // -------------------------------
  async function cargarSolicitudes() {
    const res = await api("/api/solicitudes?estado=pending,ready");
    if (res.ok) setData(res.items);
  }

  async function cambiarEstadoSolicitud(id: number, estado: string) {
    const res = await api(`/api/solicitudes/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ estado }),
    });
    setMsg(res.ok ? `Solicitud ${id} → ${estado}` : res.error);
    cargarSolicitudes();
  }

  // -------------------------------
  // PRÉSTAMOS
  // -------------------------------
  async function cargarPrestamos() {
    const res = await api("/api/prestamos");
    if (res.ok) setData(res.items);
  }

  async function crearPrestamo() {
    const user_id = prompt("ID usuario:");
    const id_ejemplar = prompt("ID ejemplar:");
    const tipo = prompt("Tipo (Sala o Domicilio):", "Sala");
    if (!user_id || !id_ejemplar) return;
    const res = await api("/api/prestamos", {
      method: "POST",
      body: JSON.stringify({ user_id: Number(user_id), id_ejemplar: Number(id_ejemplar), tipo }),
    });
    setMsg(res.ok ? "Préstamo registrado" : res.error);
    cargarPrestamos();
  }

  async function devolverEjemplar() {
    const id_ejemplar = prompt("ID del ejemplar a devolver:");
    const res = await api("/api/devoluciones", {
      method: "POST",
      body: JSON.stringify({ id_ejemplar: Number(id_ejemplar) }),
    });
    setMsg(res.ok ? "Devolución registrada" : res.error);
  }

  // -------------------------------
  // SANCIONES
  // -------------------------------
  async function cargarSanciones() {
    const res = await api("/api/sanciones");
    if (res.ok) setData(res.items);
  }

  // -------------------------------
  // Render dinámico
  // -------------------------------
  useEffect(() => {
    setData([]);
    if (tab === "libros") cargarLibros();
    if (tab === "solicitudes") cargarSolicitudes();
    if (tab === "prestamos") cargarPrestamos();
    if (tab === "sanciones") cargarSanciones();
  }, [tab]);

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-2">📘 Panel de Bibliotecario</h1>

      <div className="flex gap-2 mb-4">
        <button onClick={() => setTab("libros")} className="bg-blue-500 text-white px-3 py-1 rounded">Libros</button>
        <button onClick={() => setTab("solicitudes")} className="bg-amber-500 text-white px-3 py-1 rounded">Solicitudes</button>
        <button onClick={() => setTab("prestamos")} className="bg-green-600 text-white px-3 py-1 rounded">Préstamos</button>
        <button onClick={() => setTab("sanciones")} className="bg-red-600 text-white px-3 py-1 rounded">Sanciones</button>
      </div>

      <p className="text-sm text-gray-700 mb-2">{msg}</p>

      {/* LIBROS */}
      {tab === "libros" && (
        <div>
          <button onClick={agregarLibro} className="bg-blue-600 text-white px-3 py-1 rounded mb-2">+ Agregar Libro</button>
          <table className="w-full border">
            <thead><tr className="bg-gray-200"><th>ID</th><th>Título</th><th>Autor</th><th>Categoría</th></tr></thead>
            <tbody>
              {data.map((l) => (
                <tr key={l.id_libro}><td>{l.id_libro}</td><td>{l.titulo}</td><td>{l.autor}</td><td>{l.categoria}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* SOLICITUDES */}
      {tab === "solicitudes" && (
        <table className="w-full border">
          <thead><tr className="bg-gray-200"><th>ID</th><th>Usuario</th><th>Estado</th><th>Acciones</th></tr></thead>
          <tbody>
            {data.map((s) => (
              <tr key={s.solicitud_id}>
                <td>{s.solicitud_id}</td>
                <td>{s.nombre}</td>
                <td>{s.estado}</td>
                <td>
                  {s.estado === "pending" && (
                    <button onClick={() => cambiarEstadoSolicitud(s.solicitud_id, "ready")} className="bg-green-500 text-white px-2 py-1 rounded">Marcar Ready</button>
                  )}
                  {s.estado === "ready" && (
                    <button onClick={() => cambiarEstadoSolicitud(s.solicitud_id, "served")} className="bg-blue-600 text-white px-2 py-1 rounded">Servida</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* PRÉSTAMOS */}
      {tab === "prestamos" && (
        <div>
          <div className="flex gap-2 mb-2">
            <button onClick={crearPrestamo} className="bg-green-700 text-white px-3 py-1 rounded">+ Crear Préstamo</button>
            <button onClick={devolverEjemplar} className="bg-amber-600 text-white px-3 py-1 rounded">Registrar Devolución</button>
          </div>
          <table className="w-full border">
            <thead><tr className="bg-gray-200"><th>ID</th><th>Usuario</th><th>Libro</th><th>Tipo</th><th>Vence</th></tr></thead>
            <tbody>
              {data.map((p) => (
                <tr key={p.prestamo_id}>
                  <td>{p.prestamo_id}</td><td>{p.nombre}</td><td>{p.titulo}</td><td>{p.tipo_prestamo}</td><td>{p.fecha_vencimiento}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* SANCIONES */}
      {tab === "sanciones" && (
        <table className="w-full border">
          <thead><tr className="bg-gray-200"><th>ID</th><th>Usuario</th><th>Motivo</th><th>Hasta</th></tr></thead>
          <tbody>
            {data.map((s) => (
              <tr key={s.sancion_id}>
                <td>{s.sancion_id}</td><td>{s.nombre}</td><td>{s.motivo}</td><td>{s.hasta}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
