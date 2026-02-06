import { defineStore } from 'pinia'
import { ref } from 'vue'

let notificationId = 0

export const useNotificationsStore = defineStore('notifications', () => {
  const notifications = ref([])

  function add(notification) {
    const id = ++notificationId
    const newNotification = {
      id,
      type: notification.type || 'info',
      title: notification.title,
      message: notification.message,
      duration: notification.duration ?? 5000,
    }

    notifications.value.push(newNotification)

    if (newNotification.duration > 0) {
      setTimeout(() => {
        remove(id)
      }, newNotification.duration)
    }

    return id
  }

  function remove(id) {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
  }

  function success(title, message = '') {
    return add({ type: 'success', title, message })
  }

  function error(title, message = '') {
    return add({ type: 'error', title, message, duration: 8000 })
  }

  function warning(title, message = '') {
    return add({ type: 'warning', title, message })
  }

  function info(title, message = '') {
    return add({ type: 'info', title, message })
  }

  return {
    notifications,
    add,
    remove,
    success,
    error,
    warning,
    info,
  }
})
