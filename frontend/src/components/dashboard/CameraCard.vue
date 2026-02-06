<template>
  <router-link
    :to="`/cameras/${camera.id}`"
    class="block p-4 bg-dark-700/50 rounded-lg border border-dark-600 hover:border-primary-500/50 transition-colors"
  >
    <div class="flex items-center justify-between mb-2">
      <h3 class="font-medium text-white truncate">{{ camera.name }}</h3>
      <span :class="statusClass">
        <span class="w-2 h-2 rounded-full mr-1.5" :class="statusDotClass"></span>
        {{ statusText }}
      </span>
    </div>
    <div class="text-sm text-dark-400 space-y-1">
      <p>{{ camera.hostname || camera.ip_address }}</p>
      <p v-if="camera.last_capture_at">
        Last capture: {{ formatTime(camera.last_capture_at) }}
      </p>
      <p v-else class="text-dark-500">No captures yet</p>
    </div>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'
import { formatDistanceToNow } from 'date-fns'

const props = defineProps({
  camera: {
    type: Object,
    required: true,
  },
})

const statusClass = computed(() => {
  if (!props.camera.is_active) return 'badge bg-dark-600 text-dark-400'
  if (props.camera.consecutive_errors > 0) return 'badge-danger'
  return 'badge-success'
})

const statusDotClass = computed(() => {
  if (!props.camera.is_active) return 'bg-dark-500'
  if (props.camera.consecutive_errors > 0) return 'bg-red-400'
  return 'bg-green-400'
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
