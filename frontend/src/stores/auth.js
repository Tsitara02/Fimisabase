import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'
import router from '@/router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const token = ref(localStorage.getItem('access_token') || null)
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email, password) {
    loading.value = true
    error.value = null
    try {
      const { data } = await api.post('/auth/login', { email, password })
      token.value = data.access_token
      user.value = data.user
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      router.push('/dashboard')
    } catch (e) {
      error.value = e.response?.data?.error || 'Erreur de connexion'
    } finally {
      loading.value = false
    }
  }

  async function signup(email, password) {
    loading.value = true
    error.value = null
    try {
      await api.post('/auth/signup', { email, password })
      router.push('/login?registered=1')
    } catch (e) {
      error.value = e.response?.data?.error || 'Erreur lors de la création'
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch (_) {}
    token.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  async function fetchMe() {
    try {
      const { data } = await api.get('/auth/me')
      user.value = data
    } catch (_) {
      logout()
    }
  }

  return { user, token, loading, error, isAuthenticated, login, signup, logout, fetchMe }
})
