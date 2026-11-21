import React, { createContext, useContext, useState, useEffect } from 'react'
import { API_BASE } from '../config/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('scope_guard_token'))
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('scope_guard_user')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })
  const [workspace, setWorkspace] = useState(() => {
    try {
      const saved = localStorage.getItem('scope_guard_workspace')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })
  const [loading, setLoading] = useState(true)

  // Verify session on mount with /auth/me
  useEffect(() => {
    const verifySession = async () => {
      const storedToken = localStorage.getItem('scope_guard_token')
      if (!storedToken) {
        setLoading(false)
        return
      }

      try {
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${storedToken}` },
        })

        if (res.ok) {
          const data = await res.json()
          setUser(data.user)
          setWorkspace(data.workspace)
          localStorage.setItem('scope_guard_user', JSON.stringify(data.user))
          localStorage.setItem('scope_guard_workspace', JSON.stringify(data.workspace))
        } else {
          // Token expired or invalid
          logout()
        }
      } catch (err) {
        console.warn('Backend unavailable during session restoration:', err)
        // Keep cached state if offline or network error
      } finally {
        setLoading(false)
      }
    }

    verifySession()
  }, [])

  const login = async (email, password) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.trim(), password }),
    })

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      throw new Error(errData.detail || 'Login failed. Invalid credentials.')
    }

    const tokenData = await res.json()
    const accessToken = tokenData.access_token

    // Fetch user profile and workspace
    const meRes = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })

    if (!meRes.ok) {
      throw new Error('Failed to retrieve user workspace profile.')
    }

    const meData = await meRes.json()

    // Store in localStorage
    localStorage.setItem('scope_guard_token', accessToken)
    localStorage.setItem('scope_guard_user', JSON.stringify(meData.user))
    localStorage.setItem('scope_guard_workspace', JSON.stringify(meData.workspace))

    setToken(accessToken)
    setUser(meData.user)
    setWorkspace(meData.workspace)

    return { user: meData.user, workspace: meData.workspace }
  }

  const signup = async ({ agencyName, userName, email, password }) => {
    const res = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        agency_name: agencyName.trim(),
        full_name: userName.trim(),
        email: email.trim(),
        password,
      }),
    })

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}))
      throw new Error(errData.detail || 'Signup failed. Please check your inputs.')
    }

    const data = await res.json()
    const accessToken = data.access_token

    localStorage.setItem('scope_guard_token', accessToken)
    localStorage.setItem('scope_guard_user', JSON.stringify(data.user))
    localStorage.setItem('scope_guard_workspace', JSON.stringify(data.workspace))

    setToken(accessToken)
    setUser(data.user)
    setWorkspace(data.workspace)

    return data
  }

  const logout = () => {
    localStorage.removeItem('scope_guard_token')
    localStorage.removeItem('scope_guard_user')
    localStorage.removeItem('scope_guard_workspace')
    setToken(null)
    setUser(null)
    setWorkspace(null)
  }

  // Wrapper for authenticated fetch that injects token and handles 401
  const authFetch = async (endpoint, options = {}) => {
    const currentToken = token || localStorage.getItem('scope_guard_token')
    const headers = {
      ...options.headers,
      ...(currentToken ? { Authorization: `Bearer ${currentToken}` } : {}),
    }

    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`
    const res = await fetch(url, { ...options, headers })

    if (res.status === 401) {
      logout()
    }

    return res
  }

  const value = {
    token,
    user,
    workspace,
    isAuthenticated: Boolean(token && user),
    loading,
    login,
    signup,
    logout,
    authFetch,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
