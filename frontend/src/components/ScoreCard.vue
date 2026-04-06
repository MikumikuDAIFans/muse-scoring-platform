<template>
  <div class="scoring-page">
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
    </div>

    <div class="slides-viewport" ref="viewportRef">
      <div class="slides-track" :style="{ transform: `translateY(-${currentIndex * 100}%)`, transition: 'transform 0.5s cubic-bezier(0.4, 0, 0.2, 1)' }">
        
        <div class="slide" v-for="(img, idx) in images" :key="img.id" :data-index="idx">
          <div class="slide-inner">
            <div class="img-panel">
              <img :src="img.url" :alt="'Image ' + img.id" class="main-img" @error="onImgErr" />
            </div>
            <div class="rate-panel">
              <div class="rate-inner">
                <div class="badge">🐾 进度 {{ idx + 1 }} / {{ images.length }}</div>
                
                <div class="rate-section">
                  <h2 class="rate-title">1. 这张图片的<span class="text-pink bold"> 美学表现 </span>如何？✨</h2>
                  <div class="bubbles">
                    <div v-for="n in 10" :key="'a'+n" @click="setScore(img.id, 'aesthetic', n)" class="bubble" :class="{ on: scores[img.id]?.aesthetic === n }">{{ n }}</div>
                  </div>
                  <div class="labels"><span>辣眼睛 (ಥ﹏ಥ)</span><span>神仙画作！(✧ω✧)</span></div>
                </div>

                <div class="rate-section">
                  <h2 class="rate-title">2. 这张图片的<span class="text-pink2 bold"> 细节完成度 </span>如何？🖌️</h2>
                  <div class="bubbles">
                    <div v-for="n in 10" :key="'c'+n" @click="setScore(img.id, 'completeness', n)" class="bubble" :class="{ on: scores[img.id]?.completeness === n }">{{ n }}</div>
                  </div>
                  <div class="labels"><span>粗糙线稿 (´-ω-`)</span><span>细节拉满！(≧∇≦)/</span></div>
                </div>

                <div class="status-bar">
                  <div v-if="fullyRated(img.id)" class="ok-msg">❤️ 收到啦，自动前往下一张咻咻~</div>
                  <div v-else-if="halfRated(img.id)" class="hint-msg">再戳一下另一个分数就可以啦 👆</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>

    <div class="brand">🌱 Muse</div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import { useScoreStore } from '../stores/score'
import api from '../api'

const emit = defineEmits(['batch-complete', 'no-more-images', 'batch-loaded'])

const userStore = useUserStore()
const scoreStore = useScoreStore()
const images = ref([])
const currentIndex = ref(0)
const scores = reactive({})
const isLoading = ref(false)

onMounted(async () => {
  await loadBatch()
})

const progressPercent = computed(() => {
  if (!images.value.length) return 0
  return ((currentIndex.value + 1) / images.value.length) * 100
})

const fullyRated = (id) => { const s = scores[id]; return s && s.aesthetic > 0 && s.completeness > 0 }
const halfRated = (id) => { const s = scores[id]; return s && (s.aesthetic || s.completeness) }

const setScore = async (id, dim, val) => {
  if (!scores[id]) scores[id] = { aesthetic: null, completeness: null }
  scores[id][dim] = val
  if (fullyRated(id)) {
    await submitAndAdvance(id)
  }
}

const submitAndAdvance = async (id) => {
  try {
    await scoreStore.submitScore(id, scores[id].aesthetic, scores[id].completeness)
    if (currentIndex.value < images.value.length - 1) {
      await userStore.fetchStats()
      setTimeout(() => currentIndex.value++, 600)
    } else {
      setTimeout(async () => {
        await userStore.fetchStats()
        emit('batch-complete')
      }, 600)
    }
  } catch (e) {
    console.error('Score submit error:', e)
  }
}

const loadBatchFromParent = (batchImages) => {
  images.value = batchImages
  currentIndex.value = 0
  images.value.forEach(img => {
    scores[img.id] = { aesthetic: null, completeness: null }
  })
  // Preload all images
  images.value.forEach(img => {
    const imgEl = new Image()
    imgEl.src = img.url
  })
}

const loadBatch = async (turnstileToken = null) => {
  isLoading.value = true
  try {
    const payload = turnstileToken ? { turnstile_token: turnstileToken } : {}
    const res = await api.post('/images/batch', payload)
    images.value = res.images || []
    
    // 如果没有更多图片，通知父组件
    if (images.value.length === 0) {
      emit('no-more-images', res.message || '所有图片已完成标注')
      return
    }
    
    // 图片加载成功，通知父组件可以进入打分页面
    emit('batch-loaded', images.value.length)
    
    currentIndex.value = 0
    images.value.forEach(img => {
      scores[img.id] = { aesthetic: null, completeness: null }
    })
    // Preload all images in the batch
    images.value.forEach(img => {
      const imgEl = new Image()
      imgEl.src = img.url
    })
  } catch (e) {
    console.error('Batch load error:', e)
  } finally {
    isLoading.value = false
  }
}

const onImgErr = (e) => {
  e.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'%3E%3Crect fill='%23ffe4e6' width='200' height='200'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23ff758c' font-size='14'%3EImage%3C/text%3E%3C/svg%3E"
}

defineExpose({ loadBatch, loadBatchFromParent })
</script>

<style scoped>
.scoring-page {
  position: fixed;
  inset: 0;
  background: #fff5f8;
  overflow: hidden;
}

.progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 6px;
  background: #ffe4e6;
  z-index: 100;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff758c, #ff7eb3);
  transition: width 0.5s ease;
  border-radius: 0 4px 4px 0;
}

.slides-viewport {
  position: fixed;
  inset: 0;
  top: 6px;
  overflow: hidden;
}
.slides-track {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}
.slide {
  flex: 0 0 100%;
  width: 100%;
  height: 100%;
  min-height: 100%;
  overflow: hidden;
}
.slide-inner {
  display: flex;
  width: 100%;
  height: 100%;
}

.img-panel {
  flex: 1;
  height: 100%;
  background: #fff5f8;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
}
.main-img {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  display: block;
}

.rate-panel {
  flex: 1;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 30px 40px;
  overflow-y: auto;
}
.rate-inner {
  width: 100%;
  max-width: 580px;
}

.badge {
  display: inline-flex;
  align-items: center;
  color: #ff758c;
  font-size: 15px;
  font-weight: 800;
  background: #ffe4e6;
  padding: 6px 14px;
  border-radius: 20px;
  margin-bottom: 16px;
}
.rate-title {
  font-size: 20px;
  line-height: 1.4;
  font-weight: 700;
  margin-bottom: 20px;
  color: #5d4a4a;
}
.rate-section {
  margin-bottom: 36px;
  width: 100%;
}
.bubbles {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}
.bubble {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #ffe4e6;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  color: #ff758c;
  cursor: pointer;
  transition: all 0.2s;
  font-family: inherit;
  user-select: none;
}
.bubble:hover {
  border-color: #ff758c;
  transform: scale(1.1);
}
.bubble.on {
  background: linear-gradient(135deg, #ff758c, #ff7eb3);
  color: #fff;
  border-color: transparent;
  transform: scale(1.15);
  box-shadow: 0 4px 12px rgba(255,117,140,0.3);
}
.labels {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #8a7a7a;
  font-weight: 600;
}

.status-bar {
  margin-top: 24px;
  min-height: 24px;
}
.ok-msg {
  color: #ff758c;
  font-weight: 700;
  font-size: 15px;
}
.hint-msg {
  color: #8a7a7a;
  font-weight: 600;
  font-size: 14px;
}

.text-pink { color: #ff758c; }
.text-pink2 { color: #ff7eb3; }
.bold { font-weight: 800; }

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

@media (max-width: 768px) {
  .slide-inner {
    flex-direction: column;
  }
  .img-panel {
    flex: none;
    height: 40vh;
    width: 100%;
  }
  .rate-panel {
    flex: 1;
    width: 100%;
    padding: 20px;
  }
  .rate-inner {
    max-width: 100%;
  }
  .bubble {
    width: 34px;
    height: 34px;
    font-size: 12px;
  }
}
</style>
