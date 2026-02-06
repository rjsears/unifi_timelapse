<template>
  <div class="min-h-screen flex items-center justify-center bg-dark-900 px-4">
    <div class="max-w-md w-full">
      <!-- Logo/Title -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-primary-500">UniFi Timelapse</h1>
        <p class="mt-2 text-dark-400">Sign in to your account</p>
      </div>

      <!-- Login form -->
      <div class="card p-8">
        <form @submit.prevent="handleLogin" class="space-y-6">
          <div>
            <label for="username" class="block text-sm font-medium text-dark-300 mb-2">
              Username
            </label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              class="input"
              placeholder="Enter your username"
              required
              autofocus
            />
          </div>

          <div>
            <label for="password" class="block text-sm font-medium text-dark-300 mb-2">
              Password
            </label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              class="input"
              placeholder="Enter your password"
              required
            />
          </div>

          <div v-if="error" class="text-red-400 text-sm text-center">
            {{ error }}
          </div>

          <button
            type="submit"
            class="w-full btn-primary py-3"
            :disabled="loading"
          >
            <span v-if="loading" class="flex items-center justify-center">
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Signing in...
            </span>
            <span v-else>Sign In</span>
          </button>
        </form>
      </div>

      <!-- Footer -->
      <p class="mt-4 text-center text-xs text-dark-500">
        UniFi Timelapse System v1.0.0
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const form = ref({
  username: '',
  password: '',
})
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  loading.value = true
  error.value = ''

  const result = await authStore.login(form.value.username, form.value.password)

  if (result.success) {
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } else {
    error.value = result.error
  }

  loading.value = false
}
</script>
