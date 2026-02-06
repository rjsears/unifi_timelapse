<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold text-white">Settings</h1>
      <p class="text-dark-400">System configuration and administration</p>
    </div>

    <!-- Tabs -->
    <div class="border-b border-dark-700">
      <nav class="flex space-x-8">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="[
            'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
            activeTab === tab.id
              ? 'border-primary-500 text-primary-400'
              : 'border-transparent text-dark-400 hover:text-white hover:border-dark-500',
          ]"
          @click="activeTab = tab.id"
        >
          {{ tab.name }}
        </button>
      </nav>
    </div>

    <!-- General Settings -->
    <div v-if="activeTab === 'general'" class="space-y-6">
      <div class="card">
        <div class="p-4 border-b border-dark-700">
          <h2 class="text-lg font-semibold text-white">Capture Settings</h2>
        </div>
        <div class="p-6 space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-dark-300 mb-1">
                Default Capture Interval (seconds)
              </label>
              <input
                v-model.number="settings.default_capture_interval"
                type="number"
                min="10"
                max="3600"
                class="input"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-dark-300 mb-1">
                Max Concurrent Captures
              </label>
              <input
                v-model.number="settings.max_concurrent_captures"
                type="number"
                min="1"
                max="200"
                class="input"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-dark-300 mb-1">
                Capture Timeout (seconds)
              </label>
              <input
                v-model.number="settings.capture_timeout"
                type="number"
                min="5"
                max="120"
                class="input"
              />
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="p-4 border-b border-dark-700">
          <h2 class="text-lg font-semibold text-white">Timelapse Settings</h2>
        </div>
        <div class="p-6 space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-dark-300 mb-1">
                Default Frame Rate
              </label>
              <input
                v-model.number="settings.default_frame_rate"
                type="number"
                min="1"
                max="120"
                class="input"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-dark-300 mb-1">
                Default CRF (Quality)
              </label>
              <input
                v-model.number="settings.default_crf"
                type="number"
                min="0"
                max="51"
                class="input"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-dark-300 mb-1">
                Daily Generation Time
              </label>
              <input
                v-model="settings.daily_timelapse_time"
                type="time"
                class="input"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-dark-300 mb-1">
                Pixel Format
              </label>
              <select v-model="settings.default_pixel_format" class="input">
                <option value="yuv420p">yuv420p (Recommended)</option>
                <option value="yuv444p">yuv444p (High Quality)</option>
                <option value="rgb24">rgb24</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="p-4 border-b border-dark-700">
          <h2 class="text-lg font-semibold text-white">Retention Settings</h2>
        </div>
        <div class="p-6 space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-dark-300 mb-1">
                Image Retention (days)
              </label>
              <input
                v-model.number="settings.retention_days_images"
                type="number"
                min="1"
                class="input"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-dark-300 mb-1">
                Video Retention (days)
              </label>
              <input
                v-model.number="settings.retention_days_videos"
                type="number"
                min="1"
                class="input"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-dark-300 mb-1">
                Cleanup Time
              </label>
              <input
                v-model="settings.cleanup_time"
                type="time"
                class="input"
              />
            </div>
            <div class="flex items-center">
              <label class="flex items-center">
                <input
                  v-model="settings.cleanup_after_timelapse"
                  type="checkbox"
                  class="mr-2"
                />
                <span class="text-dark-300">Delete images after timelapse</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div class="flex justify-end">
        <button class="btn-primary" @click="saveSettings">Save Settings</button>
      </div>
    </div>

    <!-- Notifications -->
    <div v-if="activeTab === 'notifications'" class="space-y-6">
      <div class="card">
        <div class="p-4 border-b border-dark-700 flex items-center justify-between">
          <h2 class="text-lg font-semibold text-white">Notification Channels</h2>
          <button class="btn-primary text-sm" @click="showAddNotification = true">
            Add Channel
          </button>
        </div>
        <div v-if="notificationConfigs.length === 0" class="p-6 text-center text-dark-400">
          No notification channels configured
        </div>
        <ul v-else class="divide-y divide-dark-700">
          <li
            v-for="config in notificationConfigs"
            :key="config.id"
            class="p-4 flex items-center justify-between"
          >
            <div>
              <p class="font-medium text-white">{{ config.name }}</p>
              <p class="text-sm text-dark-400 truncate max-w-md">{{ config.apprise_url }}</p>
            </div>
            <div class="flex items-center space-x-4">
              <span :class="config.is_enabled ? 'badge-success' : 'badge'">
                {{ config.is_enabled ? 'Enabled' : 'Disabled' }}
              </span>
              <button class="text-dark-400 hover:text-white" @click="testNotification(config)">
                Test
              </button>
              <button class="text-dark-400 hover:text-red-400" @click="deleteNotification(config)">
                Delete
              </button>
            </div>
          </li>
        </ul>
      </div>
    </div>

    <!-- System Info -->
    <div v-if="activeTab === 'system'" class="space-y-6">
      <div class="card">
        <div class="p-4 border-b border-dark-700">
          <h2 class="text-lg font-semibold text-white">System Information</h2>
        </div>
        <div class="p-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p class="text-sm text-dark-400">Version</p>
            <p class="text-white">{{ systemInfo?.version || '-' }}</p>
          </div>
          <div>
            <p class="text-sm text-dark-400">Status</p>
            <p :class="systemInfo?.status === 'healthy' ? 'text-green-400' : 'text-yellow-400'">
              {{ systemInfo?.status || '-' }}
            </p>
          </div>
          <div>
            <p class="text-sm text-dark-400">Database</p>
            <p class="text-white">PostgreSQL</p>
          </div>
          <div>
            <p class="text-sm text-dark-400">Uptime</p>
            <p class="text-white">{{ systemInfo?.uptime || '-' }}</p>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="p-4 border-b border-dark-700">
          <h2 class="text-lg font-semibold text-white">Storage</h2>
        </div>
        <div class="p-6">
          <div class="mb-4">
            <div class="flex justify-between text-sm mb-1">
              <span class="text-dark-400">Used</span>
              <span class="text-white">{{ formatBytes(storageInfo?.used_bytes) }}</span>
            </div>
            <div class="w-full bg-dark-700 rounded-full h-3">
              <div
                class="h-3 rounded-full transition-all"
                :class="storageClass"
                :style="{ width: `${storageInfo?.percent_used || 0}%` }"
              ></div>
            </div>
            <div class="flex justify-between text-sm mt-1">
              <span class="text-dark-400">{{ (storageInfo?.percent_used || 0).toFixed(1) }}% used</span>
              <span class="text-dark-400">{{ formatBytes(storageInfo?.total_bytes) }} total</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="p-4 border-b border-dark-700">
          <h2 class="text-lg font-semibold text-white">Scheduled Tasks</h2>
        </div>
        <table class="table">
          <thead>
            <tr>
              <th>Task</th>
              <th>Schedule</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="task in scheduledTasks" :key="task.id">
              <td class="text-white">{{ task.name }}</td>
              <td class="text-dark-300">{{ task.schedule }}</td>
              <td>
                <span class="badge-success">Active</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Notification Modal -->
    <Modal v-model="showAddNotification" title="Add Notification Channel" size="md">
      <form @submit.prevent="addNotification" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-dark-300 mb-1">Name</label>
          <input v-model="notificationForm.name" type="text" class="input" required />
        </div>
        <div>
          <label class="block text-sm font-medium text-dark-300 mb-1">Apprise URL</label>
          <input
            v-model="notificationForm.apprise_url"
            type="text"
            class="input"
            placeholder="slack://token_a/token_b/token_c"
            required
          />
          <p class="mt-1 text-xs text-dark-400">
            <a href="https://github.com/caronc/apprise" target="_blank" class="text-primary-400">
              Apprise documentation
            </a>
          </p>
        </div>
        <div class="space-y-2">
          <label class="flex items-center">
            <input v-model="notificationForm.notify_on_capture_fail" type="checkbox" class="mr-2" />
            <span class="text-sm text-dark-300">Capture failures</span>
          </label>
          <label class="flex items-center">
            <input v-model="notificationForm.notify_on_timelapse_done" type="checkbox" class="mr-2" />
            <span class="text-sm text-dark-300">Timelapse completion</span>
          </label>
          <label class="flex items-center">
            <input v-model="notificationForm.notify_on_camera_down" type="checkbox" class="mr-2" />
            <span class="text-sm text-dark-300">Camera offline</span>
          </label>
          <label class="flex items-center">
            <input v-model="notificationForm.notify_on_storage_warn" type="checkbox" class="mr-2" />
            <span class="text-sm text-dark-300">Storage warnings</span>
          </label>
        </div>
        <div class="flex justify-end space-x-3 pt-4">
          <button type="button" class="btn-secondary" @click="showAddNotification = false">
            Cancel
          </button>
          <button type="submit" class="btn-primary">Add Channel</button>
        </div>
      </form>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useSystemStore } from '@/stores/system'
