import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useMultidayStore = defineStore('multiday', () => {
  const configs = ref([])
  const loading = ref(false)
  const error = ref(null)

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

  return {
    configs,
    loading,
    error,
    fetchConfigs,
    createConfig,
    updateConfig,
    deleteConfig,
    triggerGeneration,
  }
})
