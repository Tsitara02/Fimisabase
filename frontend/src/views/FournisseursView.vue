<template>
  <div class="fade-up">
    <div class="page-header">
      <div>
        <h1>Fournisseurs AMI</h1>
        <div class="sub">Avis à Manifestation d'Intérêt — Base fournisseurs agréés</div>
      </div>
      <button class="btn btn-primary" @click="openModal()">+ Nouveau fournisseur</button>
    </div>

    <div class="filters-bar card">
      <input v-model="search" placeholder="Rechercher par raison sociale, responsable, email…" @input="debouncedSearch" />
      <div class="filter-stats">
        <span class="badge badge-green">{{ agrees }} agréés</span>
        <span class="badge badge-muted">{{ total }} total</span>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="successMsg" class="alert alert-success">{{ successMsg }}</div>

    <div class="card" style="margin-top:14px; padding: 0; overflow: hidden;">
      <div v-if="loading" class="empty-state"><p>Chargement…</p></div>
      <div v-else-if="filtered.length === 0" class="empty-state">
        <div class="icon">◉</div><p>Aucun fournisseur trouvé</p>
      </div>
      <table class="data-table" v-else>
        <thead>
          <tr>
            <th>Raison sociale</th>
            <th>Responsable</th>
            <th>Contact</th>
            <th>NIF / STAT</th>
            <th>Lots</th>
            <th>Agréé</th>
            <th style="text-align:right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="f in filtered" :key="f.id_fournisseur">
            <td>
              <span style="font-family: monospace; color: #3b82f6; font-weight: bold; margin-right: 8px;" v-if="f.code_fournisseur">
                [{{ f.code_fournisseur }}]
              </span>
              <div class="fourn-name" style="display: inline-block;">{{ f.raison_sociale }}</div>
              <div class="fourn-rc" v-if="f.rc">RC: {{ f.rc }}</div>
              <div style="font-size: 11px; color: var(--muted); margin-top: 2px;" v-if="f.date_soumission">
                📅 {{ new Date(f.date_soumission).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute:'2-digit' }) }}
              </div>
            </td>
            <td>{{ f.responsable_nom || '—' }}</td>
            <td>
              <div v-if="f.telephone" class="contact-line">📞 {{ f.telephone }}</div>
              <div v-if="f.email" class="contact-line email">✉ {{ f.email }}</div>
            </td>
            <td>
              <div v-if="f.nif" class="tax-line">NIF: {{ f.nif }}</div>
              <div v-if="f.stat" class="tax-line">STAT: {{ f.stat }}</div>
            </td>
            <td>
              <div class="lots-wrap">
                <span class="badge badge-blue" v-for="lot in (f.lots_soumissionnes||[])" :key="lot">Lot {{ lot }}</span>
              </div>
            </td>
            <td>
              <span class="badge" :class="f.statut_agree ? 'badge-green' : 'badge-muted'">
                {{ f.statut_agree ? '✓ Agréé' : 'En attente' }}
              </span>
            </td>
            <td>
              <div class="actions">
                <button class="btn btn-ghost btn-sm btn-icon" @click="openModal(f)" title="Modifier">✎</button>
                <button class="btn btn-danger btn-sm btn-icon" @click="confirmDelete(f)" title="Supprimer">✕</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editMode ? 'Modifier le fournisseur' : 'Nouveau fournisseur' }}</h2>
          <button class="btn btn-ghost btn-icon" @click="closeModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Raison sociale *</label>
            <input v-model="form.raison_sociale" placeholder="SARL Exemple" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Responsable</label>
              <input v-model="form.responsable_nom" placeholder="Nom complet" />
            </div>
            <div class="form-group">
              <label>Téléphone</label>
              <input v-model="form.telephone" placeholder="+261 …" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Email</label>
              <input v-model="form.email" type="email" placeholder="contact@…" />
            </div>
            <div class="form-group">
              <label>NIF</label>
              <input v-model="form.nif" placeholder="NIF" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>STAT</label>
              <input v-model="form.stat" placeholder="STAT" />
            </div>
            <div class="form-group">
              <label>RC</label>
              <input v-model="form.rc" placeholder="RC" />
            </div>
          </div>
          <div class="form-group">
            <label>Adresse</label>
            <textarea v-model="form.adresse" rows="2" placeholder="Adresse complète" style="resize:vertical"></textarea>
          </div>
          <div class="form-group">
            <label>Lots soumissionnés * <span style="font-weight:400;text-transform:none;letter-spacing:0">(séparés par virgule)</span></label>
            <input v-model="lotsInput" placeholder="1, 2, 3 (Entrez uniquement les numéros des lots)" />
          </div>
          <div class="form-group">
            <label>Date de soumission *</label>
            <input type="datetime-local" v-model="form.date_soumission" required />
          </div>
          <div class="form-group agrée-toggle">
            <label>Statut AMI</label>
            <div class="toggle-row">
              <button type="button" class="btn" :class="form.statut_agree ? 'btn-primary' : 'btn-ghost'" @click="form.statut_agree = true">✓ Agréé</button>
              <button type="button" class="btn" :class="!form.statut_agree ? 'btn-amber' : 'btn-ghost'" @click="form.statut_agree = false">En attente</button>
            </div>
          </div>
          <div v-if="formError" class="alert alert-danger">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Annuler</button>
          <button class="btn btn-primary" @click="saveForm" :disabled="saving">
            {{ saving ? 'Enregistrement…' : (editMode ? 'Mettre à jour' : 'Créer') }}
          </button>
        </div>
      </div>
    </div>

    <div class="modal-overlay" v-if="deleteTarget" @click.self="deleteTarget = null">
      <div class="modal" style="max-width:400px">
        <div class="modal-header"><h2>Confirmer la suppression</h2></div>
        <div class="modal-body">
          <p style="color:var(--muted2)">Supprimer <strong style="color:var(--text)">{{ deleteTarget.raison_sociale }}</strong> ? Cette action est irréversible.</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="deleteTarget = null">Annuler</button>
          <button class="btn btn-danger" @click="doDelete" :disabled="saving">
            {{ saving ? '…' : 'Supprimer' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'

const fournisseurs = ref([])
const loading = ref(true)
const error = ref('')
const successMsg = ref('')
const search = ref('')
const showModal = ref(false)
const editMode = ref(false)
const saving = ref(false)
const formError = ref('')
const deleteTarget = ref(null)
const lotsInput = ref('')

// Récupère l'heure courante calée sur le fuseau horaire local
const getCurrentDateTime = () => {
  const tzoffset = (new Date()).getTimezoneOffset() * 60000;
  return (new Date(Date.now() - tzoffset)).toISOString().slice(0, 16);
}

const defaultForm = () => ({ 
  raison_sociale: '', 
  responsable_nom: '', 
  telephone: '', 
  email: '', 
  nif: '', 
  stat: '', 
  rc: '', 
  adresse: '', 
  date_soumission: getCurrentDateTime(), 
  statut_agree: false 
})

const form = ref(defaultForm())
let editId = null

const filtered = computed(() => {
  if (!search.value) return fournisseurs.value
  const s = search.value.toLowerCase()
  return fournisseurs.value.filter(f =>
    f.raison_sociale?.toLowerCase().includes(s) ||
    f.responsable_nom?.toLowerCase().includes(s) ||
    f.email?.toLowerCase().includes(s) ||
    f.code_fournisseur?.includes(s) // Permet aussi de chercher par l'ID "0001" !
  )
})
const total = computed(() => fournisseurs.value.length)
const agrees = computed(() => fournisseurs.value.filter(f => f.statut_agree).length)

let searchTimer = null
function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {}, 300)
}