import { useNotificationsStore } from '@/stores/notifications'
import Modal from '@/components/ui/Modal.vue'

const systemStore = useSystemStore()
const toasts = useNotificationsStore()

const activeTab = ref('general')
const tabs = [
  { id: 'general', name: 'General' },
  { id: 'notifications', name: 'Notifications' },
  { id: 'system', name: 'System' },
]

const settings = ref({
  default_capture_interval: 30,
  max_concurrent_captures: 50,
  capture_timeout: 30,
  default_frame_rate: 30,
  default_crf: 20,
  default_pixel_format: 'yuv444p',
  daily_timelapse_time: '01:00',
  retention_days_images: 7,
  retention_days_videos: 365,
  cleanup_time: '03:00',
  cleanup_after_timelapse: true,
})

const notificationConfigs = ref([])
const showAddNotification = ref(false)
const notificationForm = ref({
  name: '',
  apprise_url: '',
  notify_on_capture_fail: true,
  notify_on_timelapse_done: true,
  notify_on_camera_down: true,
  notify_on_storage_warn: true,
})

const scheduledTasks = ref([
  { id: 1, name: 'Camera Capture Cycle', schedule: 'Every 30s' },
  { id: 2, name: 'Daily Timelapse Generation', schedule: '01:00 daily' },
  { id: 3, name: 'Multi-day Timelapse', schedule: 'Sunday 02:00' },
  { id: 4, name: 'File Cleanup', schedule: '03:00 daily' },
])

