<template>
  <div class="card p-6">
    <div class="flex items-center">
      <div :class="['p-3 rounded-lg', bgClass]">
        <component :is="iconComponent" :class="['w-6 h-6', iconColorClass]" />
      </div>
      <div class="ml-4">
        <p class="text-sm font-medium text-dark-400">{{ title }}</p>
        <p class="text-2xl font-bold text-white">{{ value }}</p>
        <p v-if="subtitle" class="text-xs text-dark-500">{{ subtitle }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  VideoCameraIcon,
  PhotoIcon,
  FilmIcon,
  ServerIcon,
} from '@heroicons/vue/24/outline'

const props = defineProps({
  title: String,
  value: [String, Number],
  subtitle: String,
  icon: {
    type: String,
    default: 'camera',
  },
  color: {
    type: String,
    default: 'primary',
  },
})

const iconComponent = computed(() => {
  const icons = {
    camera: VideoCameraIcon,
    photo: PhotoIcon,
    film: FilmIcon,
    server: ServerIcon,
  }
  return icons[props.icon] || VideoCameraIcon
})

const bgClass = computed(() => {
  const colors = {
    primary: 'bg-primary-500/20',
    green: 'bg-green-500/20',
    purple: 'bg-purple-500/20',
    yellow: 'bg-yellow-500/20',
    red: 'bg-red-500/20',
  }
  return colors[props.color] || 'bg-primary-500/20'
})

const iconColorClass = computed(() => {
  const colors = {
    primary: 'text-primary-400',
    green: 'text-green-400',
    purple: 'text-purple-400',
    yellow: 'text-yellow-400',
    red: 'text-red-400',
  }
  return colors[props.color] || 'text-primary-400'
})
</script>
