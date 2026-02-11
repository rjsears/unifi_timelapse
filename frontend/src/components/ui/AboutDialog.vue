<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="open"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4"
      >
        <!-- Backdrop -->
        <div
          class="absolute inset-0 bg-black/50"
          @click="close"
        />

        <!-- Dialog -->
        <div class="relative bg-white dark:bg-dark-800 rounded-lg shadow-xl max-w-md w-full border border-gray-200 dark:border-dark-700">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-dark-700">
            <div class="flex items-center gap-3">
              <div class="p-2 rounded-full bg-primary-100 dark:bg-primary-500/20">
                <InformationCircleIcon class="h-5 w-5 text-primary-600 dark:text-primary-400" />
              </div>
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">About</h3>
            </div>
            <button
              @click="close"
              class="p-1 rounded-lg text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-dark-700"
            >
              <XMarkIcon class="h-5 w-5" />
            </button>
          </div>

          <!-- Content -->
          <div class="px-6 py-6 space-y-6">
            <!-- App name and version -->
            <div class="text-center">
              <h2 class="text-2xl font-bold text-gray-900 dark:text-white">{{ appInfo.name }}</h2>
              <div class="mt-2 flex items-center justify-center gap-2">
                <span class="px-2.5 py-0.5 rounded-full bg-primary-100 dark:bg-primary-500/20 text-primary-700 dark:text-primary-300 text-sm font-medium">
                  v{{ appInfo.version }}
                </span>
              </div>
            </div>

            <!-- Divider -->
            <div class="border-t border-gray-200 dark:border-dark-700"></div>

            <!-- Author info -->
            <div class="text-center space-y-1">
              <p class="text-sm text-gray-500 dark:text-gray-400">Developed by</p>
              <p class="font-medium text-gray-900 dark:text-white">{{ appInfo.author }}</p>
            </div>

            <!-- Divider -->
            <div class="border-t border-gray-200 dark:border-dark-700"></div>

            <!-- GitHub link -->
            <div class="text-center">
              <button
                @click="openGithub"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-100 dark:bg-dark-700 hover:bg-gray-200 dark:hover:bg-dark-600 text-gray-900 dark:text-white transition-colors"
              >
                <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 24 24">
                  <path fill-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clip-rule="evenodd" />
                </svg>
                View on GitHub
                <ArrowTopRightOnSquareIcon class="h-4 w-4" />
              </button>
            </div>
          </div>

          <!-- Footer -->
          <div class="flex items-center justify-center px-6 py-4 border-t border-gray-200 dark:border-dark-700 bg-gray-50 dark:bg-dark-800/50 rounded-b-lg">
            <button
              @click="close"
              class="btn-secondary"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { XMarkIcon, InformationCircleIcon, ArrowTopRightOnSquareIcon } from '@heroicons/vue/24/outline'

defineProps({
  open: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close'])

const appInfo = {
  name: 'UniFi Timelapse',
  version: '1.0.0',
  author: 'Richard J. Sears',
  githubUrl: 'https://github.com/rjsears/unifi_timelapse',
}

function close() {
  emit('close')
}

function openGithub() {
  window.open(appInfo.githubUrl, '_blank', 'noopener,noreferrer')
}
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
