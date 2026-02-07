<template>
  <div>
    <!-- Mobile sidebar backdrop -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-40 bg-gray-900/50 lg:hidden"
      @click="sidebarOpen = false"
    ></div>

    <!-- Sidebar -->
    <div
      :class="[
        'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 lg:translate-x-0',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full',
      ]"
    >
      <!-- Logo -->
      <div class="flex items-center h-16 px-6 border-b border-gray-200">
        <span class="text-xl font-bold text-primary-600">UniFi Timelapse</span>
      </div>

      <!-- Navigation -->
      <nav class="px-4 py-6 space-y-1">
        <router-link
          v-for="item in navigation"
          :key="item.name"
          :to="item.to"
          :class="[
            'flex items-center px-4 py-2.5 rounded-lg transition-colors',
            isActive(item.to)
              ? 'bg-primary-600 text-white'
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
          ]"
          @click="sidebarOpen = false"
        >
          <component :is="item.icon" class="w-5 h-5 mr-3" />
          {{ item.name }}
        </router-link>
      </nav>

      <!-- Storage indicator -->
      <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
        <div class="text-xs text-gray-500 mb-2">Storage Usage</div>
        <div class="w-full bg-gray-200 rounded-full h-2">
          <div
            class="h-2 rounded-full transition-all duration-300"
            :class="storageClass"
            :style="{ width: `${storagePercent}%` }"
          ></div>
        </div>
        <div class="text-xs text-gray-500 mt-1">
          {{ storagePercent.toFixed(1) }}% used
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSystemStore } from '@/stores/system'
import {
  HomeIcon,
  VideoCameraIcon,
  FilmIcon,
  PhotoIcon,
  HeartIcon,
  CogIcon,
} from '@heroicons/vue/24/outline'

const route = useRoute()
const systemStore = useSystemStore()
const sidebarOpen = ref(false)

const navigation = [
  { name: 'Dashboard', to: '/', icon: HomeIcon },
  { name: 'Cameras', to: '/cameras', icon: VideoCameraIcon },
  { name: 'Timelapses', to: '/timelapses', icon: FilmIcon },
  { name: 'Images', to: '/images', icon: PhotoIcon },
  { name: 'Health', to: '/health', icon: HeartIcon },
  { name: 'Settings', to: '/settings', icon: CogIcon },
]

const storagePercent = computed(() => {
  return systemStore.storageInfo?.percent_used || 0
})

const storageClass = computed(() => {
  const percent = storagePercent.value
  if (percent >= 90) return 'bg-red-500'
  if (percent >= 75) return 'bg-yellow-500'
  return 'bg-primary-500'
})

function isActive(path) {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

onMounted(() => {
  systemStore.fetchStorageInfo()
})

// Expose sidebarOpen for mobile toggle
defineExpose({ sidebarOpen })
</script>
