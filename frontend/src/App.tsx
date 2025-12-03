import { Routes, Route, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'
import SiteLogin from './pages/SiteLogin'
import AdminDashboard from './pages/admin/AdminDashboard'
import Usuarios from './pages/admin/adminTools/Usuarios'
import RegistroFicha from './pages/admin/adminTools/RegistroFicha'
import Prestamos from './pages/admin/adminTools/Prestamos'
import Navbar from './components/Navbar'
import BibliotecarioHome from './pages/bibliotecario/BibliotecarioHome'
import BibliotecarioDashboard from "./pages/bibliotecario/BibliotecarioDashboard";
import ClienteHome from './pages/cliente/Home'
import Protected from './Protected'

export default function App() {
return (
    <div className="app">
        <Navbar />
        <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<SiteLogin />} />
            <Route path="/admin/dashboard" element={<Protected role="admin"><AdminDashboard /></Protected>} />
            <Route path="/bibliotecario/home" element={<Protected role="bibliotecario"><BibliotecarioDashboard /></Protected>} />
            {/*<Route path="/bibliotecario/home" element={<Protected role="bibliotecario"><BibliotecarioHome /></Protected>} />*/}
            <Route path="/cliente/home" element={<Protected role="cliente"><ClienteHome /></Protected>} />

            {/* placeholders */}
            <Route path="/admin/usuarios" element={<Protected role="admin"><Usuarios /></Protected>} />
            <Route path="/admin/registro-ficha" element={<Protected role="admin"><RegistroFicha /></Protected>} />
            <Route path="/admin/prestamos" element={<Protected role="admin"><Prestamos /></Protected>} />

            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    </div>
)
}
