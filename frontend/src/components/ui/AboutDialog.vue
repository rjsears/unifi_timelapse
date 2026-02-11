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
        <div class="relative rounded-lg shadow-xl max-w-md w-full border"
          style="background-color: var(--color-surface); border-color: var(--color-border);">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b"
            style="border-color: var(--color-border);">
            <div class="flex items-center gap-3">
              <div class="p-2 rounded-full bg-blue-100 dark:bg-blue-500/20">
                <InformationCircleIcon class="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 class="text-lg font-semibold" style="color: var(--color-text-primary);">About</h3>
            </div>
            <button
              @click="close"
              class="p-1 rounded-lg transition-colors"
              style="color: var(--color-text-secondary);"
            >
              <XMarkIcon class="h-5 w-5" />
            </button>
          </div>

          <!-- Content -->
          <div class="px-6 py-6 space-y-6">
            <!-- App name and version -->
            <div class="text-center">
              <h2 class="text-2xl font-bold" style="color: var(--color-text-primary);">{{ appInfo.name }}</h2>
              <p class="text-sm mt-1" style="color: var(--color-text-muted);">{{ appInfo.fullName }}</p>
              <div class="mt-2 flex items-center justify-center gap-2">
                <span class="px-2.5 py-0.5 rounded-full bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-300 text-sm font-medium">
                  v{{ appInfo.version }}
                </span>
                <span class="text-sm" style="color: var(--color-text-muted);">{{ appInfo.versionDate }}</span>
              </div>
            </div>

            <!-- Divider -->
            <div class="border-t" style="border-color: var(--color-border);"></div>

            <!-- Description -->
            <div class="text-center">
              <p class="text-sm" style="color: var(--color-text-secondary);">
                Automated timelapse creation system for UniFi Protect cameras. Capture, schedule, and generate beautiful timelapse videos with ease.
              </p>
            </div>

            <!-- Divider -->
            <div class="border-t" style="border-color: var(--color-border);"></div>

            <!-- Author info -->
            <div class="text-center space-y-1">
              <p class="text-sm" style="color: var(--color-text-muted);">Developed by</p>
              <p class="font-medium" style="color: var(--color-text-primary);">{{ appInfo.author }}</p>
              <a
                :href="`mailto:${appInfo.email}`"
                class="text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                {{ appInfo.email }}
              </a>
            </div>

            <!-- Divider -->
            <div class="border-t" style="border-color: var(--color-border);"></div>

            <!-- GitHub link -->
            <div class="text-center">
              <button
                @click="openGithub"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-lg transition-colors"
                style="background-color: var(--color-bg-secondary); color: var(--color-text-primary);"
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
          <div class="flex items-center justify-center px-6 py-4 border-t rounded-b-lg"
            style="border-color: var(--color-border); background-color: var(--color-bg-secondary);">
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

// Version info
const appInfo = {
  name: 'UniFi Timelapse',
  fullName: 'UniFi Protect Timelapse System',
  version: '1.0.0',
  versionDate: '2026-02-10',
  author: 'Richard J. Sears',
  email: 'richardjsears@protonmail.com',
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
