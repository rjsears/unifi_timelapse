<template>
  <div class="min-h-screen bg-gray-50 dark:bg-dark-950">
    <!-- Top Navigation Bar -->
    <header class="sticky top-0 z-50 border-b border-gray-200 dark:border-dark-700 bg-white dark:bg-dark-900 backdrop-blur-sm bg-opacity-95 dark:bg-opacity-95">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="flex h-16 items-center justify-between">
          <!-- Logo -->
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <span class="text-xl font-bold text-primary-600 dark:text-primary-400">UniFi</span>
              <span class="text-xl font-light text-gray-600 dark:text-gray-400 ml-1">Timelapse</span>
            </div>
          </div>

          <!-- Navigation -->
          <nav class="hidden md:flex items-center space-x-1">
            <router-link
              v-for="item in navItems"
              :key="item.route"
              :to="item.to"
              :class="[
                'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                isActive(item.to)
                  ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-dark-800'
              ]"
            >
              <component :is="item.icon" class="h-5 w-5 mr-1.5" />
              {{ item.name }}
            </router-link>
          </nav>

          <!-- Right side -->
          <div class="flex items-center space-x-3">
            <!-- System status indicator -->
            <div class="hidden sm:flex items-center space-x-2 text-sm">
              <span :class="statusClass" class="w-2 h-2 rounded-full"></span>
              <span class="text-gray-500 dark:text-gray-400">{{ statusText }}</span>
            </div>

            <!-- About button -->
            <button
              @click="showAbout = true"
              class="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-dark-800 transition-colors"
              title="About"
            >
              <InformationCircleIcon class="h-5 w-5" />
            </button>

            <!-- Theme toggle -->
            <button
              @click="themeStore.toggleColorMode"
              class="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-dark-800 transition-colors"
              :title="themeTitle"
            >
              <SunIcon v-if="themeStore.isDark" class="h-5 w-5" />
              <MoonIcon v-else class="h-5 w-5" />
            </button>

            <!-- User menu -->
            <div class="relative">
              <button
                class="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-dark-800 transition-colors"
                @click="showUserMenu = !showUserMenu"
              >
                <div class="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                  <span class="text-sm font-medium text-white">
                    {{ userInitial }}
                  </span>
                </div>
                <ChevronDownIcon class="w-4 h-4 text-gray-500 dark:text-gray-400" />
              </button>

              <!-- Dropdown menu -->
              <Transition
                enter-active-class="transition ease-out duration-100"
                enter-from-class="transform opacity-0 scale-95"
                enter-to-class="transform opacity-100 scale-100"
                leave-active-class="transition ease-in duration-75"
                leave-from-class="transform opacity-100 scale-100"
                leave-to-class="transform opacity-0 scale-95"
              >
                <div
                  v-if="showUserMenu"
                  class="absolute right-0 mt-2 w-48 bg-white dark:bg-dark-800 rounded-lg shadow-lg border border-gray-200 dark:border-dark-700 py-1"
                >
                  <div class="px-4 py-2 border-b border-gray-200 dark:border-dark-700">
                    <p class="text-sm font-medium text-gray-900 dark:text-white">{{ authStore.user?.username }}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">
                      {{ authStore.isAdmin ? 'Administrator' : 'User' }}
                    </p>
                  </div>
                  <button
                    class="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-700"
                    @click="handleChangePassword"
                  >
                    Change Password
                  </button>
                  <button
                    class="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-dark-700"
                    @click="handleLogout"
                  >
                    Sign Out
                  </button>
                </div>
              </Transition>
            </div>

            <!-- Mobile menu button -->
            <button
              class="md:hidden p-2 text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white rounded-lg"
              @click="mobileMenuOpen = !mobileMenuOpen"
            >
              <Bars3Icon v-if="!mobileMenuOpen" class="w-6 h-6" />
              <XMarkIcon v-else class="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>

      <!-- Mobile menu -->
      <Transition
        enter-active-class="transition ease-out duration-200"
        enter-from-class="opacity-0 -translate-y-1"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition ease-in duration-150"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-1"
      >
        <div v-if="mobileMenuOpen" class="md:hidden border-t border-gray-200 dark:border-dark-700 bg-white dark:bg-dark-900">
          <nav class="px-4 py-3 space-y-1">
            <router-link
              v-for="item in navItems"
              :key="item.route"
              :to="item.to"
              :class="[
                'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                isActive(item.to)
                  ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-dark-800'
              ]"
              @click="mobileMenuOpen = false"
            >
              <component :is="item.icon" class="h-5 w-5 mr-2" />
              {{ item.name }}
            </router-link>
          </nav>
        </div>
      </Transition>
    </header>

    <!-- Main Content -->
    <main class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
      <slot />
    </main>

    <!-- About Dialog -->
    <AboutDialog :open="showAbout" @close="showAbout = false" />

    <!-- Change Password Modal -->
    <Modal v-model="showPasswordModal" title="Change Password">
      <form @submit.prevent="submitPasswordChange" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Current Password
          </label>
          <input
            v-model="passwordForm.current"
            type="password"
            class="input"
            required
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            New Password
          </label>
          <input
            v-model="passwordForm.new"
            type="password"
            class="input"
            required
            minlength="8"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Confirm New Password
          </label>
          <input
            v-model="passwordForm.confirm"
            type="password"
            class="input"
            required
          />
        </div>
        <div class="flex justify-end space-x-3 pt-4">
          <button
            type="button"
            class="btn-secondary"
            @click="showPasswordModal = false"
          >
            Cancel
          </button>
          <button type="submit" class="btn-primary">
            Change Password
          </button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSystemStore } from '@/stores/system'
