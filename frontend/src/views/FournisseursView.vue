<template>
  <div class="fade-up">
    <div class="page-header">
      <div>
        <h1>Fournisseurs AMI</h1>
        <div class="sub">Appel à Manifestation d'Intérêt — Base fournisseurs agréés</div>
      </div>
      <button class="btn btn-primary" @click="openModal">+ Nouveau fournisseur</button>
    </div>

    <!-- Filters -->
    <div class="filters-bar card">
      <input v-model="search" placeholder="Rechercher par raison sociale, responsable, email…" />
      <select v-model="filterStatut" style="width:auto;min-width:150px">
        <option value="">Tous les statuts</option>
        <option value="agree">Agréé</option>
        <option value="attente">En attente</option>
      </select>
      <div class="filter-stats">
        <span class="badge badge-green">{{ agrees }} agréés</span>
        <span class="badge badge-muted">{{ total }} total</span>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>

    <!-- Liste cards -->
    <div class="card" style="margin-top:14px; padding:0; overflow:hidden;">
      <div v-if="loading" class="empty-state"><p>Chargement…</p></div>
      <div v-else-if="filtered.length === 0" class="empty-state">
        <div class="icon">◉</div>
        <p>Aucun fournisseur trouvé</p>
      </div>
      <div v-else class="fourn-list">
        <div
          class="fourn-card fade-up"
          v-for="(f, i) in filtered"
          :key="f.id_fournisseur"
          :style="{ animationDelay: Math.min(i, 8) * 40 + 'ms' }"
        >
          <!-- Avatar -->
          <div class="fourn-avatar" :class="avatarClass(f.raison_sociale)">
            {{ initiales(f.raison_sociale) }}
          </div>

          <!-- Corps -->
          <div class="fourn-body">
            <div class="fourn-title">
              <span class="fourn-name">{{ f.raison_sociale }}</span>
              <span class="badge" :class="f.statut_agree ? 'badge-green' : 'badge-muted'">
                {{ f.statut_agree ? '✓ Agréé' : 'En attente' }}
              </span>
              <span class="badge badge-blue" v-if="f.code_fournisseur" style="font-family:monospace">
                {{ f.code_fournisseur }}
              </span>
            </div>
            <div class="fourn-meta">
              <span v-if="f.responsable_nom">👤 {{ f.responsable_nom }}</span>
              <span v-if="f.telephone">📞 {{ f.telephone }}</span>
              <span v-if="f.email" style="color:var(--blue)">✉ {{ f.email }}</span>
              <span v-if="f.nif" style="font-family:monospace;font-size:11px">NIF: {{ f.nif }}</span>
            </div>
            <div class="lots-wrap" v-if="f.lots_soumissionnes?.length">
              <span class="badge badge-blue" v-for="lot in f.lots_soumissionnes" :key="lot">
                Lot {{ lot }}
              </span>
            </div>
          </div>

          <!-- Actions -->
          <div class="fourn-actions">
            <div class="fourn-date" v-if="f.date_soumission">
              {{ formatDate(f.date_soumission) }}
            </div>
            <div class="fourn-actions-btns">
              <button
                class="btn btn-ghost btn-sm btn-icon"
                @click="openModal(f)"
                title="Modifier"
              >✎</button>
              <div style="width:1px;background:var(--border);margin:0 2px;align-self:stretch"></div>
              <button
                class="btn btn-danger btn-sm btn-icon"
                @click="confirmDelete(f)"
                title="Supprimer"
              >✕</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Fournisseur -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
        <div class="modal">
          <div class="modal-header">
            <h2>{{ editMode ? 'Modifier le fournisseur' : 'Nouveau fournisseur' }}</h2>
            <button class="btn btn-ghost btn-icon" @click="closeModal">✕</button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <label>Raison sociale *</label>
              <input v-model="form.raison_sociale" placeholder="SARL Exemple" autofocus />
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
              <label>
                Lots soumissionnés *
                <span style="font-weight:400;text-transform:none;letter-spacing:0;font-size:11px">
                  — numéros séparés par virgule
                </span>
              </label>
              <input v-model="lotsInput" placeholder="1, 2, 3" />
            </div>
            <div class="form-group">
              <label>Date de soumission *</label>
              <input type="datetime-local" v-model="form.date_soumission" />
            </div>
            <div class="form-group">
              <label>Statut AMI</label>
              <div class="toggle-row">
                <button
                  type="button" class="btn"
                  :class="form.statut_agree ? 'btn-primary' : 'btn-ghost'"
                  @click="form.statut_agree = true"
                >✓ Agréé</button>
                <button
                  type="button" class="btn"
                  :class="!form.statut_agree ? 'btn-amber' : 'btn-ghost'"
                  @click="form.statut_agree = false"
                >En attente</button>
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
    </Teleport>

    <!-- Confirm delete -->
    <Teleport to="body">
      <div class="modal-overlay" v-if="deleteTarget" @click.self="deleteTarget = null">
        <div class="modal" style="max-width:400px">
          <div class="modal-header"><h2>Confirmer la suppression</h2></div>
          <div class="modal-body">
            <div style="display:flex;align-items:center;gap:14px">
              <div class="fourn-avatar" :class="avatarClass(deleteTarget.raison_sociale)" style="width:48px;height:48px;font-size:16px;flex-shrink:0">
                {{ initiales(deleteTarget.raison_sociale) }}
              </div>
              <p style="color:var(--muted2)">
                Supprimer <strong style="color:var(--text)">{{ deleteTarget.raison_sociale }}</strong> ?
                <br><span style="font-size:12px">Cette action est irréversible.</span>
              </p>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-ghost" @click="deleteTarget = null">Annuler</button>
            <button class="btn btn-danger" @click="doDelete" :disabled="saving">
              {{ saving ? '…' : 'Supprimer définitivement' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useToast'

const { success, error: toastError } = useToast()

const fournisseurs = ref([])
const loading      = ref(true)
const error        = ref('')
const search       = ref('')
const filterStatut = ref('')
const showModal    = ref(false)
const editMode     = ref(false)
const saving       = ref(false)
const formError    = ref('')
const deleteTarget = ref(null)
const lotsInput    = ref('')
let editId = null

const getCurrentDateTime = () => {
  const tzoffset = new Date().getTimezoneOffset() * 60000
  return new Date(Date.now() - tzoffset).toISOString().slice(0, 16)
}

const defaultForm = () => ({
  raison_sociale: '', responsable_nom: '', telephone: '',
  email: '', nif: '', stat: '', rc: '', adresse: '',
  date_soumission: getCurrentDateTime(), statut_agree: false
})
const form = ref(defaultForm())

// ─── Helpers visuels ────────────────────────────────────────────────────────

function initiales(nom = '') {
  const words = nom.trim().split(/\s+/).filter(Boolean)
  if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase()
  return nom.slice(0, 2).toUpperCase()
}

function avatarClass(nom = '') {
  const letter = (nom[0] || ' ').toLowerCase()
  return `avatar-${letter}`
}

function formatDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}

// ─── Computed ────────────────────────────────────────────────────────────────

const filtered = computed(() => {
  let list = fournisseurs.value
  if (search.value) {
    const s = search.value.toLowerCase()
    list = list.filter(f =>
      f.raison_sociale?.toLowerCase().includes(s) ||
      f.responsable_nom?.toLowerCase().includes(s) ||
      f.email?.toLowerCase().includes(s) ||
      f.code_fournisseur?.toLowerCase().includes(s)
    )
  }
  if (filterStatut.value === 'agree')   list = list.filter(f =>  f.statut_agree)
  if (filterStatut.value === 'attente') list = list.filter(f => !f.statut_agree)
  return list
})

const total  = computed(() => fournisseurs.value.length)
const agrees = computed(() => fournisseurs.value.filter(f => f.statut_agree).length)

// ─── CRUD ────────────────────────────────────────────────────────────────────

async function fetchFournisseurs() {
  loading.value = true; error.value = ''
  try {
    const { data } = await api.get('/fournisseurs')
    fournisseurs.value = data
  } catch (e) {
    error.value = e.response?.data?.error || 'Erreur de chargement'
  } finally { loading.value = false }
}

function openModal(f = null) {
  formError.value = ''
  if (f && typeof f === 'object' && f.id_fournisseur) {
    editMode.value = true
    editId = f.id_fournisseur
    const formattedDate = f.date_soumission
      ? new Date(f.date_soumission).toISOString().slice(0, 16)
      : getCurrentDateTime()
    form.value = { ...defaultForm(), ...f, date_soumission: formattedDate }
    lotsInput.value = (f.lots_soumissionnes || []).join(', ')
  } else {
    editMode.value = false; editId = null
    form.value = defaultForm(); lotsInput.value = ''
  }
  showModal.value = true
}

function closeModal() { showModal.value = false }

async function saveForm() {
  formError.value = ''
  if (!form.value.raison_sociale)   { formError.value = 'La raison sociale est requise.'; return }
  if (!form.value.date_soumission)  { formError.value = 'La date de soumission est requise.'; return }

  const lots = lotsInput.value.split(',').map(l => parseInt(l.trim(), 10)).filter(n => !isNaN(n))
  if (!lots.length) { formError.value = 'Au moins un lot est requis.'; return }

  const payload = {
    ...form.value,
    date_soumission: new Date(form.value.date_soumission).toISOString(),
    lots_soumissionnes: lots
  }

  saving.value = true
  try {
    if (editMode.value) {
      const { data } = await api.put(`/fournisseurs/${editId}`, payload)
      const idx = fournisseurs.value.findIndex(f => f.id_fournisseur === editId)
      if (idx > -1) fournisseurs.value[idx] = data
      success('Fournisseur mis à jour.')
    } else {
      const { data } = await api.post('/fournisseurs', payload)
      fournisseurs.value.unshift(data)
      success('Fournisseur créé avec succès.')
    }
    closeModal()
  } catch (e) {
    formError.value = e.response?.data?.error || 'Erreur lors de la sauvegarde'
  } finally { saving.value = false }
}

function confirmDelete(f) { deleteTarget.value = f }

async function doDelete() {
  saving.value = true
  try {
    await api.delete(`/fournisseurs/${deleteTarget.value.id_fournisseur}`)
    fournisseurs.value = fournisseurs.value.filter(f => f.id_fournisseur !== deleteTarget.value.id_fournisseur)
    success(`${deleteTarget.value.raison_sociale} supprimé.`)
    deleteTarget.value = null
  } catch (e) {
    toastError(e.response?.data?.error || 'Erreur de suppression')
  } finally { saving.value = false }
}

onMounted(fetchFournisseurs)
</script>

<style scoped>
.filters-bar { display: flex; align-items: center; gap: 10px; padding: 12px 16px; flex-wrap: wrap; }
.filters-bar input { flex: 1; min-width: 200px; }
.filter-stats { display: flex; gap: 8px; flex-shrink: 0; }
.toggle-row { display: flex; gap: 8px; }
</style>