<template>
  <div class="flex items-center justify-between">
    <span class="text-sm text-dark-300">{{ label }}</span>
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
    unknown: 'badge bg-dark-600 text-dark-400',
    degraded: 'badge-warning',
  }
  return classes[props.status] || 'badge bg-dark-600 text-dark-400'
})
</script>
