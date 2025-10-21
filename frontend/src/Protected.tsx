import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth, Role } from './auth'

type Allowed = Role | Role[]

export default function Protected({ children, role }: { children: React.ReactNode; role?: Allowed }) {
  const { auth, loading, roleHome } = useAuth()
  const location = useLocation()

  if (loading) {
    return <div>Loading...</div>
  }

  if (!auth) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  if (role) {
    const allowed = Array.isArray(role) ? role : [role]
    if (!allowed.includes(auth.role)) {
      return <Navigate to={roleHome} replace />
    }
  }

  return <>{children}</>
}
