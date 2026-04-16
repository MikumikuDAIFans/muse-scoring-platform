<template>
  <Transition name="fade" mode="out-in">
    <LoginPage v-if="currentPage === 'login'" @login-success="onLoginSuccess" />

    <AdminDashboard v-else-if="currentPage === 'admin'" @logout="doLogout" key="admin" />

    <div v-else-if="currentPage === 'welcome'" class="welcome-overlay" key="welcome">
      <div class="welcome-content text-center">
        <div class="emoji-bounce">🎯</div>
        <h1 class="title-welcome">欢迎来到打分环节</h1>
        <p class="subtitle">
          Hello, <span class="text-pink">{{ userStore.username }}</span><br>
          已打 <span class="text-pink">{{ userStore.stats.total_scores }}</span> 次分，今天
          <span class="text-pink">{{ userStore.stats.today_scores }}</span> 次
        </p>
        <p class="hint-text">每次只展示 1 张图，后台最多预取 1 张下一张，提交后会立即切换。</p>

        <div class="turnstile-container" v-if="turnstileSiteKey">
          <div ref="turnstileWidget" class="cf-turnstile"></div>
        </div>
        <p v-if="turnstileSiteKey && !turnstileReady" class="hint-text turnstile-hint">
          请先完成人机验证，再开始打分
        </p>

        <button @click="startScoring" class="tf-btn" :disabled="isLoading">
          <span v-if="isLoading">正在准备图片...</span>
          <span v-else>开始打分</span>
        </button>

        <div class="logout-area">
          <button @click="doLogout" class="logout-btn">退出登录</button>
        </div>
      </div>
    </div>

    <ScoreCard
      v-else-if="currentPage === 'scoring'"
      @no-more-images="onNoMoreImages"
      key="scoring"
    />

    <div v-else-if="currentPage === 'all-done'" class="done-overlay" key="all-done">
      <div class="done-content text-center">
        <div class="gift-icon">🏆</div>
        <h1 class="title-done">所有图片都已完成标注</h1>
        <p class="subtitle">{{ noMoreMsg || '感谢你的辛勤付出，数据集标注已经全部完成。' }}</p>
        <div class="done-actions">
          <button @click="goWelcome" class="rest-btn">返回首页</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useUserStore } from './stores/user'
import { useScoreStore } from './stores/score'
import LoginPage from './components/LoginPage.vue'
import ScoreCard from './components/ScoreCard.vue'
import AdminDashboard from './components/AdminDashboard.vue'

const userStore = useUserStore()
const scoreStore = useScoreStore()

const currentPage = ref('login')
const isLoading = ref(false)
const turnstileToken = ref('')
const turnstileReady = ref(true)
const turnstileWidget = ref(null)
const noMoreMsg = ref('')

let turnstileWidgetId = null
let turnstileInitTimer = null
let statsRefreshTimer = null

const turnstileSiteKey = computed(() => import.meta.env.VITE_TURNSTILE_SITE_KEY || '')

onMounted(() => {
  userStore.loadToken()
  if (userStore.isLoggedIn) {
    currentPage.value = userStore.role === 'admin' ? 'admin' : 'welcome'
  }
  startStatsSync()
  initTurnstile()
})

function startStatsSync() {
  if (statsRefreshTimer) window.clearInterval(statsRefreshTimer)
  statsRefreshTimer = window.setInterval(() => {
    if (userStore.isLoggedIn && userStore.role !== 'admin') {
      userStore.fetchStats()
    }
  }, 60000)
}

