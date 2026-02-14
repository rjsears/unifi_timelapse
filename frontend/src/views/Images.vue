<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold" style="color: var(--color-text-primary);">Images</h1>
        <p style="color: var(--color-text-muted);">Browse captured images</p>
      </div>
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
        <input v-model="filters.date" type="date" class="input w-auto" />
        <label class="flex items-center" style="color: var(--color-text-secondary);">
          <input v-model="filters.protected" type="checkbox" class="mr-2" />
          Protected only
        </label>
      </div>
    </div>

    <!-- Image grid -->
    <div class="card">
      <div v-if="loading" class="flex justify-center py-12">
        <div class="spinner w-8 h-8"></div>
      </div>
      <div v-else-if="images.length === 0" class="text-center py-12">
        <PhotoIcon class="w-12 h-12 mx-auto" style="color: var(--color-text-muted);" />
        <h3 class="mt-4 text-lg font-medium" style="color: var(--color-text-primary);">No images found</h3>
        <p class="mt-2" style="color: var(--color-text-muted);">Adjust your filters or wait for new captures.</p>
      </div>
      <div v-else class="p-4">
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <div
            v-for="image in images"
            :key="image.id"
            class="relative group cursor-pointer"
            @click="openImage(image)"
          >
            <div class="aspect-video rounded-lg overflow-hidden" style="background-color: var(--color-bg-secondary);">
              <img
                :src="getImageSrc(image)"
                :key="imageRetryKeys[image.id] || 0"
                loading="lazy"
                class="w-full h-full object-cover transition-transform group-hover:scale-105"
                @error="handleImageError(image)"
              />
            </div>
            <!-- Protected indicator -->
            <div
              v-if="image.is_protected"
              class="absolute top-2 right-2 bg-yellow-500/80 p-1 rounded"
              title="Protected"
            >
              <ShieldCheckIcon class="w-4 h-4 text-white" />
            </div>
            <!-- Hover overlay -->
            <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
              <MagnifyingGlassPlusIcon class="w-8 h-8 text-white" />
            </div>
            <!-- Time -->
            <div class="mt-1 text-xs truncate" style="color: var(--color-text-muted);">
              {{ formatTime(image.captured_at) }}
            </div>
          </div>
        </div>

        <!-- Pagination -->
        <div class="mt-6 flex items-center justify-between">
          <p class="text-sm" style="color: var(--color-text-muted);">
            Showing {{ images.length }} of {{ total }} images
          </p>
          <div class="flex space-x-2">
            <button
              class="btn-secondary"
              :disabled="page === 1"
              @click="page--"
            >
              Previous
            </button>
            <button
              class="btn-secondary"
              :disabled="images.length < perPage"
              @click="page++"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Image viewer modal -->
    <Modal v-model="showViewer" size="full">
      <template #header>
        <div class="flex items-center justify-between w-full">
          <div>
            <h3 class="text-lg font-semibold" style="color: var(--color-text-primary);">{{ selectedImage?.camera_name }}</h3>
            <p class="text-sm" style="color: var(--color-text-muted);">{{ formatDateTime(selectedImage?.captured_at) }}</p>
          </div>
          <div class="flex items-center space-x-2">
            <button
              class="btn-secondary text-xs"
              :class="{ 'bg-yellow-500/20': selectedImage?.is_protected }"
              @click="toggleProtection"
            >
              <ShieldCheckIcon class="w-4 h-4 mr-1" />
              {{ selectedImage?.is_protected ? 'Unprotect' : 'Protect' }}
            </button>
            <button class="btn-secondary text-xs" @click="downloadImage">
              <ArrowDownTrayIcon class="w-4 h-4 mr-1" />
              Download
            </button>
            <button class="btn-secondary text-xs text-red-500" @click="confirmDeleteImage">
              <TrashIcon class="w-4 h-4" />
            </button>
          </div>
        </div>
      </template>
      <div class="flex items-center justify-center rounded-lg" style="height: 70vh; background-color: var(--color-bg-secondary);">
        <img
          v-if="selectedImage"
          :src="`/api/images/${selectedImage.id}/full`"
          class="max-w-full max-h-full object-contain"
        />
      </div>
      <div class="mt-4 flex items-center justify-between">
        <button
          class="btn-secondary"
          :disabled="currentIndex === 0"
          @click="navigateImage(-1)"
        >
          Previous
        </button>
        <span style="color: var(--color-text-muted);">{{ currentIndex + 1 }} of {{ images.length }}</span>
        <button
          class="btn-secondary"
          :disabled="currentIndex >= images.length - 1"
          @click="navigateImage(1)"
        >
          Next
        </button>
      </div>
    </Modal>

    <!-- Delete confirmation -->
    <Modal v-model="showDeleteModal" title="Delete Image" size="sm">
      <p style="color: var(--color-text-secondary);">Are you sure you want to delete this image?</p>
      <div class="flex justify-end space-x-3 pt-6">
        <button class="btn-secondary" @click="showDeleteModal = false">Cancel</button>
        <button class="btn-danger" @click="deleteImage">Delete</button>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { format } from 'date-fns'
