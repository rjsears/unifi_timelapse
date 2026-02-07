<template>
  <router-link
    :to="`/cameras/${camera.id}`"
    class="block p-4 bg-white rounded-lg border border-gray-200 hover:border-primary-500/50 transition-colors shadow-sm"
  >
    <div class="flex items-center justify-between mb-2">
      <h3 class="font-medium text-gray-900 truncate">{{ camera.name }}</h3>
      <span :class="statusClass">
        <span class="w-2 h-2 rounded-full mr-1.5" :class="statusDotClass"></span>
        {{ statusText }}
      </span>
    </div>
    <div class="text-sm text-gray-500 space-y-1">
      <p>{{ camera.hostname || camera.ip_address }}</p>
      <p v-if="camera.last_capture_at">
        Last capture: {{ formatTime(camera.last_capture_at) }}
      </p>
      <p v-else class="text-gray-400">No captures yet</p>
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
