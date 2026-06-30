import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 15000,
})

const token = localStorage.getItem('prism_token')
if (token) {
  api.defaults.headers.common['Authorization'] = 'Bearer ' + token
}

export default api
