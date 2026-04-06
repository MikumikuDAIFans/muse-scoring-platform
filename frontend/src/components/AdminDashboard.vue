<template>
  <div class="admin-page">
    <div class="bg-blob-1"></div>
    
    <div class="admin-header">
      <div class="header-left">
        <span class="header-emoji">🎨</span>
        <h1 class="header-title">Muse 管理面板</h1>
      </div>
      <button @click="onLogout" class="logout-btn">退出登录</button>
    </div>

    <div class="admin-body" v-if="!loading">
      <!-- 标注进度 -->
      <div class="card progress-card">
        <div class="card-header">
          <span class="card-icon">📊</span>
          <span class="card-label">标注进度</span>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar-bg">
            <div class="progress-bar-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <div class="progress-text">
            <span class="progress-number">{{ formatNum(stats.annotated_images) }}</span>
            <span class="progress-total">/ {{ formatNum(stats.total_images) }}</span>
            <span class="progress-percent">({{ progressPercent.toFixed(1) }}%)</span>
          </div>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-icon">👥</div>
          <div class="stat-value">{{ formatNum(stats.total_users) }}</div>
          <div class="stat-label">注册用户</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">📝</div>
          <div class="stat-value">{{ formatNum(stats.today_scores) }}</div>
          <div class="stat-label">今日打分</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">🔴</div>
          <div class="stat-value">{{ formatNum(stats.qps) }}</div>
          <div class="stat-label">QPS</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">📦</div>
          <div class="stat-value">{{ formatNum(stats.redis_queue) }}</div>
          <div class="stat-label">Redis 待落库</div>
        </div>
      </div>

      <!-- 用户排行 -->
      <div class="card leaderboard-card">
        <div class="card-header">
          <span class="card-icon">🏆</span>
          <span class="card-label">用户打分排行 Top 10</span>
        </div>
        <table class="leaderboard-table">
          <thead>
            <tr>
              <th>排名</th>
              <th>用户名</th>
              <th>总打分</th>
              <th>今日打分</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(u, i) in topUsers" :key="u.username">
              <td class="rank-cell">
                <span v-if="i === 0">🥇</span>
                <span v-else-if="i === 1">🥈</span>
                <span v-else-if="i === 2">🥉</span>
                <span v-else>{{ i + 1 }}</span>
              </td>
              <td class="username-cell">{{ u.username }}</td>
              <td class="score-cell">{{ formatNum(u.total_scores) }}</td>
              <td class="today-cell">{{ formatNum(u.today_scores) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="admin-loading" v-else>
      <div class="spinner">⏳</div>
      <p>加载中...</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '../stores/user'
import api from '../api'

const emit = defineEmits(['logout'])

const userStore = useUserStore()
const loading = ref(true)
const stats = ref({
  total_images: 0,
  annotated_images: 0,
  total_scores: 0,
  total_users: 0,
  today_scores: 0,
  qps: 0,
  redis_queue: 0
})
const topUsers = ref([])
let refreshTimer = null

const progressPercent = computed(() => {
  if (!stats.value.total_images) return 0
  const pct = (stats.value.annotated_images / stats.value.total_images) * 100
  return Math.min(pct, 100)
})

function formatNum(n) {
  if (n == null) return '0'
  return Number(n).toLocaleString()
}

async function fetchAdminStats() {
  try {
    const res = await api.get('/admin/stats')
    stats.value = res
  } catch (e) {
    console.error('Failed to fetch admin stats:', e)
  }
}

async function fetchTopUsers() {
  try {
    const res = await api.get('/admin/users?page=1&page_size=10')
    topUsers.value = res.users || []
  } catch (e) {
    console.error('Failed to fetch top users:', e)
  }
}

async function refreshAll() {
  await Promise.all([fetchAdminStats(), fetchTopUsers()])
  loading.value = false
}

onMounted(() => {
  refreshAll()
  refreshTimer = setInterval(refreshAll, 10000) // 每10秒刷新
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})

function onLogout() {
  emit('logout')
}
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  max-height: 100vh;
  background: #fff5f8;
  padding: 20px;
  position: relative;
  overflow-x: hidden;
  overflow-y: auto;
}

.bg-blob-1 {
  position: fixed;
  width: 400px;
  height: 400px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255,117,140,0.12) 0%, transparent 70%);
  top: -100px;
  right: -100px;
  pointer-events: none;
  z-index: 0;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1100px;
  margin: 0 auto 24px;
  position: relative;
  z-index: 1;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-emoji {
  font-size: 2rem;
}

.header-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: #5d4a4a;
}

.logout-btn {
  padding: 8px 20px;
  border: 2px solid #ffe4e6;
  background: #fff;
  color: #ff758c;
  font-size: 14px;
  font-weight: 700;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.3s;
  font-family: inherit;
}

.logout-btn:hover {
  background: #ff758c;
  color: #fff;
  border-color: #ff758c;
}

.admin-body {
  max-width: 1100px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.card {
  background: #fff;
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(255,117,140,0.1);
  border: 1px solid #ffe4e6;
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.card-icon {
  font-size: 1.4rem;
}

.card-label {
  font-size: 1.1rem;
  font-weight: 700;
  color: #5d4a4a;
}

.progress-bar-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-bar-bg {
  height: 24px;
  background: #ffe4e6;
  border-radius: 12px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff758c, #ff7eb3);
  border-radius: 12px;
  transition: width 0.6s ease;
}

.progress-text {
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-weight: 700;
}

.progress-number {
  font-size: 1.2rem;
  color: #ff758c;
}

.progress-total, .progress-percent {
  font-size: 0.9rem;
  color: #a08a8a;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

@media (min-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(4, 1fr);
  }
}

.stat-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 4px 16px rgba(255,117,140,0.08);
  border: 1px solid #ffe4e6;
}

.stat-icon {
  font-size: 1.5rem;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 800;
  color: #5d4a4a;
}

.stat-label {
  font-size: 0.85rem;
  color: #a08a8a;
  font-weight: 600;
  margin-top: 4px;
}

.leaderboard-table {
  width: 100%;
  border-collapse: collapse;
}

.leaderboard-table th {
  text-align: left;
  padding: 10px 12px;
  font-size: 0.85rem;
  color: #a08a8a;
  font-weight: 700;
  border-bottom: 2px solid #ffe4e6;
}

.leaderboard-table td {
  padding: 12px;
  font-size: 0.95rem;
  color: #5d4a4a;
  border-bottom: 1px solid #fff0f5;
}

.rank-cell {
  font-weight: 700;
  width: 60px;
}

.username-cell {
  font-weight: 600;
}

.score-cell, .today-cell {
  font-weight: 700;
  color: #ff758c;
  text-align: right;
}

.admin-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  gap: 16px;
}

.spinner {
  font-size: 2.5rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.admin-loading p {
  font-size: 1.1rem;
  color: #a08a8a;
  font-weight: 600;
}
</style>
