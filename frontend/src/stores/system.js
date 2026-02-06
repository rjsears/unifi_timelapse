import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api'

export const useSystemStore = defineStore('system', () => {
  const systemInfo = ref(null)
  const storageInfo = ref(null)
  const loading = ref(false)

  async function fetchSystemInfo() {
    try {
      const response = await api.get('/system/info')
      systemInfo.value = response.data
    } catch (err) {
      console.error('Failed to fetch system info:', err)
    }
  }

  async function fetchStorageInfo() {
    try {
      const response = await api.get('/system/storage')
      storageInfo.value = response.data
    } catch (err) {
      console.error('Failed to fetch storage info:', err)
    }
  }

  async function fetchAll() {
    loading.value = true
    await Promise.all([fetchSystemInfo(), fetchStorageInfo()])
    loading.value = false
  }

  return {
    systemInfo,
    storageInfo,
    loading,
    fetchSystemInfo,
    fetchStorageInfo,
    fetchAll,
  }
})
