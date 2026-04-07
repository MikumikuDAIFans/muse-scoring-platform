<template>
  <div class="login-page">
    <div class="bg-blob-1"></div>
    <div class="bg-blob-2"></div>
    
    <div class="login-content">
      <div class="emoji-bounce">🎨</div>
      <h1 class="title">
        百万级图像数据集<br><span class="gradient-text">双维标注计划 ✨</span>
      </h1>
      <p class="subtitle">你的每一次打分，都在帮助 AI 变得更懂二次元！(๑>ᴗ<๑)</p>
      
      <div class="auth-card">
        <div class="auth-tabs">
          <button type="button" @click="activeTab = 'login'" :class="{ active: activeTab === 'login' }">登录</button>
          <button type="button" @click="activeTab = 'register'" :class="{ active: activeTab === 'register' }">注册</button>
        </div>
        
        <form @submit.prevent="handleSubmit" class="auth-form">
          <input 
            v-model="form.username" 
            placeholder="用户名 (3-20位字母/数字/下划线)" 
            class="cute-input" 
            autocomplete="username"
          />
          <input 
            v-model="form.password" 
            type="password" 
            placeholder="密码 (至少8位)" 
            class="cute-input" 
            autocomplete="current-password"
            @keyup.enter="handleSubmit" 
          />
          
          <button type="submit" class="tf-btn" :disabled="loading">
            <span v-if="loading">⏳ 处理中...</span>
            <span v-else>{{ activeTab === 'login' ? '登录' : '注册' }} 🚀</span>
          </button>
          
          <!-- Turnstile Widget (仅注册时显示) -->
          <div v-if="activeTab === 'register' && turnstileSiteKey" class="turnstile-wrapper">
            <div ref="turnstileWidget" class="cf-turnstile"></div>
          </div>
          
          <p v-if="error" class="error-text">{{ error }}</p>
        </form>
      </div>
    </div>
    
    <div class="brand">🌱 Muse</div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useUserStore } from '../stores/user'

const emit = defineEmits(['login-success'])
const userStore = useUserStore()

const activeTab = ref('login')
const form = reactive({ username: '', password: '' })
const loading = ref(false)
const error = ref('')
const turnstileWidget = ref(null)
let turnstileWidgetId = null

// Turnstile Site Key
const turnstileSiteKey = computed(() => {
  return import.meta.env.VITE_TURNSTILE_SITE_KEY || ''
})
const turnstileToken = ref('')

onMounted(() => {
  initTurnstile()
})

function initTurnstile() {
  if (!turnstileSiteKey.value) return
  if (window.turnstile) {
    renderTurnstile()
    return
  }

  const timer = window.setInterval(() => {
    if (window.turnstile) {
      window.clearInterval(timer)
      renderTurnstile()
    }
  }, 200)

  window.setTimeout(() => window.clearInterval(timer), 10000)
}

function renderTurnstile() {
  if (!window.turnstile || !turnstileWidget.value) return
  if (turnstileWidgetId) {
    window.turnstile.remove(turnstileWidgetId)
    turnstileWidgetId = null
  }
  turnstileWidgetId = window.turnstile.render(turnstileWidget.value, {
    sitekey: turnstileSiteKey.value,
    theme: 'light',
    size: 'normal',
    callback: (token) => { turnstileToken.value = token },
  })
}

async function handleSubmit() {
  if (!form.username || !form.password) {
    error.value = '请填写用户名和密码'
    return
  }
  
  // 注册时需要 Turnstile token
  if (activeTab.value === 'register' && turnstileSiteKey.value && !turnstileToken.value) {
    error.value = '请先完成人机验证'
    return
  }
  
  loading.value = true
  error.value = ''
  try {
    const payload = { ...form }
    if (activeTab.value === 'register') {
      payload.turnstile_token = turnstileToken.value
    }
    
    if (activeTab.value === 'login') {
      await userStore.login(form)
    } else {
      await userStore.register(payload)
    }
    emit('login-success')
  } catch (err) {
    error.value = err.detail || '操作失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

watch(activeTab, async (tab) => {
  if (tab !== 'register' || !turnstileSiteKey.value) return
  await nextTick()
  initTurnstile()
})

onUnmounted(() => {
  if (turnstileWidgetId && window.turnstile) {
    window.turnstile.remove(turnstileWidgetId)
  }
})
</script>

<style scoped>
.login-page {
  position: fixed;
  inset: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #fff5f8;
  overflow: hidden;
}

.bg-blob-1, .bg-blob-2 {
  position: fixed;
  border-radius: 50%;
  pointer-events: none;
  z-index: 0;
}
.bg-blob-1 {
  top: -100px;
  right: -100px;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(255,154,162,0.3), transparent 70%);
}
.bg-blob-2 {
  bottom: -150px;
  left: -150px;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(255,126,179,0.2), transparent 70%);
}

.login-content {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 40px 20px;
  max-width: 500px;
  width: 100%;
}

.emoji-bounce {
  font-size: 3rem;
  display: inline-block;
  margin-bottom: 1rem;
  animation: bounce 1s infinite;
}
@keyframes bounce {
  0%, 100% { transform: translateY(-25%); }
  50% { transform: translateY(0); }
}

.title {
  font-size: 2.25rem;
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 1.5rem;
  color: #5d4a4a;
}
.gradient-text {
  background: linear-gradient(135deg, #ff758c, #ff7eb3);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.subtitle {
  font-size: 1.125rem;
  color: #8a7a7a;
  margin-bottom: 2.5rem;
  line-height: 1.6;
  font-weight: 600;
}

.auth-card {
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(255,117,140,0.15);
  padding: 32px;
  max-width: 400px;
  margin: 0 auto;
}
.auth-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 24px;
}
.auth-tabs button {
  flex: 1;
  padding: 10px;
  border: none;
  background: #ffe4e6;
  color: #ff758c;
  font-weight: 700;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 16px;
  font-family: inherit;
}
.auth-tabs button.active {
  background: linear-gradient(135deg, #ff758c, #ff7eb3);
  color: #fff;
}
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.cute-input {
  padding: 12px 16px;
  border: 2px solid #ffe4e6;
  border-radius: 12px;
  font-size: 15px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.3s;
  background: #fff;
}
.cute-input:focus {
  border-color: #ff758c;
}
.tf-btn {
  padding: 14px 32px;
  border: none;
  background: linear-gradient(135deg, #ff758c, #ff7eb3);
  color: #fff;
  font-size: 18px;
  font-weight: 700;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s;
  font-family: inherit;
  box-shadow: 0 4px 16px rgba(255,117,140,0.3);
}
.tf-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(255,117,140,0.4);
}
.tf-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.error-text {
  color: #f44336;
  text-align: center;
  margin-top: 8px;
  font-size: 14px;
}

.turnstile-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}
.cf-turnstile {
  min-height: 65px;
}

.brand {
  position: fixed;
  bottom: 16px;
  right: 16px;
  background: #fff;
  border-radius: 20px;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 700;
  color: #ff758c;
  box-shadow: 0 2px 12px rgba(255,117,140,0.15);
  z-index: 50;
}
</style>
