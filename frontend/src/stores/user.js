import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import api from '../api'

function parseJwtRole(token) {
  try {
    const parts = token.split('.')
    const payload = JSON.parse(atob(parts[1]))
    return payload.role || 'user'
  } catch {
    return 'user'
  }
}

function isValidToken(token) {
  try {
    const parts = token.split('.')
    const payload = JSON.parse(atob(parts[1]))
    return !!payload.role && !!payload.exp && payload.exp > Math.floor(Date.now() / 1000)
  } catch {
    return false
  }
}

export const useUserStore = defineStore('user', () => {
  const rawToken = localStorage.getItem('token') || ''
  const token = ref(isValidToken(rawToken) ? rawToken : '')
  const username = ref('')
  const role = ref(parseJwtRole(token.value))
  const isLoggedIn = ref(!!token.value)
  const stats = reactive({ total_scores: 0, today_scores: 0 })

  async function login(credentials) {
    const res = await api.post('/auth/login', credentials)
    token.value = res.token
    role.value = parseJwtRole(res.token)
    localStorage.setItem('token', res.token)
    isLoggedIn.value = true
    await fetchStats()
  }

  async function register(credentials) {
    const res = await api.post('/auth/register', credentials)
    token.value = res.token
    role.value = parseJwtRole(res.token)
    localStorage.setItem('token', res.token)
    isLoggedIn.value = true
    await fetchStats()
  }

  function loadToken() {
    const t = localStorage.getItem('token')
    if (t && isValidToken(t)) {
      token.value = t
      role.value = parseJwtRole(t)
      isLoggedIn.value = true
      fetchStats()
    }
  }

  function logout() {
    token.value = ''
    username.value = ''
    role.value = 'user'
    isLoggedIn.value = false
    stats.total_scores = 0
    stats.today_scores = 0
    localStorage.removeItem('token')
  }

  async function fetchStats() {
    try {
      const res = await api.get('/my-stats')
      stats.total_scores = res.total_scores
      stats.today_scores = res.today_scores
      username.value = res.username
    } catch {
      // stats fetch failed silently
    }
  }

  return { token, username, role, isLoggedIn, stats, login, register, logout, loadToken, fetchStats }
})
