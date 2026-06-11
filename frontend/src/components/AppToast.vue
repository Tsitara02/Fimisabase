<template>
  <div class="toast-container" aria-live="polite">
    <div v-for="t in toasts" :key="t.id" class="toast" :class="[`toast-${t.type}`, { leaving: t.leaving }]">
      <span class="toast-icon">{{ t.type === 'success' ? '✓' : t.type === 'error' ? '✕' : 'ℹ' }}</span>
      <span class="toast-msg">{{ t.msg }}</span>
      <button class="toast-close" @click="dismiss(t.id)">✕</button>
    </div>
  </div>
</template>
<script setup>
import { useToast } from '@/composables/useToast'
const { toasts, dismiss } = useToast()
</script>