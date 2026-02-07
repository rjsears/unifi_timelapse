<template>
  <div class="min-h-screen bg-gray-50">
    <template v-if="authStore.isAuthenticated">
      <Sidebar />
      <div class="lg:pl-64">
        <Header />
        <main class="p-6">
          <router-view v-slot="{ Component }">
            <transition name="page" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </main>
      </div>
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
import Sidebar from '@/components/layout/Sidebar.vue'
import Header from '@/components/layout/Header.vue'
import Notifications from '@/components/ui/Notifications.vue'

const authStore = useAuthStore()

onMounted(async () => {
  await authStore.checkAuth()
})
</script>
