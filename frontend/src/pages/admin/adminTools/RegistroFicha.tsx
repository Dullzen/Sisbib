import { FormEvent, useState } from 'react'

const initialForm = {
  nombre: '',
  apellido1: '',
  apellido2: '',
  rut_numero: '',
  rut_dv: '',
  email: '',
  password: '',
  role: 'Cliente',
}

export default function RegistroFicha() {
  const [form, setForm] = useState(initialForm)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)
    try {
      const res = await fetch('/api/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          rut_numero: parseInt(form.rut_numero, 10)
        })
      })
      const data = await res.json()
      if (!res.ok || !data.ok) {
        throw new Error(data?.error || 'Error al registrar usuario')
      }
      setSuccess(`Usuario ${data.user.email} creado con éxito.`)
      setForm(initialForm) // Reset form
    } catch (err: any) {
      setError(err?.message || 'No se pudo registrar el usuario')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
  }

  return (
    <main className="container">
      <h2>Registro de Ficha de Usuario</h2>
      <form className="card form" onSubmit={onSubmit}>
        <div className="grid-col-2">
          <label>
            Nombre
            <input type="text" name="nombre" value={form.nombre} onChange={handleChange} required />
          </label>
          <label>
            Primer Apellido
            <input type="text" name="apellido1" value={form.apellido1} onChange={handleChange} required />
          </label>
        </div>
        <label>
          Segundo Apellido
          <input type="text" name="apellido2" value={form.apellido2} onChange={handleChange} required />
        </label>
        <div className="grid-col-2">
          <label>
            RUT (sin puntos ni guión)
            <input type="number" name="rut_numero" placeholder="Ej: 12345678" value={form.rut_numero} onChange={handleChange} required />
          </label>
          <label>
            Dígito Verificador
            <input type="text" name="rut_dv" placeholder="K" maxLength={1} value={form.rut_dv} onChange={handleChange} required style={{ textTransform: 'uppercase' }}/>
          </label>
        </div>
        <label>
          Email
          <input type="email" name="email" value={form.email} onChange={handleChange} required />
        </label>
        <label>
          Contraseña
          <input type="password" name="password" value={form.password} onChange={handleChange} required />
        </label>
        <label>
          Rol
          <select name="role" value={form.role} onChange={handleChange}>
            <option value="Cliente">Cliente</option>
            <option value="Bibliotecario">Bibliotecario</option>
            <option value="Admin">Admin</option>
          </select>
        </label>

        {error && <div className="error" role="alert">{error}</div>}
        {success && <div className="success" role="alert">{success}</div>}

        <button className="btn primary" type="submit" disabled={loading}>
          {loading ? 'Registrando…' : 'Registrar Usuario'}
        </button>
      </form>
    </main>
  )
}
