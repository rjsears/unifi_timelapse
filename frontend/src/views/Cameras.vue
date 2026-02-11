<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold" style="color: var(--color-text-primary);">Cameras</h1>
        <p style="color: var(--color-text-muted);">Manage your camera configurations</p>
      </div>
      <button class="btn-primary" @click="showAddModal = true">
        <PlusIcon class="w-5 h-5 mr-2" />
        Add Camera
      </button>
    </div>

    <!-- Camera list -->
    <div class="card">
      <div v-if="camerasStore.loading" class="flex justify-center py-12">
        <div class="spinner w-8 h-8"></div>
      </div>
      <div v-else-if="camerasStore.cameras.length === 0" class="text-center py-12">
        <VideoCameraIcon class="w-12 h-12 mx-auto" style="color: var(--color-text-muted);" />
        <h3 class="mt-4 text-lg font-medium" style="color: var(--color-text-primary);">No cameras configured</h3>
        <p class="mt-2" style="color: var(--color-text-muted);">Get started by adding your first camera.</p>
        <button class="btn-primary mt-4" @click="showAddModal = true">
          Add Camera
        </button>
      </div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Host</th>
            <th>Interval</th>
            <th>Last Capture</th>
            <th>Status</th>
            <th class="text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="camera in camerasStore.cameras" :key="camera.id">
            <td>
              <router-link
                :to="`/cameras/${camera.id}`"
                class="font-medium text-primary-600 hover:text-primary-500"
              >
                {{ camera.name }}
              </router-link>
            </td>
            <td style="color: var(--color-text-secondary);">
              {{ camera.hostname || camera.ip_address }}
            </td>
            <td style="color: var(--color-text-secondary);">
              {{ camera.capture_interval }}s
            </td>
            <td style="color: var(--color-text-secondary);">
              <span v-if="camera.last_capture_at">
                {{ formatTime(camera.last_capture_at) }}
              </span>
              <span v-else style="color: var(--color-text-muted);">Never</span>
            </td>
            <td>
              <span :class="getStatusClass(camera)">
                {{ getStatusText(camera) }}
              </span>
            </td>
            <td class="text-right">
              <div class="flex items-center justify-end space-x-2">
                <button
                  class="p-2 rounded hover:opacity-80" style="color: var(--color-text-muted);"
                  title="Test connection"
                  @click="testCamera(camera)"
                >
                  <SignalIcon class="w-4 h-4" />
                </button>
                <button
                  class="p-2 rounded hover:opacity-80" style="color: var(--color-text-muted);"
                  title="Capture now"
                  @click="captureNow(camera)"
                >
                  <CameraIcon class="w-4 h-4" />
                </button>
                <button
                  class="p-2 rounded hover:opacity-80" style="color: var(--color-text-muted);"
                  title="Edit"
                  @click="editCamera(camera)"
                >
                  <PencilIcon class="w-4 h-4" />
                </button>
                <button
                  class="p-2 rounded hover:text-red-500" style="color: var(--color-text-muted);"
                  title="Delete"
                  @click="confirmDelete(camera)"
                >
                  <TrashIcon class="w-4 h-4" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add/Edit Modal -->
    <Modal v-model="showAddModal" :title="editingCamera ? 'Edit Camera' : 'Add Camera'" size="lg">
      <form @submit.prevent="saveCamera" class="space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div class="col-span-2">
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Name</label>
            <input v-model="cameraForm.name" type="text" class="input" required />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Hostname</label>
            <input v-model="cameraForm.hostname" type="text" class="input" placeholder="camera.local" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">IP Address</label>
            <input v-model="cameraForm.ip_address" type="text" class="input" placeholder="192.168.1.100" />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Capture Interval (seconds)</label>
            <input v-model.number="cameraForm.capture_interval" type="number" min="10" max="3600" class="input" />
          </div>
          <div class="flex items-center space-x-4">
            <label class="flex items-center">
              <input v-model="cameraForm.is_active" type="checkbox" class="mr-2" />
              <span class="text-sm" style="color: var(--color-text-secondary);">Active</span>
            </label>
            <label class="flex items-center">
              <input v-model="cameraForm.timelapse_enabled" type="checkbox" class="mr-2" />
              <span class="text-sm" style="color: var(--color-text-secondary);">Timelapse Enabled</span>
            </label>
          </div>
        </div>

        <!-- Blackout Period -->
        <div class="border-t pt-4" style="border-color: var(--color-border);">
          <h4 class="text-sm font-medium mb-3" style="color: var(--color-text-primary);">Blackout Period</h4>
          <p class="text-xs mb-3" style="color: var(--color-text-muted);">Skip image capture during this time window (e.g., nighttime)</p>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Start Time</label>
              <input
                v-model="cameraForm.blackout_start"
                type="time"
                class="input"
                placeholder="22:00"
              />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">End Time</label>
              <input
                v-model="cameraForm.blackout_end"
                type="time"
                class="input"
                placeholder="06:00"
              />
            </div>
          </div>
          <p class="text-xs mt-2" style="color: var(--color-text-muted);">Leave both empty to capture 24/7. Supports overnight periods (e.g., 22:00 to 06:00).</p>
        </div>

        <div class="flex justify-end space-x-3 pt-4">
          <button type="button" class="btn-secondary" @click="showAddModal = false">
            Cancel
          </button>
          <button type="submit" class="btn-primary">
            {{ editingCamera ? 'Save Changes' : 'Add Camera' }}
          </button>
        </div>
      </form>
    </Modal>

    <!-- Delete confirmation -->
    <Modal v-model="showDeleteModal" title="Delete Camera" size="sm">
      <p style="color: var(--color-text-secondary);">
        Are you sure you want to delete <strong style="color: var(--color-text-primary);">{{ cameraToDelete?.name }}</strong>?
        This will also delete all associated images and timelapses.
      </p>
      <div class="flex justify-end space-x-3 pt-6">
        <button class="btn-secondary" @click="showDeleteModal = false">Cancel</button>
        <button class="btn-danger" @click="deleteCamera">Delete</button>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCamerasStore } from '@/stores/cameras'
