<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold" style="color: var(--color-text-primary);">Camera Health</h1>
      <p style="color: var(--color-text-muted);">Monitor camera connectivity and health status</p>
    </div>

    <!-- Overview cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="card p-4">
        <p class="text-sm" style="color: var(--color-text-muted);">Total Cameras</p>
        <p class="text-2xl font-bold" style="color: var(--color-text-primary);">{{ cameras.length }}</p>
      </div>
      <div class="card p-4">
        <p class="text-sm" style="color: var(--color-text-muted);">Online</p>
        <p class="text-2xl font-bold text-green-500">{{ onlineCameras }}</p>
      </div>
      <div class="card p-4">
        <p class="text-sm" style="color: var(--color-text-muted);">Warning</p>
        <p class="text-2xl font-bold text-yellow-500">{{ warningCameras }}</p>
      </div>
      <div class="card p-4">
        <p class="text-sm" style="color: var(--color-text-muted);">Offline</p>
        <p class="text-2xl font-bold text-red-500">{{ offlineCameras }}</p>
      </div>
    </div>

    <!-- Camera health list -->
    <CollapsibleCard
      title="Camera Status"
      subtitle="Current status of all cameras"
      :icon="VideoCameraIcon"
      icon-color="green"
    >
      <div v-if="loading" class="flex justify-center py-12">
        <div class="spinner w-8 h-8"></div>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="table">
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
                  class="font-medium text-primary-600 dark:text-primary-400 hover:text-primary-500 dark:hover:text-primary-300"
                >
                  {{ camera.name }}
                </router-link>
              </td>
              <td>
                <span :class="getStatusClass(camera)">
                  {{ getStatusText(camera) }}
                </span>
              </td>
              <td style="color: var(--color-text-secondary);">
                <div class="flex items-center">
                  <div class="w-24 rounded-full h-2 mr-2" style="background-color: var(--color-bg-secondary);">
                    <div
                      class="h-2 rounded-full"
                      :class="getUptimeClass(camera.uptime)"
                      :style="{ width: `${camera.uptime || 0}%` }"
                    ></div>
                  </div>
                  {{ (camera.uptime || 0).toFixed(1) }}%
                </div>
              </td>
              <td style="color: var(--color-text-secondary);">
                {{ camera.avg_response ? `${camera.avg_response}ms` : '-' }}
              </td>
              <td style="color: var(--color-text-secondary);">
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
                  <span v-if="!camera.is_blank && !camera.is_frozen" style="color: var(--color-text-muted);">
                    None
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </CollapsibleCard>

    <!-- Health history chart placeholder -->
    <CollapsibleCard
      title="Health History (24h)"
      subtitle="Camera uptime and response times over time"
      :icon="ChartBarIcon"
      icon-color="blue"
    >
      <div class="h-64 rounded-lg flex items-center justify-center" style="background-color: var(--color-bg-secondary); color: var(--color-text-muted);">
        <div class="text-center">
          <ChartBarIcon class="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>Health timeline visualization</p>
          <p class="text-sm">Coming soon</p>
        </div>
      </div>
    </CollapsibleCard>

    <!-- Recent alerts -->
    <CollapsibleCard
      title="Recent Alerts"
      subtitle="Camera warnings and errors"
      :icon="ExclamationTriangleIcon"
      icon-color="yellow"
    >
      <div v-if="alerts.length === 0" class="py-8 text-center" style="color: var(--color-text-muted);">
        <BellSlashIcon class="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No recent alerts</p>
      </div>
      <ul v-else class="divide-y" style="border-color: var(--color-border);">
        <li v-for="alert in alerts" :key="alert.id" class="py-4 flex items-center justify-between">
          <div class="flex items-center">
            <ExclamationTriangleIcon
              class="w-5 h-5 mr-3"
              :class="alert.type === 'error' ? 'text-red-500' : 'text-yellow-500'"
            />
            <div>
              <p style="color: var(--color-text-primary);">{{ alert.message }}</p>
              <p class="text-xs" style="color: var(--color-text-muted);">{{ alert.camera_name }}</p>
            </div>
          </div>
          <span class="text-sm" style="color: var(--color-text-muted);">{{ formatTime(alert.created_at) }}</span>
        </li>
      </ul>
    </CollapsibleCard>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import api from '@/api'
import CollapsibleCard from '@/components/ui/CollapsibleCard.vue'
import {
  VideoCameraIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  BellSlashIcon,
} from '@heroicons/vue/24/outline'

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
  if (!camera.is_active) return 'badge bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
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