function initTurnstile() {
  if (!turnstileSiteKey.value || currentPage.value !== 'welcome') {
    turnstileReady.value = true
    return
  }

  turnstileReady.value = false

  if (turnstileInitTimer) {
    window.clearTimeout(turnstileInitTimer)
    turnstileInitTimer = null
  }

  if (window.turnstile) {
    turnstileInitTimer = window.setTimeout(() => renderTurnstile(), 150)
    return
  }

  const existingScript = document.querySelector('script[src="https://challenges.cloudflare.com/turnstile/v0/api.js"]')
  if (!existingScript) {
    const script = document.createElement('script')
    script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js'
    script.async = true
    script.defer = true
    script.onload = () => renderTurnstile()
    document.head.appendChild(script)
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
  if (!window.turnstile || !turnstileWidget.value || currentPage.value !== 'welcome') return

  if (turnstileWidget.value.querySelector('iframe')) return

  if (turnstileWidgetId) {
    window.turnstile.remove(turnstileWidgetId)
    turnstileWidgetId = null
  }

  turnstileWidgetId = window.turnstile.render(turnstileWidget.value, {
    sitekey: turnstileSiteKey.value,
    theme: 'light',
    size: 'normal',
    callback: (token) => {
      turnstileToken.value = token
      turnstileReady.value = true
    },
    'expired-callback': () => {
      turnstileToken.value = ''
      turnstileReady.value = false
    },
    'error-callback': () => {
      turnstileToken.value = ''
      turnstileReady.value = false
    },
  })
}

async function onLoginSuccess() {
  currentPage.value = userStore.role === 'admin' ? 'admin' : 'welcome'
  if (currentPage.value === 'welcome') {
    await nextTick()
    initTurnstile()
  }
}

async function startScoring() {
  if (turnstileSiteKey.value && (!turnstileReady.value || !turnstileToken.value)) {
    return
  }

  isLoading.value = true
  scoreStore.clearTasks()

  const token = turnstileToken.value
  if (turnstileWidgetId && window.turnstile) {
    window.turnstile.reset(turnstileWidgetId)
  }
  turnstileToken.value = ''

  try {
    const task = await scoreStore.startSession(token)
    if (!task) {
      noMoreMsg.value = scoreStore.message || '所有图片都已完成标注'
      currentPage.value = 'all-done'
      return
    }
    currentPage.value = 'scoring'
  } finally {
    isLoading.value = false
  }
}

function onNoMoreImages(message) {
  noMoreMsg.value = message
  currentPage.value = 'all-done'
}

function goWelcome() {
  currentPage.value = 'welcome'
  scoreStore.clearTasks()
  turnstileToken.value = ''
  if (turnstileWidgetId && window.turnstile) {
    window.turnstile.remove(turnstileWidgetId)
    turnstileWidgetId = null
  }
  turnstileReady.value = !turnstileSiteKey.value
}

function doLogout() {
  scoreStore.clearTasks()
  userStore.logout()
  currentPage.value = 'login'
  turnstileToken.value = ''
  turnstileReady.value = true
}

watch(currentPage, async (page) => {
  if (page !== 'welcome' || !turnstileSiteKey.value) return
  turnstileToken.value = ''
  turnstileReady.value = false
  await nextTick()
  initTurnstile()
})

watch(turnstileWidget, async (widgetEl) => {
  if (!widgetEl || currentPage.value !== 'welcome' || !turnstileSiteKey.value) return
  if (!turnstileWidgetId) {
    await nextTick()
    initTurnstile()
  }
})

onUnmounted(() => {
  if (turnstileInitTimer) window.clearTimeout(turnstileInitTimer)
  if (statsRefreshTimer) window.clearInterval(statsRefreshTimer)
  if (turnstileWidgetId && window.turnstile) {
    window.turnstile.remove(turnstileWidgetId)
  }
})
</script>

<style>
*,*::before,*::after{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%;height:100%;margin:0;padding:0;overflow:hidden}
body{font-family:'Nunito','PingFang SC','Microsoft YaHei',sans-serif;background:#fff5f8;color:#5d4a4a;-webkit-font-smoothing:antialiased}

.fade-enter-active,.fade-leave-active{transition:opacity .4s ease}
.fade-enter-from,.fade-leave-to{opacity:0}

.welcome-overlay{position:fixed;inset:0;display:flex;justify-content:center;align-items:center;background:#fff5f8;z-index:200}
.welcome-content{padding:40px 20px;max-width:600px;width:100%}
.text-center{text-align:center}
.emoji-bounce{font-size:3rem;display:inline-block;margin-bottom:1rem;animation:bounce 1s infinite}
@keyframes bounce{0%,100%{transform:translateY(-25%)}50%{transform:translateY(0)}}
.title-welcome{font-size:1.875rem;font-weight:800;margin-bottom:1.5rem;color:#5d4a4a}
.subtitle{font-size:1.125rem;color:#8a7a7a;margin-bottom:2.5rem;line-height:1.6;font-weight:600}
.hint-text{font-size:1rem;color:#8a7a7a;margin-bottom:2.5rem;line-height:1.6;font-weight:600;max-width:32rem;margin-left:auto;margin-right:auto}
.text-pink{color:#ff758c}
.tf-btn{padding:14px 32px;border:none;background:linear-gradient(135deg,#ff758c,#ff7eb3);color:#fff;font-size:18px;font-weight:700;border-radius:16px;cursor:pointer;transition:all .3s;font-family:inherit;box-shadow:0 4px 16px rgba(255,117,140,.3)}
.tf-btn:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 6px 24px rgba(255,117,140,.4)}
.tf-btn:disabled{opacity:.6;cursor:not-allowed}
.logout-btn{padding:10px 20px;border:none;background:transparent;color:#8a7a7a;font-size:14px;cursor:pointer;font-family:inherit}
.logout-btn:hover{color:#ff758c}
.logout-area{margin-top:2rem;display:flex;justify-content:center}

.done-overlay{position:fixed;inset:0;display:flex;justify-content:center;align-items:center;background:#fff5f8;z-index:200}
.done-content{padding:40px 20px;max-width:600px;width:100%}
.gift-icon{font-size:3rem;margin-bottom:1rem}
.title-done{font-size:2.25rem;font-weight:800;margin-bottom:1rem;color:#5d4a4a}
.done-actions{display:flex;flex-direction:column;gap:1rem;justify-content:center;align-items:center}
@media(min-width:640px){.done-actions{flex-direction:row}}
.rest-btn{padding:12px 24px;border:2px solid #ffe4e6;background:#fff;color:#ff758c;font-size:16px;font-weight:700;border-radius:14px;cursor:pointer;transition:all .3s;font-family:inherit}

.turnstile-container {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
  min-height: 65px;
}
.turnstile-container :deep(.cf-turnstile) {
  transform-origin: center center;
}
.turnstile-hint {
  margin-top: -0.5rem;
  margin-bottom: 1rem;
  color: #ff758c;
}
</style>
