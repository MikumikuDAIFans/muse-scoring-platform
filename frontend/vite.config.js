import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const isDev = mode === 'development'
  return {
    plugins: [vue()],
    server: {
      port: 5173,
      proxy: isDev ? { '/api': 'http://localhost:8000' } : undefined
    },
    define: {
      // 注入 Turnstile Site Key 到前端（公开信息，可安全暴露）
      'import.meta.env.VITE_TURNSTILE_SITE_KEY': JSON.stringify(process.env.VITE_TURNSTILE_SITE_KEY || ''),
      // 注入 API 基础 URL（生产环境通过环境变量覆盖）
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify(process.env.VITE_API_BASE_URL || '')
    }
  }
})
