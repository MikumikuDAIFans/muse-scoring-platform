import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import api from '../api'

const ROUND_SIZE = 10

function preloadImage(url) {
  if (!url) return
  const img = new Image()
  img.src = url
}

export const useScoreStore = defineStore('score', () => {
  const currentTask = ref(null)
  const nextTask = ref(null)
  const loading = ref(false)
  const prefetching = ref(false)
  const submitting = ref(false)
  const message = ref('')
  const assignedCount = ref(0)
  const completedCount = ref(0)

  const progressPercent = computed(() => {
    if (!currentTask.value && completedCount.value === 0) return 0
    return Math.min(((completedCount.value + (currentTask.value ? 1 : 0)) / ROUND_SIZE) * 100, 100)
  })

  const roundAssignedFull = computed(() => assignedCount.value >= ROUND_SIZE)
  const roundCompleted = computed(() => completedCount.value >= ROUND_SIZE)

  function clearTasks() {
    currentTask.value = null
    nextTask.value = null
    message.value = ''
    assignedCount.value = 0
    completedCount.value = 0
  }

  async function requestTask({ turnstileToken = null, currentTaskId = null } = {}) {
    if (roundCompleted.value) return null
    if (currentTaskId != null && roundAssignedFull.value) return null
    loading.value = true
    try {
      const payload = {}
      if (turnstileToken) payload.turnstile_token = turnstileToken
      if (currentTaskId != null) payload.current_task_id = currentTaskId
      const res = await api.post('/tasks/next', payload)
      if (res.message) message.value = res.message
      return res.task || null
    } catch (err) {
      message.value = err.detail || '获取任务失败'
      return null
    } finally {
      loading.value = false
    }
  }

  async function startRound(turnstileToken = null) {
    clearTasks()
    const task = await requestTask({ turnstileToken })
    currentTask.value = task
    if (task) {
      assignedCount.value = 1
    }
    return task
  }

  async function prefetchNextTask() {
    if (!currentTask.value || nextTask.value || prefetching.value) return nextTask.value
    if (assignedCount.value >= ROUND_SIZE) return null

    prefetching.value = true
    try {
      const task = await requestTask({ currentTaskId: currentTask.value.task_id })
      if (task && task.task_id !== currentTask.value.task_id) {
        nextTask.value = task
        assignedCount.value += 1
        preloadImage(task.image_url)
      }
      return nextTask.value
    } finally {
      prefetching.value = false
    }
  }

  async function submitTaskScore({ taskId, imageId, aesthetic, completeness }) {
    submitting.value = true
    try {
      await api.post(`/tasks/${taskId}/submit`, {
        image_id: imageId,
        aesthetic_score: aesthetic,
        completeness_score: completeness,
      })
      completedCount.value += 1
      return true
    } catch (err) {
      message.value = err.detail || '提交失败'
      return false
    } finally {
      submitting.value = false
    }
  }

  function promoteNextTask() {
    currentTask.value = nextTask.value
    nextTask.value = null
    return currentTask.value
  }

  return {
    ROUND_SIZE,
    currentTask,
    nextTask,
    loading,
    prefetching,
    submitting,
    message,
    assignedCount,
    completedCount,
    progressPercent,
    roundAssignedFull,
    roundCompleted,
    clearTasks,
    requestTask,
    startRound,
    prefetchNextTask,
    submitTaskScore,
    promoteNextTask,
  }
})
