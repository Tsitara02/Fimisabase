import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login',     name: 'Login',       component: () => import('@/views/LoginView.vue'),       meta: { guest: true } },
  { path: '/signup',    name: 'Signup',      component: () => import('@/views/SignupView.vue'),      meta: { guest: true } },
  { path: '/',          redirect: '/dashboard' },
  { path: '/dashboard', name: 'Dashboard',   component: () => import('@/views/DashboardView.vue'),   meta: { requiresAuth: true } },
  { path: '/fournisseurs', name: 'Fournisseurs', component: () => import('@/views/FournisseursView.vue'), meta: { requiresAuth: true } },
  { path: '/stock',     name: 'Stock',       component: () => import('@/views/StockView.vue'),       meta: { requiresAuth: true } },
  { path: '/settings',  name: 'Settings',    component: () => import('@/views/SettingsView.vue'),    meta: { requiresAuth: true } },
  { path: '/bons-commande', name: 'BonsCommande', component: () => import('@/views/BonsCommandeView.vue'), meta: { requiresAuth: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) return '/login'
  if (to.meta.guest && auth.isAuthenticated) return '/dashboard'
})

export default router
