<template>
  <div :class="themeStore.themeClasses" class="min-h-screen">
    <template v-if="authStore.isAuthenticated">
      <TopNav>
        <router-view v-slot="{ Component }">
          <transition name="page" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </TopNav>
    </template>
    <template v-else>
      <router-view />
    </template>

    <!-- Toast notifications -->
    <Notifications />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/stores/theme'
import TopNav from '@/components/layout/TopNav.vue'
import Notifications from '@/components/ui/Notifications.vue'

const authStore = useAuthStore()
const themeStore = useThemeStore()

onMounted(async () => {
  // Initialize theme
  themeStore.init()

  // Check authentication
  await authStore.checkAuth()
})
</script>
