<template>
  <router-link
    :to="`/cameras/${camera.id}`"
    class="block bg-white rounded-lg border border-gray-200 hover:border-primary-500/50 transition-colors shadow-sm overflow-hidden"
  >
    <!-- Thumbnail preview -->
    <div class="aspect-video bg-gray-100 relative">
      <img
        :src="`/api/cameras/${camera.id}/preview?t=${refreshKey}`"
        class="w-full h-full object-cover"
        @error="imageError = true"
        @load="imageError = false"
      />
      <div
        v-if="imageError"
        class="absolute inset-0 flex items-center justify-center text-gray-400"
      >
        <VideoCameraIcon class="w-8 h-8" />
      </div>
    </div>
    <!-- Camera info -->
    <div class="p-3">
      <div class="flex items-center justify-between mb-1">
        <h3 class="font-medium text-gray-900 truncate text-sm">{{ camera.name }}</h3>
        <span :class="statusClass" class="text-xs">
          <span class="w-1.5 h-1.5 rounded-full mr-1" :class="statusDotClass"></span>
          {{ statusText }}
        </span>
      </div>
      <div class="text-xs text-gray-500 space-y-0.5">
        <p>{{ camera.hostname || camera.ip_address }}</p>
        <p v-if="camera.last_capture_at">
          {{ formatTime(camera.last_capture_at) }}
        </p>
        <p v-else class="text-gray-400">No captures yet</p>
      </div>
    </div>
  </router-link>
</template>

<script setup>
import { computed, ref } from 'vue'
import { formatDistanceToNow } from 'date-fns'
import { VideoCameraIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  camera: {
    type: Object,
    required: true,
  },
})

const imageError = ref(false)
const refreshKey = ref(Date.now())

const statusClass = computed(() => {
  if (!props.camera.is_active) return 'badge bg-gray-200 text-gray-500'
  if (props.camera.consecutive_errors > 0) return 'badge-danger'
  return 'badge-success'
})

const statusDotClass = computed(() => {
  if (!props.camera.is_active) return 'bg-gray-400'
  if (props.camera.consecutive_errors > 0) return 'bg-red-500'
  return 'bg-green-500'
})

const statusText = computed(() => {
  if (!props.camera.is_active) return 'Inactive'
  if (props.camera.consecutive_errors > 0) return 'Error'
  return 'Active'
})

function formatTime(dateStr) {
  return formatDistanceToNow(new Date(dateStr), { addSuffix: true })
}
</script>
