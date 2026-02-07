<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Timelapses</h1>
        <p class="text-gray-500">View and manage timelapse videos</p>
      </div>
      <button class="btn-primary" @click="showGenerateModal = true">
        <PlayIcon class="w-5 h-5 mr-2" />
        Generate Timelapse
      </button>
    </div>

    <!-- Filters -->
    <div class="card p-4">
      <div class="flex flex-wrap gap-4">
        <select v-model="filters.camera" class="input w-auto">
          <option value="">All Cameras</option>
          <option v-for="camera in cameras" :key="camera.id" :value="camera.id">
            {{ camera.name }}
          </option>
        </select>
        <select v-model="filters.status" class="input w-auto">
          <option value="">All Status</option>
          <option value="completed">Completed</option>
          <option value="processing">Processing</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
        </select>
        <select v-model="filters.type" class="input w-auto">
          <option value="">All Types</option>
          <option value="daily">Daily</option>
          <option value="multiday">Multi-day</option>
        </select>
      </div>
    </div>

    <!-- Timelapse list -->
    <div class="card">
      <div v-if="loading" class="flex justify-center py-12">
        <div class="spinner w-8 h-8"></div>
      </div>
      <div v-else-if="timelapses.length === 0" class="text-center py-12">
        <FilmIcon class="w-12 h-12 mx-auto text-gray-400" />
        <h3 class="mt-4 text-lg font-medium text-gray-900">No timelapses found</h3>
        <p class="mt-2 text-gray-500">Timelapses will appear here once generated.</p>
      </div>
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
        <div
          v-for="timelapse in timelapses"
          :key="timelapse.id"
          class="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm"
        >
          <!-- Thumbnail -->
          <div class="aspect-video bg-gray-100 relative">
            <img
              v-if="timelapse.status === 'completed'"
              :src="`/api/timelapses/${timelapse.id}/thumbnail`"
              class="w-full h-full object-cover"
              @error="$event.target.style.display = 'none'"
            />
            <div class="absolute inset-0 flex items-center justify-center">
              <div
                v-if="timelapse.status === 'processing'"
                class="bg-gray-900/80 px-3 py-2 rounded-lg flex items-center text-white"
              >
                <div class="spinner w-4 h-4 mr-2"></div>
                Processing...
              </div>
              <PlayCircleIcon
                v-else-if="timelapse.status === 'completed'"
                class="w-12 h-12 text-white/80 cursor-pointer hover:text-white"
                @click="playTimelapse(timelapse)"
              />
            </div>
          </div>
          <!-- Info -->
          <div class="p-4">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-medium text-gray-900">{{ timelapse.camera_name }}</h3>
              <span :class="statusClass(timelapse.status)">{{ timelapse.status }}</span>
            </div>
            <p class="text-sm text-gray-500">
              {{ formatDateRange(timelapse) }}
            </p>
            <div v-if="timelapse.status === 'completed'" class="mt-2 text-xs text-gray-400">
              {{ timelapse.frame_count }} frames • {{ formatDuration(timelapse.duration_seconds) }}
            </div>
            <div v-if="timelapse.status === 'failed'" class="mt-2 text-xs text-red-500">
              {{ timelapse.error_message }}
            </div>
            <!-- Actions -->
            <div class="mt-4 flex items-center space-x-2">
              <button
                v-if="timelapse.status === 'completed'"
                class="btn-secondary text-xs px-3 py-1"
                @click="downloadTimelapse(timelapse)"
              >
                <ArrowDownTrayIcon class="w-4 h-4 mr-1" />
                Download
              </button>
              <button
                class="btn-secondary text-xs px-3 py-1 text-red-500 hover:text-red-600"
                @click="confirmDelete(timelapse)"
              >
                <TrashIcon class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Generate Modal -->
    <Modal v-model="showGenerateModal" title="Generate Timelapse" size="md">
      <form @submit.prevent="generateTimelapse" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Camera</label>
          <select v-model="generateForm.camera_id" class="input" required>
            <option value="">Select a camera</option>
            <option v-for="camera in cameras" :key="camera.id" :value="camera.id">
              {{ camera.name }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Date</label>
          <input v-model="generateForm.date" type="date" class="input" required />
        </div>
        <div class="flex justify-end space-x-3 pt-4">
          <button type="button" class="btn-secondary" @click="showGenerateModal = false">
            Cancel
          </button>
          <button type="submit" class="btn-primary">Generate</button>
        </div>
      </form>
    </Modal>

    <!-- Video Player Modal -->
    <Modal v-model="showPlayerModal" :title="playingTimelapse?.camera_name" size="full">
      <div class="aspect-video bg-black rounded-lg overflow-hidden">
        <video
          v-if="playingTimelapse"
          :src="`/api/timelapses/${playingTimelapse.id}/video`"
          controls
          autoplay
          class="w-full h-full"
        ></video>
      </div>
    </Modal>

    <!-- Delete confirmation -->
    <Modal v-model="showDeleteModal" title="Delete Timelapse" size="sm">
      <p class="text-gray-700">
        Are you sure you want to delete this timelapse?
      </p>
      <div class="flex justify-end space-x-3 pt-6">
        <button class="btn-secondary" @click="showDeleteModal = false">Cancel</button>
        <button class="btn-danger" @click="deleteTimelapse">Delete</button>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { format } from 'date-fns'
import api from '@/api'
import { useNotificationsStore } from '@/stores/notifications'
import Modal from '@/components/ui/Modal.vue'
import {
  PlayIcon,
  FilmIcon,
  PlayCircleIcon,
  ArrowDownTrayIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline'

const notifications = useNotificationsStore()

const loading = ref(false)
const timelapses = ref([])
const cameras = ref([])
const showGenerateModal = ref(false)
const showPlayerModal = ref(false)
const showDeleteModal = ref(false)
const playingTimelapse = ref(null)
const timelapseToDelete = ref(null)

const filters = ref({
  camera: '',
  status: '',
  type: '',
})

const generateForm = ref({
  camera_id: '',
  date: format(new Date(), 'yyyy-MM-dd'),
})

async function loadTimelapses() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.value.camera) params.append('camera_id', filters.value.camera)
    if (filters.value.status) params.append('status', filters.value.status)
    if (filters.value.type) params.append('type', filters.value.type)

    const response = await api.get(`/timelapses?${params}`)
    timelapses.value = response.data
  } catch (error) {
    notifications.error('Error', 'Failed to load timelapses')
  } finally {
    loading.value = false
  }
}

