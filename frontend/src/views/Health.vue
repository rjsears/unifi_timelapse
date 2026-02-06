<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">Camera Health</h1>
      <p class="text-dark-400">Monitor camera connectivity and health status</p>
    </div>

    <!-- Overview cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="card p-4">
        <p class="text-sm text-dark-400">Total Cameras</p>
        <p class="text-2xl font-bold text-white">{{ cameras.length }}</p>
      </div>
      <div class="card p-4">
        <p class="text-sm text-dark-400">Online</p>
        <p class="text-2xl font-bold text-green-400">{{ onlineCameras }}</p>
      </div>
      <div class="card p-4">
        <p class="text-sm text-dark-400">Warning</p>
        <p class="text-2xl font-bold text-yellow-400">{{ warningCameras }}</p>
      </div>
      <div class="card p-4">
        <p class="text-sm text-dark-400">Offline</p>
        <p class="text-2xl font-bold text-red-400">{{ offlineCameras }}</p>
      </div>
    </div>

    <!-- Camera health list -->
    <div class="card">
      <div class="p-4 border-b border-dark-700">
        <h2 class="text-lg font-semibold text-white">Camera Status</h2>
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
                class="font-medium text-primary-400 hover:text-primary-300"
              >
                {{ camera.name }}
              </router-link>
            </td>
            <td>
              <span :class="getStatusClass(camera)">
                {{ getStatusText(camera) }}
              </span>
            </td>
            <td class="text-dark-300">
              <div class="flex items-center">
                <div class="w-24 bg-dark-700 rounded-full h-2 mr-2">
                  <div
                    class="h-2 rounded-full"
                    :class="getUptimeClass(camera.uptime)"
                    :style="{ width: `${camera.uptime || 0}%` }"
                  ></div>
                </div>
                {{ (camera.uptime || 0).toFixed(1) }}%
              </div>
            </td>
            <td class="text-dark-300">
              {{ camera.avg_response ? `${camera.avg_response}ms` : '-' }}
            </td>
            <td class="text-dark-300">
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
                <span v-if="!camera.is_blank && !camera.is_frozen" class="text-dark-500">
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
      <div class="p-4 border-b border-dark-700">
        <h2 class="text-lg font-semibold text-white">Health History (24h)</h2>
      </div>
      <div class="p-4">
        <div class="h-64 bg-dark-700/50 rounded-lg flex items-center justify-center text-dark-400">
          Health timeline visualization would go here
        </div>
      </div>
    </div>

    <!-- Recent alerts -->
    <div class="card">
      <div class="p-4 border-b border-dark-700">
        <h2 class="text-lg font-semibold text-white">Recent Alerts</h2>
      </div>
      <div v-if="alerts.length === 0" class="p-4 text-center text-dark-400">
        No recent alerts
      </div>
      <ul v-else class="divide-y divide-dark-700">
        <li v-for="alert in alerts" :key="alert.id" class="p-4 flex items-center justify-between">
          <div class="flex items-center">
            <ExclamationTriangleIcon
              class="w-5 h-5 mr-3"
              :class="alert.type === 'error' ? 'text-red-400' : 'text-yellow-400'"
            />
            <div>
              <p class="text-white">{{ alert.message }}</p>
              <p class="text-xs text-dark-400">{{ alert.camera_name }}</p>
            </div>
          </div>
          <span class="text-sm text-dark-400">{{ formatTime(alert.created_at) }}</span>
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

    cameras.value = camerasResponse.data.map(camera => {
      const health = healthResponse.data.find(h => h.camera_id === camera.id) || {}
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
    alerts.value = response.data
  } catch (error) {
    console.error('Failed to load alerts:', error)
  }
}

function getStatusClass(camera) {
  if (!camera.is_active) return 'badge bg-dark-600 text-dark-400'
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
  return formatDistanceToNow(new Date(dateStr), { addSuffix: true })
}

onMounted(() => {
  loadHealth()
  loadAlerts()
})
</script>
