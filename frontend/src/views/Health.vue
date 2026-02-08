<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-gray-900">Camera Health</h1>
      <p class="text-gray-500">Monitor camera connectivity and health status</p>
    </div>

    <!-- Overview cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="card p-4">
        <p class="text-sm text-gray-500">Total Cameras</p>
        <p class="text-2xl font-bold text-gray-900">{{ cameras.length }}</p>
      </div>
      <div class="card p-4">
        <p class="text-sm text-gray-500">Online</p>
        <p class="text-2xl font-bold text-green-500">{{ onlineCameras }}</p>
      </div>
      <div class="card p-4">
        <p class="text-sm text-gray-500">Warning</p>
        <p class="text-2xl font-bold text-yellow-500">{{ warningCameras }}</p>
      </div>
      <div class="card p-4">
        <p class="text-sm text-gray-500">Offline</p>
        <p class="text-2xl font-bold text-red-500">{{ offlineCameras }}</p>
      </div>
    </div>

    <!-- Camera health list -->
    <div class="card">
      <div class="p-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Camera Status</h2>
      </div>
      <div v-if="loading" class="flex justify-center py-12">
        <div class="spinner w-8 h-8"></div>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Camera</th>
            <th>Status</th>
            <th>Uptime (24h)</th>
            <th>Avg Response</th>
            <th>Last Check</th>
            <th>Issues</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="camera in cameras" :key="camera.id">
            <td>
              <router-link
                :to="`/cameras/${camera.id}`"
                class="font-medium text-primary-600 hover:text-primary-500"
              >
                {{ camera.name }}
              </router-link>
            </td>
            <td>
              <span :class="getStatusClass(camera)">
                {{ getStatusText(camera) }}
              </span>
            </td>
            <td class="text-gray-700">
              <div class="flex items-center">
                <div class="w-24 bg-gray-200 rounded-full h-2 mr-2">
                  <div
                    class="h-2 rounded-full"
                    :class="getUptimeClass(camera.uptime)"
                    :style="{ width: `${camera.uptime || 0}%` }"
                  ></div>
                </div>
                {{ (camera.uptime || 0).toFixed(1) }}%
              </div>
            </td>
            <td class="text-gray-700">
              {{ camera.avg_response ? `${camera.avg_response}ms` : '-' }}
            </td>
            <td class="text-gray-700">
              {{ camera.last_check ? formatTime(camera.last_check) : 'Never' }}
            </td>
            <td>
              <div class="flex items-center space-x-2">
                <span
                  v-if="camera.is_blank"
                  class="badge-warning"
                  title="Blank images detected"
                >
                  Blank
                </span>
                <span
                  v-if="camera.is_frozen"
                  class="badge-warning"
                  title="Frozen images detected"
                >
                  Frozen
                </span>
                <span v-if="!camera.is_blank && !camera.is_frozen" class="text-gray-400">
                  None
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Health history chart placeholder -->
    <div class="card">
      <div class="p-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Health History (24h)</h2>
      </div>
      <div class="p-4">
        <div class="h-64 bg-gray-50 rounded-lg flex items-center justify-center text-gray-500">
          Health timeline visualization would go here
        </div>
      </div>
    </div>

    <!-- Recent alerts -->
    <div class="card">
      <div class="p-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-900">Recent Alerts</h2>
      </div>
      <div v-if="alerts.length === 0" class="p-4 text-center text-gray-500">
        No recent alerts
      </div>
      <ul v-else class="divide-y divide-gray-200">
        <li v-for="alert in alerts" :key="alert.id" class="p-4 flex items-center justify-between">
          <div class="flex items-center">
            <ExclamationTriangleIcon
              class="w-5 h-5 mr-3"
              :class="alert.type === 'error' ? 'text-red-500' : 'text-yellow-500'"
            />
            <div>
              <p class="text-gray-900">{{ alert.message }}</p>
              <p class="text-xs text-gray-500">{{ alert.camera_name }}</p>
            </div>
          </div>
          <span class="text-sm text-gray-500">{{ formatTime(alert.created_at) }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import api from '@/api'
import { ExclamationTriangleIcon } from '@heroicons/vue/24/outline'

const loading = ref(true)
const cameras = ref([])
const alerts = ref([])

const onlineCameras = computed(() =>
  cameras.value.filter(c => c.is_active && c.consecutive_errors === 0).length
)

const warningCameras = computed(() =>
  cameras.value.filter(c => c.is_active && c.consecutive_errors > 0 && c.consecutive_errors < 3).length
)

const offlineCameras = computed(() =>
  cameras.value.filter(c => !c.is_active || c.consecutive_errors >= 3).length
)

async function loadHealth() {
  try {
    const [camerasResponse, healthResponse] = await Promise.all([
      api.get('/cameras'),
      api.get('/health/cameras'),
    ])

    const camerasList = camerasResponse.data.cameras || []
    const healthList = Array.isArray(healthResponse.data) ? healthResponse.data : []
    cameras.value = camerasList.map(camera => {
      const health = healthList.find(h => h.camera_id === camera.id) || {}
      return {
        ...camera,
        uptime: health.uptime_percent || 100,
        avg_response: health.avg_response_ms,
        last_check: health.last_check,
        is_blank: health.is_blank,
        is_frozen: health.is_frozen,
      }
    })
  } catch (error) {
    console.error('Failed to load health data:', error)
  } finally {
    loading.value = false
  }
}

async function loadAlerts() {
  try {
    const response = await api.get('/health/alerts?limit=10')
    alerts.value = response.data || []
  } catch (error) {
    // Endpoint may not exist yet, silently fail
    alerts.value = []
  }
}

function getStatusClass(camera) {
  if (!camera.is_active) return 'badge bg-gray-200 text-gray-500'
  if (camera.consecutive_errors >= 3) return 'badge-danger'
  if (camera.consecutive_errors > 0) return 'badge-warning'
  return 'badge-success'
}

function getStatusText(camera) {
  if (!camera.is_active) return 'Inactive'
  if (camera.consecutive_errors >= 3) return 'Offline'
  if (camera.consecutive_errors > 0) return 'Warning'
  return 'Online'
}

function getUptimeClass(uptime) {
  if (uptime >= 99) return 'bg-green-500'
  if (uptime >= 95) return 'bg-yellow-500'
  return 'bg-red-500'
}

function formatTime(dateStr) {
  if (!dateStr) return 'Never'
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true })
  } catch {
    return 'Invalid'
  }
}

onMounted(() => {
  loadHealth()
  loadAlerts()
})
</script>
