import axios from 'axios'

// On s'assure d'inclure le sous-dossier /api à la racine des requêtes
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL 
    ? `${import.meta.env.VITE_API_BASE_URL}/api` 
    : 'http://localhost:5000/api',
  headers: { 'Content-Type': 'application/json' },
})

// Inject token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Handle 401 globally
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api