const systemInfo = computed(() => systemStore.systemInfo)
const storageInfo = computed(() => systemStore.storageInfo)

const storageClass = computed(() => {
  const percent = storageInfo.value?.percent_used || 0
  if (percent >= 90) return 'bg-red-500'
  if (percent >= 75) return 'bg-yellow-500'
  return 'bg-primary-500'
})

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`
}

async function loadSettings() {
  try {
    const response = await api.get('/settings')
    // Merge loaded settings with defaults
    settings.value = { ...settings.value, ...response.data }
  } catch (error) {
    console.error('Failed to load settings:', error)
  }
}

async function saveSettings() {
  try {
    await api.put('/settings', settings.value)
    toasts.success('Saved', 'Settings saved successfully')
  } catch (error) {
    toasts.error('Error', 'Failed to save settings')
  }
}

async function loadNotifications() {
  try {
    const response = await api.get('/notifications/configs')
    notificationConfigs.value = response.data
  } catch (error) {
    console.error('Failed to load notifications:', error)
  }
}

async function addNotification() {
  try {
    await api.post('/notifications/configs', notificationForm.value)
    toasts.success('Added', 'Notification channel added')
    showAddNotification.value = false
    notificationForm.value = {
      name: '',
      apprise_url: '',
      notify_on_capture_fail: true,
      notify_on_timelapse_done: true,
      notify_on_camera_down: true,
      notify_on_storage_warn: true,
    }
    await loadNotifications()
  } catch (error) {
    toasts.error('Error', 'Failed to add notification channel')
  }
}

async function testNotification(config) {
  try {
    await api.post(`/notifications/configs/${config.id}/test`)
    toasts.success('Sent', 'Test notification sent')
  } catch (error) {
    toasts.error('Error', 'Failed to send test notification')
  }
}

async function deleteNotification(config) {
  if (!confirm(`Delete notification channel "${config.name}"?`)) return
  try {
    await api.delete(`/notifications/configs/${config.id}`)
    toasts.success('Deleted', 'Notification channel deleted')
    await loadNotifications()
  } catch (error) {
    toasts.error('Error', 'Failed to delete notification channel')
  }
}

onMounted(() => {
  systemStore.fetchAll()
  loadSettings()
  loadNotifications()
})
</script>