import { useNotificationsStore } from '@/stores/notifications'
import { formatDistanceToNow } from 'date-fns'
import Modal from '@/components/ui/Modal.vue'
import {
  PlusIcon,
  VideoCameraIcon,
  SignalIcon,
  CameraIcon,
  PencilIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline'

const camerasStore = useCamerasStore()
const notifications = useNotificationsStore()

const showAddModal = ref(false)
const showDeleteModal = ref(false)
const editingCamera = ref(null)
const cameraToDelete = ref(null)

const cameraForm = ref({
  name: '',
  hostname: '',
  ip_address: '',
  capture_interval: 30,
  is_active: true,
  timelapse_enabled: true,
  blackout_start: '',
  blackout_end: '',
})

function resetForm() {
  cameraForm.value = {
    name: '',
    hostname: '',
    ip_address: '',
    capture_interval: 30,
    is_active: true,
    timelapse_enabled: true,
    blackout_start: '',
    blackout_end: '',
  }
  editingCamera.value = null
}

function editCamera(camera) {
  editingCamera.value = camera
  cameraForm.value = {
    ...camera,
    // Convert "HH:MM:SS" to "HH:MM" for time inputs
    blackout_start: camera.blackout_start ? camera.blackout_start.slice(0, 5) : '',
    blackout_end: camera.blackout_end ? camera.blackout_end.slice(0, 5) : '',
  }
  showAddModal.value = true
}

function confirmDelete(camera) {
  cameraToDelete.value = camera
  showDeleteModal.value = true
}

async function saveCamera() {
  const data = { ...cameraForm.value }
  // Convert empty blackout times to null for API
  if (!data.blackout_start) data.blackout_start = null
  if (!data.blackout_end) data.blackout_end = null

  if (editingCamera.value) {
    const result = await camerasStore.updateCamera(editingCamera.value.id, data)
    if (result.success) {
      notifications.success('Camera Updated', `${data.name} has been updated`)
      showAddModal.value = false
      resetForm()
    } else {
      notifications.error('Error', result.error)
    }
  } else {
    const result = await camerasStore.createCamera(data)
    if (result.success) {
      notifications.success('Camera Added', `${data.name} has been added`)
      showAddModal.value = false
      resetForm()
    } else {
      notifications.error('Error', result.error)
    }
  }
}

async function deleteCamera() {
  const result = await camerasStore.deleteCamera(cameraToDelete.value.id)
  if (result.success) {
    notifications.success('Camera Deleted', `${cameraToDelete.value.name} has been deleted`)
  } else {
    notifications.error('Error', result.error)
  }
  showDeleteModal.value = false
  cameraToDelete.value = null
}

async function testCamera(camera) {
  notifications.info('Testing...', `Testing connection to ${camera.name}`)
  const result = await camerasStore.testCamera(camera.id)
  if (result.success && result.result?.success) {
    notifications.success('Success', `${camera.name} is reachable (${result.result.response_time_ms}ms)`)
  } else {
    notifications.error('Failed', result.result?.error || result.error || 'Camera is not reachable')
  }
}

async function captureNow(camera) {
  notifications.info('Capturing...', `Capturing image from ${camera.name}`)
  const result = await camerasStore.captureNow(camera.id)
  if (result.success) {
    notifications.success('Captured', `Image captured from ${camera.name}`)
    await camerasStore.fetchCameras()
  } else {
    notifications.error('Failed', result.error)
  }
}

function formatTime(dateStr) {
  return formatDistanceToNow(new Date(dateStr), { addSuffix: true })
}

function getStatusClass(camera) {
  if (!camera.is_active) return 'badge bg-gray-200 text-gray-500'
  if (camera.consecutive_errors >= 3) return 'badge-danger'
  if (camera.consecutive_errors > 0) return 'badge-warning'
  return 'badge-success'
}

function getStatusText(camera) {
  if (!camera.is_active) return 'Inactive'
  if (camera.consecutive_errors >= 3) return 'Failing'
  if (camera.consecutive_errors > 0) return 'Warning'
  return 'Active'
}

onMounted(() => {
  camerasStore.fetchCameras()
})
</script>
