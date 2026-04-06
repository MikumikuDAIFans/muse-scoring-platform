import axios from 'axios'

// 生产环境可通过 VITE_API_BASE_URL 环境变量配置后端 API 地址
// Cloudflare Pages 部署时，若前后端分离部署则需填写完整后端 URL
// 若使用 Cloudflare Tunnel 或同域部署，留空即可（使用相对路径 /api）
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 10000,
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  res => res.data,
  err => Promise.reject(err.response?.data || err)
)

export default api
