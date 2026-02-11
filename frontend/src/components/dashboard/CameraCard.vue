<template>
  <router-link
    :to="`/cameras/${camera.id}`"
    class="flex rounded-lg border hover:border-primary-500/50 transition-colors shadow-sm overflow-hidden"
    style="background-color: var(--color-surface); border-color: var(--color-border);"
  >
    <!-- Thumbnail preview (small) -->
    <div class="w-20 h-16 relative flex-shrink-0" style="background-color: var(--color-bg-secondary);">
      <img
        :src="`/api/cameras/${camera.id}/preview?t=${refreshKey}`"
        class="w-full h-full object-cover"
        @error="imageError = true"
        @load="imageError = false"
      />
      <div
        v-if="imageError"
        class="absolute inset-0 flex items-center justify-center"
        style="color: var(--color-text-muted);"
      >
        <VideoCameraIcon class="w-5 h-5" />
      </div>
    </div>
    <!-- Camera info -->
    <div class="p-2 flex-1 min-w-0">
      <div class="flex items-center justify-between mb-0.5">
        <h3 class="font-medium truncate text-sm" style="color: var(--color-text-primary);">{{ camera.name }}</h3>
        <span :class="statusClass" class="text-xs ml-2 flex-shrink-0">
          <span class="w-1.5 h-1.5 rounded-full mr-1" :class="statusDotClass"></span>
          {{ statusText }}
        </span>
      </div>
      <div class="text-xs" style="color: var(--color-text-muted);">
        <p class="truncate">{{ camera.hostname || camera.ip_address }}</p>
        <p v-if="camera.last_capture_at">
          {{ formatTime(camera.last_capture_at) }}
        </p>
        <p v-else style="color: var(--color-text-muted);">No captures yet</p>
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