import api from '@/api'
import { useNotificationsStore } from '@/stores/notifications'
import Modal from '@/components/ui/Modal.vue'
import {
  PhotoIcon,
  ShieldCheckIcon,
  MagnifyingGlassPlusIcon,
  ArrowDownTrayIcon,
  TrashIcon,
} from '@heroicons/vue/24/outline'

const route = useRoute()
const notifications = useNotificationsStore()

const loading = ref(false)
const images = ref([])
const cameras = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 48

const showViewer = ref(false)
const showDeleteModal = ref(false)
const selectedImage = ref(null)
const currentIndex = ref(0)

const filters = ref({
  camera: route.query.camera || '',
  date: format(new Date(), 'yyyy-MM-dd'),
  protected: false,
})

// Track image retry keys for failed loads
const imageRetryKeys = ref({})
const imageRetryCount = ref({})
const MAX_RETRIES = 2

async function loadImages() {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.value.camera) params.append('camera_id', filters.value.camera)
    if (filters.value.date) params.append('date', filters.value.date)
    if (filters.value.protected) params.append('is_protected', 'true')
    params.append('page', page.value.toString())
    params.append('limit', perPage.toString())

    const response = await api.get(`/images?${params}`)
    images.value = response.data.images || response.data
    total.value = response.data.total || images.value.length
    // Reset retry counters when loading new images
    imageRetryKeys.value = {}
    imageRetryCount.value = {}
  } catch (error) {
    notifications.error('Error', 'Failed to load images')
  } finally {
    loading.value = false
  }
}

async function loadCameras() {
  try {
    const response = await api.get('/cameras')
    cameras.value = response.data.cameras || []
  } catch (error) {
    console.error('Failed to load cameras:', error)
  }
}

function openImage(image) {
  selectedImage.value = image
  currentIndex.value = images.value.findIndex(i => i.id === image.id)
  showViewer.value = true
}

function navigateImage(direction) {
  const newIndex = currentIndex.value + direction
  if (newIndex >= 0 && newIndex < images.value.length) {
    currentIndex.value = newIndex
    selectedImage.value = images.value[newIndex]
  }
}

async function toggleProtection() {
  try {
    await api.post(`/images/${selectedImage.value.id}/protect`, {
      is_protected: !selectedImage.value.is_protected,
    })
    selectedImage.value.is_protected = !selectedImage.value.is_protected
    // Update in list too
    const idx = images.value.findIndex(i => i.id === selectedImage.value.id)
    if (idx !== -1) {
      images.value[idx].is_protected = selectedImage.value.is_protected
    }
    notifications.success('Updated', selectedImage.value.is_protected ? 'Image protected' : 'Protection removed')
  } catch (error) {
    notifications.error('Error', 'Failed to update protection')
  }
}

function downloadImage() {
  window.open(`/api/images/${selectedImage.value.id}/download`, '_blank')
}

function confirmDeleteImage() {
  showDeleteModal.value = true
}

async function deleteImage() {
  try {
    await api.delete(`/images/${selectedImage.value.id}`)
    notifications.success('Deleted', 'Image deleted')
    showDeleteModal.value = false
    showViewer.value = false
    await loadImages()
  } catch (error) {
    notifications.error('Error', 'Failed to delete image')
  }
}

function formatTime(dateStr) {
  return format(new Date(dateStr), 'HH:mm:ss')
}

function getImageSrc(image) {
  const retryKey = imageRetryKeys.value[image.id] || 0
  // Add cache-busting param on retry
  return retryKey > 0
    ? `/api/images/${image.id}/thumbnail?retry=${retryKey}`
    : `/api/images/${image.id}/thumbnail`
}

function handleImageError(image) {
  const currentRetries = imageRetryCount.value[image.id] || 0
  if (currentRetries < MAX_RETRIES) {
    // Schedule retry after a short delay
    setTimeout(() => {
      imageRetryCount.value[image.id] = currentRetries + 1
      imageRetryKeys.value[image.id] = (imageRetryKeys.value[image.id] || 0) + 1
    }, 500 * (currentRetries + 1)) // Exponential backoff: 500ms, 1000ms
  }
}

function formatDateTime(dateStr) {
  if (!dateStr) return ''
  return format(new Date(dateStr), 'MMM d, yyyy HH:mm:ss')
}

watch([filters, page], loadImages, { deep: true })

onMounted(() => {
  loadCameras()
  loadImages()
})
</script>
