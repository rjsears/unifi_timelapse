import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  const colorMode = ref(localStorage.getItem('theme') || 'system')

  const isDark = computed(() => {
    if (colorMode.value === 'dark') return true
    if (colorMode.value === 'light') return false
    // System preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  const themeClasses = computed(() => {
    return isDark.value ? 'dark' : ''
  })

  function setColorMode(mode) {
    colorMode.value = mode
    localStorage.setItem('theme', mode)
    applyTheme()
  }

  function toggleColorMode() {
    if (colorMode.value === 'dark') {
      setColorMode('light')
    } else if (colorMode.value === 'light') {
      setColorMode('system')
    } else {
      setColorMode('dark')
    }
  }

  function applyTheme() {
    if (isDark.value) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  function init() {
    applyTheme()
    // Listen for system preference changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (colorMode.value === 'system') {
        applyTheme()
      }
    })
  }

  return {
    colorMode,
    isDark,
    themeClasses,
    setColorMode,
    toggleColorMode,
    init,
  }
})
