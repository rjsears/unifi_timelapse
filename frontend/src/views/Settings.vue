<template>
  <div class="space-y-6">
    <!-- Header -->
    <div>
      <h1 class="text-2xl font-bold" style="color: var(--color-text-primary);">Settings</h1>
      <p style="color: var(--color-text-muted);">System configuration and administration</p>
    </div>

    <!-- Tabs -->
    <div class="border-b" style="border-color: var(--color-border);">
      <nav class="flex space-x-8">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="[
            'py-4 px-1 border-b-2 font-medium text-sm transition-colors',
            activeTab === tab.id
              ? 'border-primary-500 text-primary-600 dark:text-primary-400'
              : 'border-transparent hover:border-gray-300 dark:hover:border-slate-600',
          ]"
          :style="activeTab !== tab.id ? { color: 'var(--color-text-secondary)' } : {}"
          @click="activeTab = tab.id"
        >
          {{ tab.name }}
        </button>
      </nav>
    </div>

    <!-- General Settings -->
    <div v-if="activeTab === 'general'" class="space-y-4">
      <!-- Capture Settings -->
      <CollapsibleCard
        title="Capture Settings"
        subtitle="Configure image capture behavior"
        :icon="CameraIcon"
        icon-color="blue"
      >
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">
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
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">
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
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">
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
      </CollapsibleCard>

      <!-- Timelapse Settings -->
      <CollapsibleCard
        title="Timelapse Settings"
        subtitle="Video generation parameters"
        :icon="FilmIcon"
        icon-color="purple"
      >
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">
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
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">
              Default CRF (Quality)
            </label>
            <input
              v-model.number="settings.default_crf"
              type="number"
              min="0"
              max="51"
              class="input"
            />
            <p class="mt-1 text-xs" style="color: var(--color-text-muted);">Lower values = higher quality</p>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">
              Daily Generation Time
            </label>
            <input
              v-model="settings.daily_timelapse_time"
              type="time"
              class="input"
            />
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">
              Pixel Format
            </label>
            <select v-model="settings.default_pixel_format" class="input">
              <option value="yuv420p">yuv420p (Recommended)</option>
              <option value="yuv444p">yuv444p (High Quality)</option>
              <option value="rgb24">rgb24</option>
            </select>
          </div>
        </div>
      </CollapsibleCard>

      <!-- Retention Settings -->
      <CollapsibleCard
        title="Retention Settings"
        subtitle="Image and video cleanup policies"
        :icon="TrashIcon"
        icon-color="red"
      >
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">
              Image Retention (days)
            </label>
            <input
              v-model.number="settings.retention_days_images"
              type="number"
              min="1"
              class="input"
            />
            <p class="mt-1 text-xs" style="color: var(--color-text-muted);">
              Note: Custom timelapses can only use images within this retention period
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">
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
            <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">
              Cleanup Time
            </label>
            <input
              v-model="settings.cleanup_time"
              type="time"
              class="input"
            />
          </div>
        </div>
      </CollapsibleCard>

      <div class="flex justify-end">
        <button class="btn-primary" @click="saveSettings">Save Settings</button>
      </div>
    </div>

    <!-- Notifications -->
    <div v-if="activeTab === 'notifications'" class="space-y-4">
      <CollapsibleCard
        title="Notification Channels"
        subtitle="Configure alerts and notifications"
        :icon="BellIcon"
        icon-color="yellow"
        :default-open="true"
      >
        <template #default>
          <div class="space-y-4">
            <div class="flex justify-end">
              <button class="btn-primary text-sm" @click="showAddNotification = true">
                Add Channel
              </button>
            </div>
            <div v-if="notificationConfigs.length === 0" class="text-center py-8" style="color: var(--color-text-muted);">
              No notification channels configured
            </div>
            <ul v-else class="divide-y" style="--tw-divide-opacity: 1; border-color: var(--color-border);">
              <li
                v-for="config in notificationConfigs"
                :key="config.id"
                class="py-4 flex items-center justify-between"
              >
                <div>
                  <p class="font-medium" style="color: var(--color-text-primary);">{{ config.name }}</p>
                  <p class="text-sm truncate max-w-md" style="color: var(--color-text-muted);">{{ config.apprise_url }}</p>
                </div>
                <div class="flex items-center space-x-4">
                  <span :class="config.is_enabled ? 'badge-success' : 'badge'">
                    {{ config.is_enabled ? 'Enabled' : 'Disabled' }}
                  </span>
                  <button class="hover:opacity-80" style="color: var(--color-text-muted);" @click="testNotification(config)">
                    Test
                  </button>
                  <button class="hover:text-red-500" style="color: var(--color-text-muted);" @click="deleteNotification(config)">
                    Delete
                  </button>
                </div>
              </li>
            </ul>
          </div>
        </template>
      </CollapsibleCard>
    </div>

    <!-- System Info -->
    <div v-if="activeTab === 'system'" class="space-y-4">
      <!-- System Information -->
      <CollapsibleCard
        title="System Information"
        subtitle="Application version and status"
        :icon="CpuChipIcon"
        icon-color="green"
        :default-open="true"
      >
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <p class="text-sm" style="color: var(--color-text-muted);">Version</p>
            <p style="color: var(--color-text-primary);">{{ systemInfo?.version || '-' }}</p>
          </div>
          <div>
            <p class="text-sm" style="color: var(--color-text-muted);">Status</p>
            <p :class="systemInfo?.status === 'healthy' ? 'text-green-500' : 'text-yellow-500'">
              {{ systemInfo?.status || '-' }}
            </p>
          </div>
          <div>
            <p class="text-sm" style="color: var(--color-text-muted);">Database</p>
            <p style="color: var(--color-text-primary);">PostgreSQL</p>
          </div>
          <div>
            <p class="text-sm" style="color: var(--color-text-muted);">Uptime</p>
            <p style="color: var(--color-text-primary);">{{ systemInfo?.uptime || '-' }}</p>
          </div>
        </div>
      </CollapsibleCard>

      <!-- Storage -->
      <CollapsibleCard
        title="Storage"
        subtitle="Disk usage and capacity"
        :icon="CircleStackIcon"
        icon-color="blue"
      >
        <div class="mb-4">
          <div class="flex justify-between text-sm mb-1">
            <span class="text-gray-500 dark:text-gray-400">Used</span>
            <span style="color: var(--color-text-primary);">{{ formatBytes(storageInfo?.used_bytes) }}</span>
          </div>
          <div class="w-full rounded-full h-3" style="background-color: var(--color-bg-secondary);">
            <div
              class="h-3 rounded-full transition-all"
              :class="storageClass"
              :style="{ width: `${storageInfo?.percent_used || 0}%` }"
            ></div>
          </div>
          <div class="flex justify-between text-sm mt-1">
            <span class="text-gray-500 dark:text-gray-400">{{ (storageInfo?.percent_used || 0).toFixed(1) }}% used</span>
            <span class="text-gray-500 dark:text-gray-400">{{ formatBytes(storageInfo?.total_bytes) }} total</span>
          </div>
        </div>
      </CollapsibleCard>

      <!-- Scheduled Tasks -->
      <CollapsibleCard
        title="Scheduled Tasks"
        subtitle="Background job schedules"
        :icon="ClockIcon"
        icon-color="gray"
      >
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
              <td style="color: var(--color-text-primary);">{{ task.name }}</td>
              <td style="color: var(--color-text-secondary);">{{ task.schedule }}</td>
              <td>
                <span class="badge-success">Active</span>
              </td>
            </tr>
          </tbody>
        </table>
      </CollapsibleCard>
    </div>

    <!-- Add Notification Modal -->
    <Modal v-model="showAddNotification" title="Add Notification Channel" size="md">
      <form @submit.prevent="addNotification" class="space-y-4">
        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Name</label>
          <input v-model="notificationForm.name" type="text" class="input" required />
        </div>
        <div>
          <label class="block text-sm font-medium mb-1" style="color: var(--color-text-secondary);">Apprise URL</label>
          <input
            v-model="notificationForm.apprise_url"
            type="text"
            class="input"
            placeholder="slack://token_a/token_b/token_c"
            required
          />
          <p class="mt-1 text-xs" style="color: var(--color-text-muted);">
            <a href="https://github.com/caronc/apprise" target="_blank" class="text-primary-600 dark:text-primary-400 hover:underline">
              Apprise documentation
            </a>
          </p>
        </div>
        <div class="space-y-2">
          <label class="flex items-center cursor-pointer">
            <input v-model="notificationForm.notify_on_capture_fail" type="checkbox" class="w-4 h-4 text-primary-600 rounded border-gray-300 dark:border-dark-600 focus:ring-primary-500 dark:bg-dark-700" />
            <span class="ml-2 text-sm" style="color: var(--color-text-secondary);">Capture failures</span>
          </label>
          <label class="flex items-center cursor-pointer">
            <input v-model="notificationForm.notify_on_timelapse_done" type="checkbox" class="w-4 h-4 text-primary-600 rounded border-gray-300 dark:border-dark-600 focus:ring-primary-500 dark:bg-dark-700" />
            <span class="ml-2 text-sm" style="color: var(--color-text-secondary);">Timelapse completion</span>
          </label>
          <label class="flex items-center cursor-pointer">
            <input v-model="notificationForm.notify_on_camera_down" type="checkbox" class="w-4 h-4 text-primary-600 rounded border-gray-300 dark:border-dark-600 focus:ring-primary-500 dark:bg-dark-700" />
            <span class="ml-2 text-sm" style="color: var(--color-text-secondary);">Camera offline</span>
          </label>
          <label class="flex items-center cursor-pointer">
            <input v-model="notificationForm.notify_on_storage_warn" type="checkbox" class="w-4 h-4 text-primary-600 rounded border-gray-300 dark:border-dark-600 focus:ring-primary-500 dark:bg-dark-700" />
            <span class="ml-2 text-sm" style="color: var(--color-text-secondary);">Storage warnings</span>
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
import CollapsibleCard from '@/components/ui/CollapsibleCard.vue'
import {
  CameraIcon,
  FilmIcon,
  TrashIcon,
  BellIcon,
  CpuChipIcon,
  CircleStackIcon,
  ClockIcon,
} from '@heroicons/vue/24/outline'

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
    // Convert settings array to key-value object
    const settingsObj = {}
    for (const setting of response.data.settings || []) {
      settingsObj[setting.key] = setting.value
    }
    // Merge loaded settings with defaults
    settings.value = { ...settings.value, ...settingsObj }
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
    const response = await api.get('/notifications')
    notificationConfigs.value = response.data
  } catch (error) {
    console.error('Failed to load notifications:', error)
  }
}

async function addNotification() {
  try {
    await api.post('/notifications', notificationForm.value)
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
    await api.post(`/notifications/${config.id}/test`)
    toasts.success('Sent', 'Test notification sent')
  } catch (error) {
    toasts.error('Error', 'Failed to send test notification')
  }
}

async function deleteNotification(config) {
  if (!confirm(`Delete notification channel "${config.name}"?`)) return
  try {
    await api.delete(`/notifications/${config.id}`)
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
