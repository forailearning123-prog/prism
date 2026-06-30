import React, { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('prism_token')
    if (token) {
      api.defaults.headers.common['Authorization'] = 'Bearer ' + token
      api.get('/api/v1/auth/me')
        .then(res => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('prism_token')
          delete api.defaults.headers.common['Authorization']
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (email, password) => {
    const params = new URLSearchParams()
    params.append('username', email)
    params.append('password', password)
    const res = await api.post('/api/v1/auth/token', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    const { access_token } = res.data
    localStorage.setItem('prism_token', access_token)
    api.defaults.headers.common['Authorization'] = 'Bearer ' + access_token
    const meRes = await api.get('/api/v1/auth/me')
    setUser(meRes.data)
  }

  const register = async (data) => {
    await api.post('/api/v1/auth/register', data)
    await login(data.email, data.password)
  }

  const logout = () => {
    localStorage.removeItem('prism_token')
    delete api.defaults.headers.common['Authorization']
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
