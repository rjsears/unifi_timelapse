<template>
  <div class="space-y-6">
    <!-- Stats cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        title="Active Cameras"
        :value="camerasStore.activeCameraCount"
        :subtitle="`${camerasStore.cameraCount} total`"
        icon="camera"
        color="primary"
      />
      <StatCard
        title="Images Today"
        :value="stats.imagesToday"
        :subtitle="`${stats.imagesTotal} total`"
        icon="photo"
        color="green"
      />
      <StatCard
        title="Timelapses"
        :value="stats.timelapsesCompleted"
        :subtitle="`${stats.timelapsesPending} pending`"
        icon="film"
        color="purple"
      />
      <StatCard
        title="Storage Used"
        :value="`${storagePercent}%`"
        :subtitle="storageText"
        icon="server"
        :color="storageColor"
      />
    </div>

    <!-- Camera grid -->
    <div class="card">
      <div class="p-4 border-b border-dark-700 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-white">Camera Status</h2>
        <router-link to="/cameras" class="text-sm text-primary-400 hover:text-primary-300">
          View All
        </router-link>
      </div>
      <div class="p-4">
        <div v-if="camerasStore.loading" class="flex justify-center py-8">
          <div class="spinner w-8 h-8"></div>
        </div>
        <div v-else-if="camerasStore.cameras.length === 0" class="text-center py-8 text-dark-400">
          No cameras configured. <router-link to="/cameras" class="text-primary-400">Add one</router-link>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <CameraCard
            v-for="camera in camerasStore.cameras.slice(0, 6)"
            :key="camera.id"
            :camera="camera"
          />
        </div>
      </div>
    </div>

    <!-- Recent activity -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Recent timelapses -->
      <div class="card">
        <div class="p-4 border-b border-dark-700">
          <h2 class="text-lg font-semibold text-white">Recent Timelapses</h2>
        </div>
        <div class="p-4">
          <div v-if="recentTimelapses.length === 0" class="text-center py-4 text-dark-400">
            No timelapses yet
          </div>
          <ul v-else class="space-y-3">
            <li
              v-for="timelapse in recentTimelapses"
              :key="timelapse.id"
              class="flex items-center justify-between py-2 border-b border-dark-700 last:border-0"
            >
              <div>
                <p class="text-sm font-medium text-white">{{ timelapse.camera_name }}</p>
                <p class="text-xs text-dark-400">{{ formatDate(timelapse.date_start) }}</p>
              </div>
              <span :class="statusBadgeClass(timelapse.status)">
                {{ timelapse.status }}
              </span>
            </li>
          </ul>
        </div>
      </div>

      <!-- System health -->
      <div class="card">
        <div class="p-4 border-b border-dark-700">
          <h2 class="text-lg font-semibold text-white">System Health</h2>
        </div>
        <div class="p-4 space-y-4">
          <HealthItem label="API Status" :status="systemStore.systemInfo?.status" />
          <HealthItem label="Database" status="healthy" />
          <HealthItem label="Worker" :status="workerStatus" />
          <HealthItem label="Storage" :status="storageStatus" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useCamerasStore } from '@/stores/cameras'
import { useSystemStore } from '@/stores/system'
import api from '@/api'
import { format } from 'date-fns'
import StatCard from '@/components/dashboard/StatCard.vue'
import CameraCard from '@/components/dashboard/CameraCard.vue'
import HealthItem from '@/components/dashboard/HealthItem.vue'

const camerasStore = useCamerasStore()
const systemStore = useSystemStore()

const stats = ref({
  imagesToday: 0,
  imagesTotal: 0,
  timelapsesCompleted: 0,
  timelapsesPending: 0,
})

const recentTimelapses = ref([])

const storagePercent = computed(() => {
  return Math.round(systemStore.storageInfo?.percent_used || 0)
})

const storageText = computed(() => {
  const free = systemStore.storageInfo?.free_bytes || 0
  const freeGB = (free / (1024 ** 3)).toFixed(1)
  return `${freeGB} GB free`
})

const storageColor = computed(() => {
  const percent = storagePercent.value
  if (percent >= 90) return 'red'
  if (percent >= 75) return 'yellow'
  return 'green'
})

const workerStatus = computed(() => {
  return systemStore.systemInfo?.worker_status || 'unknown'
})

const storageStatus = computed(() => {
  const percent = storagePercent.value
  if (percent >= 90) return 'critical'
  if (percent >= 75) return 'warning'
  return 'healthy'
})

function formatDate(dateStr) {
  return format(new Date(dateStr), 'MMM d, yyyy')
}

function statusBadgeClass(status) {
  const classes = {
    completed: 'badge-success',
    processing: 'badge-info',
    pending: 'badge-warning',
    failed: 'badge-danger',
  }
  return classes[status] || 'badge-info'
}

async function fetchStats() {
  try {
    // Fetch image stats
    const imagesResponse = await api.get('/images/stats')
    stats.value.imagesToday = imagesResponse.data.today || 0
    stats.value.imagesTotal = imagesResponse.data.total || 0

    // Fetch timelapse stats
    const timelapsesResponse = await api.get('/timelapses/stats')
    stats.value.timelapsesCompleted = timelapsesResponse.data.completed || 0
    stats.value.timelapsesPending = timelapsesResponse.data.pending || 0

    // Fetch recent timelapses
    const recentResponse = await api.get('/timelapses?limit=5')
    recentTimelapses.value = recentResponse.data
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  }
}

onMounted(async () => {
  await Promise.all([
    camerasStore.fetchCameras(),
    systemStore.fetchAll(),
    fetchStats(),
  ])
})
</script>
