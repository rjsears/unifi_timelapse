<template>
  <div class="rounded-lg border border-gray-200 dark:border-dark-700 bg-white dark:bg-dark-800">
    <!-- Header -->
    <button
      @click="toggle"
      class="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 dark:hover:bg-dark-700 transition-colors rounded-t-lg"
      :class="{ 'rounded-b-lg': !isOpen }"
    >
      <div class="flex items-center gap-3">
        <div
          v-if="icon"
          class="p-2 rounded-lg"
          :class="iconBgClass"
        >
          <component :is="icon" class="h-5 w-5" :class="iconClass" />
        </div>
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ title }}</h3>
          <p v-if="subtitle" class="text-sm text-gray-500 dark:text-gray-400">{{ subtitle }}</p>
        </div>
      </div>
      <ChevronDownIcon
        class="h-5 w-5 text-gray-500 dark:text-gray-400 transition-transform duration-200"
        :class="{ 'rotate-180': isOpen }"
      />
    </button>

    <!-- Content -->
    <Transition
      enter-active-class="transition-all duration-200 ease-out"
      leave-active-class="transition-all duration-200 ease-in"
      enter-from-class="opacity-0 max-h-0"
      enter-to-class="opacity-100 max-h-[2000px]"
      leave-from-class="opacity-100 max-h-[2000px]"
      leave-to-class="opacity-0 max-h-0"
    >
      <div v-show="isOpen" class="overflow-hidden">
        <div class="p-6 border-t border-gray-200 dark:border-dark-700">
          <slot />
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ChevronDownIcon } from '@heroicons/vue/24/outline'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  subtitle: {
    type: String,
    default: '',
  },
  icon: {
    type: [Object, Function],
    default: null,
  },
  iconColor: {
    type: String,
    default: 'blue',
    validator: (value) => ['blue', 'green', 'yellow', 'red', 'purple', 'gray'].includes(value),
  },
  defaultOpen: {
    type: Boolean,
    default: false,
  },
})

const isOpen = ref(props.defaultOpen)

const iconColorMap = {
  blue: {
    bg: 'bg-blue-100 dark:bg-blue-500/20',
    icon: 'text-blue-600 dark:text-blue-400',
  },
  green: {
    bg: 'bg-green-100 dark:bg-green-500/20',
    icon: 'text-green-600 dark:text-green-400',
  },
  yellow: {
    bg: 'bg-yellow-100 dark:bg-yellow-500/20',
    icon: 'text-yellow-600 dark:text-yellow-400',
  },
  red: {
    bg: 'bg-red-100 dark:bg-red-500/20',
    icon: 'text-red-600 dark:text-red-400',
  },
  purple: {
    bg: 'bg-purple-100 dark:bg-purple-500/20',
    icon: 'text-purple-600 dark:text-purple-400',
  },
  gray: {
    bg: 'bg-gray-100 dark:bg-gray-500/20',
    icon: 'text-gray-600 dark:text-gray-400',
  },
}

const iconBgClass = iconColorMap[props.iconColor]?.bg || iconColorMap.blue.bg
const iconClass = iconColorMap[props.iconColor]?.icon || iconColorMap.blue.icon

function toggle() {
  isOpen.value = !isOpen.value
}

watch(() => props.defaultOpen, (newVal) => {
  isOpen.value = newVal
})
</script>