async function fetchFournisseurs() {
  loading.value = true; error.value = ''
  try {
    const { data } = await api.get('/fournisseurs')
    fournisseurs.value = data
  } catch(e) {
    error.value = e.response?.data?.error || 'Erreur de chargement'
  } finally { loading.value = false }
}

function openModal(f = null) {
  formError.value = ''
  if (f) {
    editMode.value = true
    editId = f.id_fournisseur
    
    const formattedDate = f.date_soumission 
      ? new Date(f.date_soumission).toISOString().slice(0, 16)
      : getCurrentDateTime();

    form.value = { ...defaultForm(), ...f, date_soumission: formattedDate }
    lotsInput.value = (f.lots_soumissionnes || []).join(', ')
  } else {
    editMode.value = false
    editId = null
    form.value = defaultForm()
    lotsInput.value = ''
  }
  showModal.value = true
}

function closeModal() { showModal.value = false }

async function saveForm() {
  formError.value = ''
  if (!form.value.raison_sociale) { formError.value = 'La raison sociale est requise.'; return }
  if (!form.value.date_soumission) { formError.value = 'La date de soumission est requise.'; return }

  const payload = {
    ...form.value,
    date_soumission: new Date(form.value.date_soumission).toISOString(),
    lots_soumissionnes: lotsInput.value
      .split(',')
      .map(l => parseInt(l.trim(), 10))
      .filter(n => !isNaN(n))
  }
  
  if (!payload.lots_soumissionnes.length) { formError.value = 'Au moins un lot est requis.'; return }
  saving.value = true
  try {
    if (editMode.value) {
      const { data } = await api.put(`/fournisseurs/${editId}`, payload)
      const idx = fournisseurs.value.findIndex(f => f.id_fournisseur === editId)
      if (idx > -1) fournisseurs.value[idx] = data
    } else {
      const { data } = await api.post('/fournisseurs', payload)
      fournisseurs.value.unshift(data)
    }
    closeModal()
    flash(editMode.value ? 'Fournisseur mis à jour.' : 'Fournisseur créé avec succès.')
  } catch(e) {
    formError.value = e.response?.data?.error || 'Erreur lors de la sauvegarde'
  } finally { saving.value = false }
}

function confirmDelete(f) { deleteTarget.value = f }

async function doDelete() {
  saving.value = true
  try {
    await api.delete(`/fournisseurs/${deleteTarget.value.id_fournisseur}`)
    fournisseurs.value = fournisseurs.value.filter(f => f.id_fournisseur !== deleteTarget.value.id_fournisseur)
    deleteTarget.value = null
    flash('Fournisseur supprimé.')
  } catch(e) {
    error.value = e.response?.data?.error || 'Erreur de suppression'
  } finally { saving.value = false }
}

function flash(msg) {
  successMsg.value = msg
  setTimeout(() => { successMsg.value = '' }, 3000)
}

onMounted(fetchFournisseurs)
</script>

<style scoped>
.filters-bar { display: flex; align-items: center; gap: 12px; padding: 12px 16px; }
.filters-bar input { flex: 1; }
.filter-stats { display: flex; gap: 8px; flex-shrink: 0; }
.fourn-name { font-weight: 600; font-size: 13px; }
.fourn-rc { font-size: 11px; color: var(--muted); font-family: monospace; }
.contact-line { font-size: 12px; color: var(--muted2); }
.contact-line.email { color: var(--blue); }
.tax-line { font-size: 11px; color: var(--muted); font-family: monospace; }
.lots-wrap { display: flex; flex-wrap: wrap; gap: 4px; }
.actions { display: flex; gap: 4px; justify-content: flex-end; }
.toggle-row { display: flex; gap: 8px; }
</style>