import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useCamerasStore = defineStore('cameras', () => {
  const cameras = ref([])
  const loading = ref(false)
  const error = ref(null)

  const activeCameras = computed(() =>
    cameras.value.filter(c => c.is_active)
  )

  const cameraCount = computed(() => cameras.value.length)
  const activeCameraCount = computed(() => activeCameras.value.length)

  async function fetchCameras() {
    loading.value = true
    error.value = null
    try {
      const response = await api.get('/cameras')
      cameras.value = response.data.cameras || []
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch cameras'
    } finally {
      loading.value = false
    }
  }

  async function getCamera(id) {
    try {
      const response = await api.get(`/cameras/${id}`)
      return response.data
    } catch (err) {
      throw new Error(err.response?.data?.detail || 'Failed to fetch camera')
    }
  }

  async function createCamera(data) {
    try {
      // Clean up empty strings - convert to null for API
      const cleanData = { ...data }
      if (cleanData.hostname === '') cleanData.hostname = null
      if (cleanData.ip_address === '') cleanData.ip_address = null

      const response = await api.post('/cameras', cleanData)
      cameras.value.push(response.data)
      return { success: true, camera: response.data }
    } catch (err) {
      const detail = err.response?.data?.detail
      // Handle validation error arrays from Pydantic
      const errorMsg = Array.isArray(detail)
        ? detail.map(e => e.msg).join(', ')
        : detail || 'Failed to create camera'
      return {
        success: false,
        error: errorMsg,
      }
    }
  }

  async function updateCamera(id, data) {
    try {
      // Clean up empty strings - convert to null for API
      const cleanData = { ...data }
      if (cleanData.hostname === '') cleanData.hostname = null
      if (cleanData.ip_address === '') cleanData.ip_address = null

      const response = await api.put(`/cameras/${id}`, cleanData)
      const index = cameras.value.findIndex(c => c.id === id)
      if (index !== -1) {
        cameras.value[index] = response.data
      }
      return { success: true, camera: response.data }
    } catch (err) {
      const detail = err.response?.data?.detail
      // Handle validation error arrays from Pydantic
      const errorMsg = Array.isArray(detail)
        ? detail.map(e => e.msg).join(', ')
        : detail || 'Failed to update camera'
      return {
        success: false,
        error: errorMsg,
      }
    }
  }

  async function deleteCamera(id) {
    try {
      await api.delete(`/cameras/${id}`)
      cameras.value = cameras.value.filter(c => c.id !== id)
      return { success: true }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Failed to delete camera',
      }
    }
  }

  async function testCamera(id) {
    try {
      const response = await api.post(`/cameras/${id}/test`)
      return { success: true, result: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Camera test failed',
      }
    }
  }

  async function captureNow(id) {
    try {
      const response = await api.post(`/cameras/${id}/capture`)
      return { success: true, result: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Capture failed',
      }
    }
  }

  return {
    cameras,
    loading,
    error,
    activeCameras,
    cameraCount,
    activeCameraCount,
    fetchCameras,
    getCamera,
    createCamera,
    updateCamera,
    deleteCamera,
    testCamera,
    captureNow,
  }
})