import { useThemeStore } from '@/stores/theme'
import { useNotificationsStore } from '@/stores/notifications'
import AboutDialog from '@/components/ui/AboutDialog.vue'
import Modal from '@/components/ui/Modal.vue'
import {
  HomeIcon,
  VideoCameraIcon,
  FilmIcon,
  PhotoIcon,
  HeartIcon,
  CogIcon,
  SunIcon,
  MoonIcon,
  InformationCircleIcon,
  Bars3Icon,
  XMarkIcon,
  ChevronDownIcon,
} from '@heroicons/vue/24/outline'

const route = useRoute()
const authStore = useAuthStore()
const systemStore = useSystemStore()
const themeStore = useThemeStore()
const notifications = useNotificationsStore()

const showAbout = ref(false)
const showUserMenu = ref(false)
const showPasswordModal = ref(false)
const mobileMenuOpen = ref(false)
const passwordForm = ref({
  current: '',
  new: '',
  confirm: '',
})

const navItems = [
  { name: 'Dashboard', to: '/', icon: HomeIcon },
  { name: 'Cameras', to: '/cameras', icon: VideoCameraIcon },
  { name: 'Timelapses', to: '/timelapses', icon: FilmIcon },
  { name: 'Images', to: '/images', icon: PhotoIcon },
  { name: 'Health', to: '/health', icon: HeartIcon },
  { name: 'Settings', to: '/settings', icon: CogIcon },
]

const userInitial = computed(() => {
  return authStore.user?.username?.charAt(0).toUpperCase() || 'U'
})

const statusClass = computed(() => {
  return systemStore.systemInfo?.status === 'healthy'
    ? 'bg-green-500'
    : 'bg-yellow-500'
})

const statusText = computed(() => {
  return systemStore.systemInfo?.status === 'healthy' ? 'Healthy' : 'Degraded'
})

const themeTitle = computed(() => {
  if (themeStore.colorMode === 'dark') return 'Switch to Light Mode'
  if (themeStore.colorMode === 'light') return 'Switch to System Theme'
  return 'Switch to Dark Mode'
})

function isActive(path) {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

function handleChangePassword() {
  showUserMenu.value = false
  showPasswordModal.value = true
}

async function submitPasswordChange() {
  if (passwordForm.value.new !== passwordForm.value.confirm) {
    notifications.error('Error', 'New passwords do not match')
    return
  }

  const result = await authStore.changePassword(
    passwordForm.value.current,
    passwordForm.value.new
  )

  if (result.success) {
    notifications.success('Success', 'Password changed successfully')
    showPasswordModal.value = false
    passwordForm.value = { current: '', new: '', confirm: '' }
  } else {
    notifications.error('Error', result.error)
  }
}

function handleLogout() {
  showUserMenu.value = false
  authStore.logout()
}

// Close menu when clicking outside
function handleClickOutside(event) {
  if (!event.target.closest('.relative')) {
    showUserMenu.value = false
  }
}

onMounted(() => {
  systemStore.fetchSystemInfo()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
