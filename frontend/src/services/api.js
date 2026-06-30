import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 15000,
})

// Attach token on every request so refreshed tokens are always picked up
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('prism_token')
  if (token) {
    config.headers['Authorization'] = 'Bearer ' + token
  }
  return config
})

// Centralized error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('prism_token')
      window.location.href = '/login'
    }
    const message = error.response?.data?.detail || error.response?.data?.error || error.message || 'An unexpected error occurred'
    return Promise.reject(new Error(message))
  }
)

export default api
