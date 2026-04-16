import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

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

  async function fetchNextTask({ turnstileToken = null, currentTaskId = null } = {}) {
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

  async function startSession(turnstileToken = null) {
    const task = await fetchNextTask({ turnstileToken })
    currentTask.value = task
    nextTask.value = null
    return task
  }

  async function prefetchNextTask() {
    if (!currentTask.value || nextTask.value || prefetching.value) return nextTask.value
    prefetching.value = true
    try {
      const task = await fetchNextTask({ currentTaskId: currentTask.value.task_id })
      if (task && task.task_id !== currentTask.value.task_id) {
        nextTask.value = task
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

  function clearTasks() {
    currentTask.value = null
    nextTask.value = null
    message.value = ''
  }

  return {
    currentTask,
    nextTask,
    loading,
    prefetching,
    submitting,
    message,
    startSession,
    fetchNextTask,
    prefetchNextTask,
    submitTaskScore,
    promoteNextTask,
    clearTasks,
  }
})
