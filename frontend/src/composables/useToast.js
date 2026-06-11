import { ref } from 'vue'

const toasts = ref([])
let nextId = 0

export function useToast() {
  function show(msg, type = 'success', duration = 3200) {
    const id = ++nextId
    toasts.value.push({ id, msg, type })
    setTimeout(() => dismiss(id), duration)
  }
  function dismiss(id) {
    const toast = toasts.value.find(t => t.id === id)
    if (!toast) return
    toast.leaving = true
    setTimeout(() => { toasts.value = toasts.value.filter(t => t.id !== id) }, 220)
  }
  return { toasts, success: (m) => show(m,'success'), error: (m) => show(m,'error',5000), info: (m) => show(m,'info'), dismiss }
}