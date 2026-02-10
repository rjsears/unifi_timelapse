import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useMultidayStore = defineStore('multiday', () => {
  const configs = ref([])
  const loading = ref(false)
  const error = ref(null)
  const availableDates = ref([])
  const loadingDates = ref(false)

  async function fetchConfigs(cameraId = null) {
    loading.value = true
    error.value = null
    try {
      const params = cameraId ? `?camera_id=${cameraId}` : ''
      const response = await api.get(`/multiday${params}`)
      configs.value = response.data || []
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch configurations'
    } finally {
      loading.value = false
    }
  }

  async function createConfig(data) {
    try {
      const response = await api.post('/multiday', data)
      configs.value.push(response.data)
      return { success: true, config: response.data }
    } catch (err) {
      const detail = err.response?.data?.detail
      const errorMsg = Array.isArray(detail)
        ? detail.map(e => e.msg).join(', ')
        : detail || 'Failed to create configuration'
      return {
        success: false,
        error: errorMsg,
      }
    }
  }

  async function updateConfig(id, data) {
    try {
      const response = await api.put(`/multiday/${id}`, data)
      const index = configs.value.findIndex(c => c.id === id)
      if (index !== -1) {
        configs.value[index] = response.data
      }
      return { success: true, config: response.data }
    } catch (err) {
      const detail = err.response?.data?.detail
      const errorMsg = Array.isArray(detail)
        ? detail.map(e => e.msg).join(', ')
        : detail || 'Failed to update configuration'
      return {
        success: false,
        error: errorMsg,
      }
    }
  }

  async function deleteConfig(id) {
    try {
      await api.delete(`/multiday/${id}`)
      configs.value = configs.value.filter(c => c.id !== id)
      return { success: true }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Failed to delete configuration',
      }
    }
  }

  async function triggerGeneration(id) {
    try {
      const response = await api.post(`/multiday/${id}/generate`)
      return { success: true, result: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Failed to trigger generation',
      }
    }
  }

  // ============ Historical Mode (Custom Timelapse) ============

  async function getAvailableDates(cameraId) {
    loadingDates.value = true
    try {
      const response = await api.get(`/images/camera/${cameraId}/available-dates`)
      availableDates.value = response.data
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Failed to fetch available dates',
      }
    } finally {
      loadingDates.value = false
    }
  }

  async function generateHistorical(data) {
    try {
      const response = await api.post('/multiday/generate-historical', data)
      return { success: true, result: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Failed to start historical generation',
      }
    }
  }

  // ============ Prospective Mode ============

  async function startCollection(configId, daysToCollect) {
    try {
      const response = await api.post(`/multiday/${configId}/start-collection`, {
        days_to_collect: daysToCollect,
      })
      // Update local config
      const index = configs.value.findIndex(c => c.id === configId)
      if (index !== -1) {
        configs.value[index].status = 'collecting'
        configs.value[index].collection_start_date = response.data.collection_start_date
        configs.value[index].collection_end_date = response.data.collection_end_date
      }
      return { success: true, result: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Failed to start collection',
      }
    }
  }

  async function getProgress(configId) {
    try {
      const response = await api.get(`/multiday/${configId}/progress`)
      return { success: true, data: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Failed to get progress',
      }
    }
  }

  async function cancelCollection(configId, unprotectImages = false) {
    try {
      const response = await api.post(`/multiday/${configId}/cancel-collection`, {
        unprotect_images: unprotectImages,
      })
      // Update local config
      const index = configs.value.findIndex(c => c.id === configId)
      if (index !== -1) {
        configs.value[index].status = 'idle'
        configs.value[index].collection_start_date = null
        configs.value[index].collection_end_date = null
        configs.value[index].collection_progress_days = 0
      }
      return { success: true, result: response.data }
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Failed to cancel collection',
      }
    }
  }

  return {
    configs,
    loading,
    error,
    availableDates,
    loadingDates,
    fetchConfigs,
    createConfig,
    updateConfig,
    deleteConfig,
    triggerGeneration,
    getAvailableDates,
    generateHistorical,
    startCollection,
    getProgress,
    cancelCollection,
  }
})
