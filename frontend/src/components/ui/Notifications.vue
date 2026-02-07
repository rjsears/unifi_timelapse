<template>
  <div class="fixed bottom-4 right-4 z-50 space-y-2">
    <transition-group
      enter-active-class="transform ease-out duration-300 transition"
      enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
      enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
      leave-active-class="transition ease-in duration-100"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-for="notification in notifications"
        :key="notification.id"
        :class="[
          'max-w-sm w-full bg-white shadow-lg rounded-lg pointer-events-auto border overflow-hidden',
          borderClass(notification.type),
        ]"
      >
        <div class="p-4">
          <div class="flex items-start">
            <div class="flex-shrink-0">
              <component
                :is="iconComponent(notification.type)"
                :class="['h-5 w-5', iconClass(notification.type)]"
              />
            </div>
            <div class="ml-3 w-0 flex-1">
              <p class="text-sm font-medium text-gray-900">
                {{ notification.title }}
              </p>
              <p v-if="notification.message" class="mt-1 text-sm text-gray-500">
                {{ notification.message }}
              </p>
            </div>
            <div class="ml-4 flex-shrink-0 flex">
              <button
                class="inline-flex text-gray-500 hover:text-gray-700 focus:outline-none"
                @click="remove(notification.id)"
              >
                <XMarkIcon class="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useNotificationsStore } from '@/stores/notifications'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/vue/24/outline'

const notificationsStore = useNotificationsStore()
const notifications = computed(() => notificationsStore.notifications)

function remove(id) {
  notificationsStore.remove(id)
}

function iconComponent(type) {
  const icons = {
    success: CheckCircleIcon,
    warning: ExclamationTriangleIcon,
    error: XCircleIcon,
    info: InformationCircleIcon,
  }
  return icons[type] || InformationCircleIcon
}

function iconClass(type) {
  const classes = {
    success: 'text-green-500',
    warning: 'text-yellow-500',
    error: 'text-red-500',
    info: 'text-blue-500',
  }
  return classes[type] || 'text-blue-500'
}

function borderClass(type) {
  const classes = {
    success: 'border-green-500/20',
    warning: 'border-yellow-500/20',
    error: 'border-red-500/20',
    info: 'border-blue-500/20',
  }
  return classes[type] || 'border-gray-200'
}
</script>
