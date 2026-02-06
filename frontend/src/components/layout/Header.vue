<template>
  <header class="sticky top-0 z-30 bg-dark-800 border-b border-dark-700">
    <div class="flex items-center justify-between h-16 px-6">
      <!-- Mobile menu button -->
      <button
        class="lg:hidden p-2 text-dark-400 hover:text-white rounded-lg"
        @click="toggleSidebar"
      >
        <Bars3Icon class="w-6 h-6" />
      </button>

      <!-- Page title -->
      <h1 class="text-lg font-semibold text-white lg:pl-0">
        {{ pageTitle }}
      </h1>

      <!-- Right section -->
      <div class="flex items-center space-x-4">
        <!-- System status -->
        <div class="hidden sm:flex items-center space-x-2 text-sm">
          <span :class="statusClass" class="w-2 h-2 rounded-full"></span>
          <span class="text-dark-400">{{ statusText }}</span>
        </div>

        <!-- User menu -->
        <div class="relative">
          <button
            class="flex items-center space-x-2 p-2 rounded-lg hover:bg-dark-700 transition-colors"
            @click="showUserMenu = !showUserMenu"
          >
            <div class="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
              <span class="text-sm font-medium text-white">
                {{ userInitial }}
              </span>
            </div>
            <ChevronDownIcon class="w-4 h-4 text-dark-400" />
          </button>

          <!-- Dropdown menu -->
          <transition
            enter-active-class="transition ease-out duration-100"
            enter-from-class="transform opacity-0 scale-95"
            enter-to-class="transform opacity-100 scale-100"
            leave-active-class="transition ease-in duration-75"
            leave-from-class="transform opacity-100 scale-100"
            leave-to-class="transform opacity-0 scale-95"
          >
            <div
              v-if="showUserMenu"
              class="absolute right-0 mt-2 w-48 bg-dark-700 rounded-lg shadow-lg border border-dark-600 py-1"
            >
              <div class="px-4 py-2 border-b border-dark-600">
                <p class="text-sm font-medium text-white">{{ authStore.user?.username }}</p>
                <p class="text-xs text-dark-400">
                  {{ authStore.isAdmin ? 'Administrator' : 'User' }}
                </p>
              </div>
              <button
                class="w-full text-left px-4 py-2 text-sm text-dark-200 hover:bg-dark-600"
                @click="handleChangePassword"
              >
                Change Password
              </button>
              <button
                class="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-dark-600"
                @click="handleLogout"
              >
                Sign Out
              </button>
            </div>
          </transition>
        </div>
      </div>
    </div>
  </header>

  <!-- Change password modal -->
  <Modal v-model="showPasswordModal" title="Change Password">
    <form @submit.prevent="submitPasswordChange" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-dark-300 mb-1">
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
        <label class="block text-sm font-medium text-dark-300 mb-1">
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
        <label class="block text-sm font-medium text-dark-300 mb-1">
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
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSystemStore } from '@/stores/system'
import { useNotificationsStore } from '@/stores/notifications'
import Modal from '@/components/ui/Modal.vue'
import {
  Bars3Icon,
  ChevronDownIcon,
} from '@heroicons/vue/24/outline'

const route = useRoute()
const authStore = useAuthStore()
const systemStore = useSystemStore()
const notifications = useNotificationsStore()

const showUserMenu = ref(false)
const showPasswordModal = ref(false)
const passwordForm = ref({
  current: '',
  new: '',
  confirm: '',
})

const pageTitle = computed(() => {
  return route.name || 'Dashboard'
})

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

function toggleSidebar() {
  // Emit to parent to toggle sidebar
  const sidebar = document.querySelector('[data-sidebar]')
  if (sidebar) {
    sidebar.classList.toggle('-translate-x-full')
  }
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
