<template>
  <div class="fade-up">
    <div class="page-header">
      <div>
        <h1>Items</h1>
        <p class="page-sub">Données depuis Supabase via Flask</p>
      </div>
      <button class="btn btn-primary" @click="showForm = !showForm">
        {{ showForm ? '✕ Annuler' : '+ Ajouter' }}
      </button>
    </div>

    <!-- Add form -->
    <div class="card add-form" v-if="showForm">
      <h3>Nouvel item</h3>
      <div class="form-row">
        <input v-model="newItem.name" placeholder="Nom" />
        <input v-model="newItem.description" placeholder="Description (optionnel)" />
        <button class="btn btn-primary" @click="addItem" :disabled="!newItem.name || saving">
          {{ saving ? '…' : 'Créer' }}
        </button>
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="alert danger">{{ error }}</div>

    <!-- List -->
    <div class="card" style="margin-top: 16px;">
      <div v-if="loading" class="empty-state">Chargement…</div>
      <div v-else-if="items.length === 0" class="empty-state">
        Aucun item. Créez-en un !
      </div>
      <div v-else class="items-list">
        <div class="item-row" v-for="item in items" :key="item.id">
          <div class="item-info">
            <div class="item-name">{{ item.name }}</div>
            <div class="item-desc" v-if="item.description">{{ item.description }}</div>
          </div>
          <button class="btn btn-danger sm" @click="removeItem(item.id)">✕</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const items   = ref([])
const loading = ref(true)
const saving  = ref(false)
const error   = ref('')
const showForm = ref(false)
const newItem  = ref({ name: '', description: '' })

async function fetchItems() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/items')
    items.value = data
  } catch (e) {
    error.value = 'Impossible de charger les items. Vérifiez la table Supabase.'
  } finally {
    loading.value = false
  }
}

async function addItem() {
  if (!newItem.value.name) return
  saving.value = true
  error.value = ''
  try {
    const { data } = await api.post('/items', { ...newItem.value })
    items.value.unshift(data)
    newItem.value = { name: '', description: '' }
    showForm.value = false
  } catch (e) {
    error.value = e.response?.data?.error || 'Erreur lors de la création'
  } finally {
    saving.value = false
  }
}

async function removeItem(id) {
  try {
    await api.delete(`/items/${id}`)
    items.value = items.value.filter(i => i.id !== id)
  } catch (e) {
    error.value = 'Suppression échouée'
  }
}

onMounted(fetchItems)
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.page-header h1 { font-size: 28px; }
.page-sub { color: var(--muted); margin-top: 4px; }

.add-form { margin-bottom: 0; }
.add-form h3 { font-size: 15px; margin-bottom: 14px; }
.form-row { display: flex; gap: 10px; flex-wrap: wrap; align-items: flex-start; }
.form-row input { flex: 1; min-width: 160px; }
.form-row .btn { flex-shrink: 0; white-space: nowrap; }

.empty-state { text-align: center; color: var(--muted); padding: 40px 0; }
.items-list { display: flex; flex-direction: column; gap: 1px; }
.item-row {
  display: flex;
  align-items: center;
  padding: 14px 8px;
  border-bottom: 1px solid var(--border);
  gap: 12px;
  transition: background .15s;
}
.item-row:last-child { border-bottom: none; }
.item-row:hover { background: var(--surface2); border-radius: 8px; }
.item-info { flex: 1; min-width: 0; }
.item-name { font-weight: 500; font-size: 14px; }
.item-desc { font-size: 13px; color: var(--muted); margin-top: 2px; }
.btn.sm { padding: 6px 10px; font-size: 13px; }
.alert { padding: 10px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 12px; }
.alert.danger { background: color-mix(in srgb, var(--danger) 12%, transparent); color: #f87171; border: 1px solid color-mix(in srgb, var(--danger) 25%, transparent); }
</style>
