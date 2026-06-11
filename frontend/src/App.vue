<template>
  <div class="app-layout">
    <div class="sidebar-overlay" v-if="sidebarOpen" @click="sidebarOpen = false"></div>

    <AppSidebar
      v-if="auth.isAuthenticated"
      :mobile-open="sidebarOpen"
      @close="sidebarOpen = false"
    />

    <main class="main-content">
      <div class="mobile-topbar" v-if="auth.isAuthenticated">
        <div class="brand">
          <div class="brand-mark">F</div>
          <div class="brand-name">FIMISA</div>
        </div>
        <button class="hamburger" @click="sidebarOpen = !sidebarOpen">☰</button>
      </div>
      <RouterView />
    </main>

    <!-- Toast global -->
    <AppToast />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppSidebar from '@/components/AppSidebar.vue'
import AppToast   from '@/components/AppToast.vue'

const auth = useAuthStore()
const route = useRoute()
const sidebarOpen = ref(false)
watch(() => route.path, () => { sidebarOpen.value = false })
</script>