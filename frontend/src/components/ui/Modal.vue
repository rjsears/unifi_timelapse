<template>
  <teleport to="body">
    <transition
      enter-active-class="ease-out duration-300"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="ease-in duration-200"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 overflow-y-auto"
        @click.self="close"
      >
        <div class="min-h-screen px-4 text-center">
          <!-- Background overlay -->
          <div class="fixed inset-0 bg-black/60" @click="close"></div>

          <!-- Centering element -->
          <span class="inline-block h-screen align-middle" aria-hidden="true">&#8203;</span>

          <!-- Modal panel -->
          <transition
            enter-active-class="ease-out duration-300"
            enter-from-class="opacity-0 scale-95"
            enter-to-class="opacity-100 scale-100"
            leave-active-class="ease-in duration-200"
            leave-from-class="opacity-100 scale-100"
            leave-to-class="opacity-0 scale-95"
          >
            <div
              v-if="modelValue"
              :class="[
                'inline-block w-full text-left align-middle transition-all transform rounded-lg shadow-xl border',
                sizeClasses,
              ]"
              style="background-color: var(--color-surface); border-color: var(--color-border);"
            >
              <!-- Header -->
              <div
                v-if="title || $slots.header"
                class="flex items-center justify-between px-6 py-4 border-b"
                style="border-color: var(--color-border);"
              >
                <slot name="header">
                  <h3 class="text-lg font-semibold" style="color: var(--color-text-primary);">{{ title }}</h3>
                </slot>
                <button
                  v-if="closable"
                  class="p-1 rounded-lg transition-colors hover:bg-gray-100 dark:hover:bg-slate-800"
                  style="color: var(--color-text-muted);"
                  @click="close"
                >
                  <XMarkIcon class="w-5 h-5" />
                </button>
              </div>

              <!-- Content -->
              <div class="px-6 py-4">
                <slot></slot>
              </div>

              <!-- Footer -->
              <div
                v-if="$slots.footer"
                class="px-6 py-4 border-t rounded-b-lg"
                style="border-color: var(--color-border); background-color: var(--color-bg-secondary);"
              >
                <slot name="footer"></slot>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
import { computed, watch } from 'vue'
import { XMarkIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg', 'xl', 'full'].includes(value),
  },
  closable: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['update:modelValue', 'close'])

const sizeClasses = computed(() => {
  const sizes = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    full: 'max-w-4xl',
  }
  return sizes[props.size]
})

function close() {
  if (props.closable) {
    emit('update:modelValue', false)
    emit('close')
  }
}

// Lock body scroll when modal is open
watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
  }
)
</script>
