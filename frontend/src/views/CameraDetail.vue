<template>
  <div class="space-y-6">
    <div v-if="loading" class="flex justify-center py-12">
      <div class="spinner w-8 h-8"></div>
    </div>

    <template v-else-if="camera">
      <!-- Header -->
      <div class="flex items-center justify-between">
        <div>
          <router-link to="/cameras" class="text-sm text-gray-500 hover:text-gray-900 flex items-center mb-2">
            <ArrowLeftIcon class="w-4 h-4 mr-1" />
            Back to Cameras
          </router-link>
          <h1 class="text-2xl font-bold text-gray-900">{{ camera.name }}</h1>
          <p class="text-gray-500">{{ camera.hostname || camera.ip_address }}</p>
        </div>
        <div class="flex items-center space-x-3">
          <button class="btn-secondary" @click="testConnection">
            <SignalIcon class="w-4 h-4 mr-2" />
            Test
          </button>
          <button class="btn-primary" @click="captureNow">
            <CameraIcon class="w-4 h-4 mr-2" />
            Capture Now
          </button>
        </div>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="card p-4">
          <p class="text-sm text-gray-500">Status</p>
          <p class="text-lg font-semibold" :class="statusColor">{{ statusText }}</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">Capture Interval</p>
          <p class="text-lg font-semibold text-gray-900">{{ camera.capture_interval }}s</p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">Last Capture</p>
          <p class="text-lg font-semibold text-gray-900">
            {{ camera.last_capture_at ? formatTime(camera.last_capture_at) : 'Never' }}
          </p>
        </div>
        <div class="card p-4">
          <p class="text-sm text-gray-500">Images Today</p>
          <p class="text-lg font-semibold text-gray-900">{{ imagesCount }}</p>
        </div>
      </div>

      <!-- Live preview and recent images -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Live preview -->
        <div class="card">
          <div class="p-4 border-b border-gray-200">
            <h2 class="text-lg font-semibold text-gray-900">Live Preview</h2>
          </div>
          <div class="p-4">
            <div class="aspect-video bg-gray-100 rounded-lg overflow-hidden">
              <img
                v-if="previewUrl"
                :src="previewUrl"
                :key="previewKey"
                class="w-full h-full object-contain"
                @error="previewError = true"
              />
              <div v-else class="flex items-center justify-center h-full text-gray-500">
                <span v-if="previewError">Failed to load preview</span>
                <span v-else>Loading...</span>
              </div>
            </div>
            <button
              class="mt-4 w-full btn-secondary"
              @click="refreshPreview"
            >
              Refresh Preview
            </button>
          </div>
        </div>

        <!-- Recent images -->
        <div class="card">
          <div class="p-4 border-b border-gray-200 flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900">Recent Images</h2>
            <router-link :to="`/images?camera=${camera.id}`" class="text-sm text-primary-600">
              View All
            </router-link>
          </div>
          <div class="p-4">
            <div v-if="recentImages.length === 0" class="text-center py-8 text-gray-500">
              No images captured yet
            </div>
            <div v-else class="grid grid-cols-3 gap-2">
              <div
                v-for="image in recentImages"
                :key="image.id"
                class="aspect-video bg-gray-100 rounded overflow-hidden"
              >
                <img
                  :src="`/api/images/${image.id}/thumbnail`"
                  class="w-full h-full object-cover"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Configuration -->
      <div class="card">
        <div class="p-4 border-b border-gray-200">
          <h2 class="text-lg font-semibold text-gray-900">Configuration</h2>
        </div>
        <div class="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <p class="text-sm text-gray-500">Active</p>
            <p class="text-gray-900">{{ camera.is_active ? 'Yes' : 'No' }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Timelapse Enabled</p>
            <p class="text-gray-900">{{ camera.timelapse_enabled ? 'Yes' : 'No' }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Timelapse Time</p>
            <p class="text-gray-900">{{ camera.timelapse_time || 'Default' }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Blackout Start</p>
            <p class="text-gray-900">{{ camera.blackout_start || 'None' }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Blackout End</p>
            <p class="text-gray-900">{{ camera.blackout_end || 'None' }}</p>
          </div>
          <div>
            <p class="text-sm text-gray-500">Consecutive Errors</p>
            <p class="text-gray-900">{{ camera.consecutive_errors }}</p>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="text-center py-12">
      <p class="text-gray-500">Camera not found</p>
      <router-link to="/cameras" class="text-primary-600 mt-4 inline-block">
        Back to Cameras
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useCamerasStore } from '@/stores/cameras'
import { useNotificationsStore } from '@/stores/notifications'
import { formatDistanceToNow } from 'date-fns'
import api from '@/api'
import {
  ArrowLeftIcon,
  SignalIcon,
  CameraIcon,
} from '@heroicons/vue/24/outline'

const route = useRoute()
const camerasStore = useCamerasStore()
const notifications = useNotificationsStore()

const loading = ref(true)
const camera = ref(null)
const recentImages = ref([])
const imagesCount = ref(0)
const previewUrl = ref('')
const previewKey = ref(0)
const previewError = ref(false)

let refreshInterval = null

const statusText = computed(() => {
  if (!camera.value?.is_active) return 'Inactive'
  if (camera.value?.consecutive_errors >= 3) return 'Failing'
  if (camera.value?.consecutive_errors > 0) return 'Warning'
  return 'Active'
})

const statusColor = computed(() => {
  if (!camera.value?.is_active) return 'text-gray-500'
  if (camera.value?.consecutive_errors >= 3) return 'text-red-500'
  if (camera.value?.consecutive_errors > 0) return 'text-yellow-500'
  return 'text-green-500'
})

function formatTime(dateStr) {
  return formatDistanceToNow(new Date(dateStr), { addSuffix: true })
}

async function loadCamera() {
  try {
    camera.value = await camerasStore.getCamera(route.params.id)
    await loadRecentImages()
    refreshPreview()
  } catch (error) {
    notifications.error('Error', 'Failed to load camera')
  } finally {
    loading.value = false
  }
}

async function loadRecentImages() {
  try {
    const response = await api.get(`/images?camera_id=${route.params.id}&limit=9`)
    recentImages.value = response.data.images || []
    imagesCount.value = response.data.total || 0
  } catch (error) {
    console.error('Failed to load recent images:', error)
  }
}

function refreshPreview() {
  previewError.value = false
  previewKey.value++
  previewUrl.value = `/api/cameras/${route.params.id}/preview?t=${Date.now()}`
}

async function testConnection() {
  notifications.info('Testing...', 'Testing camera connection')
  const result = await camerasStore.testCamera(route.params.id)
  if (result.success && result.result?.success) {
    notifications.success('Success', `Camera is reachable (${result.result.response_time_ms}ms)`)
  } else {
    notifications.error('Failed', result.result?.error || result.error || 'Camera is not reachable')
  }
}

async function captureNow() {
  notifications.info('Capturing...', 'Capturing image')
  const result = await camerasStore.captureNow(route.params.id)
  if (result.success) {
    notifications.success('Captured', 'Image captured successfully')
    await loadRecentImages()
    refreshPreview()
  } else {
    notifications.error('Failed', result.error)
  }
}

onMounted(() => {
  loadCamera()
  // Auto-refresh preview every 30 seconds
  refreshInterval = setInterval(refreshPreview, 30000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>
