import { defineStore } from 'pinia'
import { ref, reactive } from 'vue'
import api from '../api'

export const useScoreStore = defineStore('score', () => {
  const images = ref([])
  const currentIndex = ref(0)
  const loading = ref(false)
  const message = ref('')
  const scoredIds = ref(new Set())

  async function fetchBatch(turnstileToken = null) {
    loading.value = true
    try {
      const payload = turnstileToken ? { turnstile_token: turnstileToken } : {}
      const res = await api.post('/images/batch', payload)
      images.value = res.images || []
      currentIndex.value = 0
      if (res.message) message.value = res.message
    } catch (err) {
      message.value = err.detail || '获取图片失败'
    } finally {
      loading.value = false
    }
  }

  async function submitScore(imageId, aesthetic, completeness) {
    try {
      await api.post('/score', {
        image_id: imageId,
        aesthetic_score: aesthetic,
        completeness_score: completeness,
      })
      scoredIds.value.add(imageId)
      return true
    } catch (err) {
      message.value = err.detail || '提交失败'
      return false
    }
  }

  async function loadScoredIds() {
    try {
      const res = await api.get('/my-scores')
      scoredIds.value = new Set(res.scored_image_ids)
    } catch {
      scoredIds.value = new Set()
    }
  }

  const currentImage = () => images.value[currentIndex.value] || null
  const hasNext = () => currentIndex.value < images.value.length - 1
  const nextImage = () => { if (hasNext()) currentIndex.value++ }

  return {
    images, currentIndex, loading, message, scoredIds,
    fetchBatch, submitScore, loadScoredIds,
    currentImage, hasNext, nextImage
  }
})