async function loadCameras() {
  try {
    const response = await api.get('/cameras')
    cameras.value = response.data
  } catch (error) {
    console.error('Failed to load cameras:', error)
  }
}

async function generateTimelapse() {
  try {
    await api.post('/timelapses/generate', generateForm.value)
    notifications.success('Started', 'Timelapse generation started')
    showGenerateModal.value = false
    await loadTimelapses()
  } catch (error) {
    notifications.error('Error', error.response?.data?.detail || 'Failed to start generation')
  }
}

function playTimelapse(timelapse) {
  playingTimelapse.value = timelapse
  showPlayerModal.value = true
}

function downloadTimelapse(timelapse) {
  window.open(`/api/timelapses/${timelapse.id}/download`, '_blank')
}

function confirmDelete(timelapse) {
  timelapseToDelete.value = timelapse
  showDeleteModal.value = true
}

async function deleteTimelapse() {
  try {
    await api.delete(`/timelapses/${timelapseToDelete.value.id}`)
    notifications.success('Deleted', 'Timelapse deleted')
    showDeleteModal.value = false
    await loadTimelapses()
  } catch (error) {
    notifications.error('Error', 'Failed to delete timelapse')
  }
}

function statusClass(status) {
  const classes = {
    completed: 'badge-success',
    processing: 'badge-info',
    pending: 'badge-warning',
    failed: 'badge-danger',
  }
  return classes[status] || 'badge'
}

function formatDateRange(timelapse) {
  if (timelapse.date_start === timelapse.date_end) {
    return format(new Date(timelapse.date_start), 'MMM d, yyyy')
  }
  return `${format(new Date(timelapse.date_start), 'MMM d')} - ${format(new Date(timelapse.date_end), 'MMM d, yyyy')}`
}

function formatDuration(seconds) {
  if (!seconds) return ''
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

watch(filters, loadTimelapses, { deep: true })

onMounted(() => {
  loadCameras()
  loadTimelapses()
})
</script>
