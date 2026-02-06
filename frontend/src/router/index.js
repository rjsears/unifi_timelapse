import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/cameras',
    name: 'Cameras',
    component: () => import('@/views/Cameras.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/cameras/:id',
    name: 'CameraDetail',
    component: () => import('@/views/CameraDetail.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/timelapses',
    name: 'Timelapses',
    component: () => import('@/views/Timelapses.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/images',
    name: 'Images',
    component: () => import('@/views/Images.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/health',
    name: 'Health',
    component: () => import('@/views/Health.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/views/Settings.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Check if route requires auth
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
    return
  }

  // Check if route requires admin
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'Dashboard' })
    return
  }

  // Redirect to dashboard if already logged in
  if (to.name === 'Login' && authStore.isAuthenticated) {
    next({ name: 'Dashboard' })
    return
  }

  next()
})

export default router
