<template>
  <div class="scoring-page">
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
    </div>

    <div class="task-shell" v-if="task">
      <div class="task-inner">
        <div class="img-panel">
          <img :src="task.image_url" :alt="'Image ' + task.image_id" class="main-img" @error="onImgErr" />
        </div>

        <div class="rate-panel">
          <div class="rate-inner">
            <div class="badge">当前任务 #{{ task.task_id }}</div>

            <div class="rate-section">
              <h2 class="rate-title">1. 这张图片的 <span class="text-pink bold">美学表现</span> 如何？</h2>
              <div class="bubbles">
                <div
                  v-for="n in 10"
                  :key="'a' + n"
                  class="bubble"
                  :class="{ on: score.aesthetic === n }"
                  @click="setScore('aesthetic', n)"
                >
                  {{ n }}
                </div>
              </div>
              <div class="labels"><span>辣眼睛</span><span>神仙画作</span></div>
            </div>

            <div class="rate-section">
              <h2 class="rate-title">2. 这张图片的 <span class="text-pink2 bold">细节完成度</span> 如何？</h2>
              <div class="bubbles">
                <div
                  v-for="n in 10"
                  :key="'c' + n"
                  class="bubble"
                  :class="{ on: score.completeness === n }"
                  @click="setScore('completeness', n)"
                >
                  {{ n }}
                </div>
              </div>
              <div class="labels"><span>粗糙线稿</span><span>细节拉满</span></div>
            </div>

            <div class="status-bar">
              <div v-if="isSubmitting" class="ok-msg">提交中，马上切到下一张...</div>
              <div v-else-if="fullyRated" class="ok-msg">收到啦，准备前往下一张</div>
              <div v-else-if="halfRated" class="hint-msg">再选另一个维度的分数就可以提交</div>
              <div v-else-if="scoreStore.prefetching" class="hint-msg">后台正在准备下一张图片</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="brand">Muse</div>
  </div>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { useUserStore } from '../stores/user'
import { useScoreStore } from '../stores/score'

const emit = defineEmits(['no-more-images'])

const userStore = useUserStore()
const scoreStore = useScoreStore()
const score = reactive({ aesthetic: null, completeness: null })

const task = computed(() => scoreStore.currentTask)
const fullyRated = computed(() => score.aesthetic > 0 && score.completeness > 0)
const halfRated = computed(() => !!(score.aesthetic || score.completeness))
const isSubmitting = computed(() => scoreStore.submitting)
const progressPercent = computed(() => (scoreStore.nextTask ? 100 : 55))

function resetScoreState() {
  score.aesthetic = null
  score.completeness = null
}

async function ensureNextTask() {
  if (!task.value) return
  const nextTask = await scoreStore.prefetchNextTask()
  if (!nextTask && !scoreStore.message && !scoreStore.prefetching) {
    // No-op: the current task can still be completed.
  }
}

async function setScore(field, value) {
  if (!task.value || scoreStore.submitting) return
  score[field] = value
  if (fullyRated.value) {
    await submitAndAdvance()
  }
}

async function submitAndAdvance() {
  if (!task.value) return
  const ok = await scoreStore.submitTaskScore({
    taskId: task.value.task_id,
    imageId: task.value.image_id,
    aesthetic: score.aesthetic,
    completeness: score.completeness,
  })
  if (!ok) return

  userStore.incrementStats()

  const nextTask = scoreStore.promoteNextTask()
  if (nextTask) {
    resetScoreState()
    await ensureNextTask()
    return
  }

  const fallbackTask = await scoreStore.fetchNextTask()
  if (!fallbackTask) {
    scoreStore.clearTasks()
    emit('no-more-images', scoreStore.message || '所有图片都已完成标注')
    return
  }

  scoreStore.currentTask = fallbackTask
  resetScoreState()
  await ensureNextTask()
}

function onImgErr(event) {
  event.target.src = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'%3E%3Crect fill='%23ffe4e6' width='200' height='200'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23ff758c' font-size='14'%3EImage%3C/text%3E%3C/svg%3E"
}

watch(
  task,
  async (nextTask) => {
    resetScoreState()
    if (!nextTask) return
    await ensureNextTask()
  },
  { immediate: true }
)
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
  transition: width 0.4s ease;
  border-radius: 0 4px 4px 0;
}

.task-shell {
  position: fixed;
  inset: 6px 0 0;
}

.task-inner {
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
  box-shadow: 0 4px 12px rgba(255, 117, 140, 0.3);
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
  box-shadow: 0 2px 12px rgba(255, 117, 140, 0.15);
  z-index: 50;
}

@media (max-width: 768px) {
  .task-inner {
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
