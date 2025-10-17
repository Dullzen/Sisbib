import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

export type Role = 'admin' | 'bibliotecario' | 'cliente'

export interface UserInfo {
  user_id: number
  email: string
  nombre?: string | null
  apellido1?: string | null
  apellido2?: string | null
}

export interface AuthState {
  role: Role
  user: UserInfo
}

interface AuthContextValue {
  auth: AuthState | null
  login: (next: AuthState) => void
  logout: () => void
  roleHome: string
  displayName: string | null
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const STORAGE_KEY = 'sisbib.auth'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [auth, setAuth] = useState<AuthState | null>(null)

  // hydrate from storage once
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) setAuth(JSON.parse(raw))
    } catch {}
  }, [])

  // persist
  useEffect(() => {
    if (auth) localStorage.setItem(STORAGE_KEY, JSON.stringify(auth))
    else localStorage.removeItem(STORAGE_KEY)
  }, [auth])

  const login = (next: AuthState) => setAuth(next)
  const logout = () => setAuth(null)

  const roleHome = useMemo(() => {
    if (!auth) return '/'
    switch (auth.role) {
      case 'admin': return '/admin/dashboard'
      case 'bibliotecario': return '/bibliotecario/home'
      default: return '/cliente/home'
    }
  }, [auth])

  const displayName = useMemo(() => {
    if (!auth) return null
    const { nombre, apellido1 } = auth.user
    if (nombre && apellido1) return `${nombre} ${apellido1}`
    if (nombre) return nombre
    return auth.user.email
  }, [auth])

  const value = useMemo(() => ({ auth, login, logout, roleHome, displayName }), [auth, roleHome, displayName])

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
