import { Routes, Route, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'
import SiteLogin from './SiteLogin'
import AdminDashboard from './pages/admin/AdminDashboard'
import Usuarios from './pages/admin/adminTools/Usuarios'
import RegistroFicha from './pages/admin/adminTools/RegistroFicha'
import PrestamosDomicilio from './pages/admin/adminTools/PrestamosDomicilio'
import PrestamosSala from './pages/admin/adminTools/PrestamosSala'
import Navbar from './components/Navbar'

export default function App() {
return (
    <div className="app">
        <Navbar />
        <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<SiteLogin />} />
            <Route path="/admin/dashboard" element={<AdminDashboard />} />

            {/* placeholders */}
            <Route path="/admin/usuarios" element={<Usuarios />} />
            <Route path="/admin/registro-ficha" element={<RegistroFicha />} />
            <Route path="/admin/prestamos-domicilio" element={<PrestamosDomicilio />} />
            <Route path="/admin/prestamos-sala" element={<PrestamosSala />} />

            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    </div>
)
}
