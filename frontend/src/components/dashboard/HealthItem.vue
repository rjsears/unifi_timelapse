<template>
  <div class="flex items-center justify-between">
    <span class="text-sm text-gray-700">{{ label }}</span>
    <span :class="badgeClass">
      {{ displayStatus }}
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: String,
  status: {
    type: String,
    default: 'unknown',
  },
})

const displayStatus = computed(() => {
  const statusMap = {
    healthy: 'Healthy',
    warning: 'Warning',
    critical: 'Critical',
    unknown: 'Unknown',
    degraded: 'Degraded',
  }
  return statusMap[props.status] || props.status
})

const badgeClass = computed(() => {
  const classes = {
    healthy: 'badge-success',
    warning: 'badge-warning',
    critical: 'badge-danger',
    unknown: 'badge bg-gray-200 text-gray-500',
    degraded: 'badge-warning',
  }
  return classes[props.status] || 'badge bg-gray-200 text-gray-500'
})
</script>
