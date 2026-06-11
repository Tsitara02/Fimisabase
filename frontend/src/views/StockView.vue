<template>
  <div class="fade-up">
    <div class="page-header">
      <div>
        <h1>Stock & Articles</h1>
        <div class="sub">Gestion des articles · alertes seuil critique</div>
      </div>
      <button class="btn btn-primary" @click="openModal()">+ Nouvel article</button>
    </div>

    <!-- Stats bar -->
    <div class="stock-stats stagger">
      <div class="stat-pill" v-for="s in stockStats" :key="s.label">
        <div class="stat-val" :style="{color: s.color}">{{ s.val }}</div>
        <div class="stat-lab">{{ s.label }}</div>
      </div>
    </div>

    <!-- Alerts -->
    <div v-if="alertes.length" class="alert-banner">
      <span class="alert-icon">⚠</span>
      <strong>{{ alertes.length }} article(s) en dessous du seuil critique</strong>
      <span class="alert-list">{{ alertes.map(a=>a.designation).join(' · ') }}</span>
    </div>

    <div v-if="error" class="alert alert-danger">{{ error }}</div>
    <div v-if="successMsg" class="alert alert-success">{{ successMsg }}</div>

    <!-- Filters -->
    <div class="filters-bar card" style="margin-bottom:14px">
      <input v-model="search" placeholder="Rechercher un article…" />
      <select v-model="filterStatus" style="width:auto;min-width:160px">
        <option value="">Tous les statuts</option>
        <option value="ok">Stock OK</option>
        <option value="alerte">En alerte</option>
        <option value="rupture">Rupture</option>
      </select>
    </div>

    <!-- Table -->
    <div class="card" style="padding:0;overflow:hidden">
      <div v-if="loading" class="empty-state"><p>Chargement…</p></div>
      <div v-else-if="filtered.length === 0" class="empty-state">
        <div class="icon">⬡</div><p>Aucun article trouvé</p>
      </div>
      <table class="data-table" v-else>
        <thead>
          <tr>
            <th>Code</th>
            <th>Désignation</th>
            <th>Unité</th>
            <th>Stock actuel</th>
            <th>Seuil alerte</th>
            <th>Statut</th>
            <th style="text-align:right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in filtered" :key="a.id_article" :class="{'row-danger': stockStatut(a)==='rupture', 'row-warn': stockStatut(a)==='alerte'}">
            <td><span class="code-tag">{{ a.code_article || '—' }}</span></td>
            <td><strong>{{ a.designation }}</strong></td>
            <td class="muted">{{ a.unite_mesure }}</td>
            <td>
              <div class="stock-cell">
                <span class="stock-val" :style="{color: stockColor(a)}">{{ a.quantite_en_stock ?? '—' }}</span>
                <div class="mini-bar" v-if="a.seuil_alerte">
                  <div class="mini-fill" :style="{width: Math.min(100,(a.quantite_en_stock||0)/a.seuil_alerte*100)+'%', background: stockColor(a)}"></div>
                </div>
              </div>
            </td>
            <td class="muted">{{ a.seuil_alerte ?? '—' }}</td>
            <td>
              <span class="badge" :class="badgeClass(a)">{{ stockLabel(a) }}</span>
            </td>
            <td>
              <div class="actions">
                <button class="btn btn-ghost btn-sm" @click="openAjust(a)" title="Ajuster stock">↕</button>
                <button class="btn btn-ghost btn-sm btn-icon" @click="openModal(a)" title="Modifier">✎</button>
                <button class="btn btn-danger btn-sm btn-icon" @click="confirmDelete(a)" title="Supprimer">✕</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modal Article -->
    <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editMode ? 'Modifier l\'article' : 'Nouvel article' }}</h2>
          <button class="btn btn-ghost btn-icon" @click="closeModal">✕</button>
        </div>
        <div class="modal-body">
          <div class="form-row">
            <div class="form-group">
              <label>Code article</label>
              <input v-model="form.code_article" placeholder="ART-001" />
            </div>
            <div class="form-group">
              <label>Unité de mesure *</label>
              <input v-model="form.unite_mesure" placeholder="kg, pcs, l…" />
            </div>
          </div>
          <div class="form-group">
            <label>Désignation *</label>
            <input v-model="form.designation" placeholder="Nom complet de l'article" />
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Quantité en stock</label>
              <input v-model.number="form.quantite_en_stock" type="number" min="0" placeholder="0" />
            </div>
            <div class="form-group">
              <label>Seuil d'alerte</label>
              <input v-model.number="form.seuil_alerte" type="number" min="0" placeholder="Ex: 10" />
            </div>
          </div>
          <div v-if="formError" class="alert alert-danger">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Annuler</button>
          <button class="btn btn-primary" @click="saveForm" :disabled="saving">
            {{ saving ? '…' : (editMode ? 'Mettre à jour' : 'Créer') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Ajustement stock -->
    <div class="modal-overlay" v-if="ajustTarget" @click.self="ajustTarget=null">
      <div class="modal" style="max-width:400px">
        <div class="modal-header">
          <h2>Ajuster le stock</h2>
          <button class="btn btn-ghost btn-icon" @click="ajustTarget=null">✕</button>
        </div>
        <div class="modal-body">
          <div class="ajust-info">
            <div class="ajust-name">{{ ajustTarget.designation }}</div>
            <div class="ajust-current">Stock actuel : <strong :style="{color: stockColor(ajustTarget)}">{{ ajustTarget.quantite_en_stock ?? 0 }} {{ ajustTarget.unite_mesure }}</strong></div>
          </div>
          <div class="ajust-controls">
            <button class="btn btn-danger" @click="ajustDelta = Math.max(-999, ajustDelta - 1)">−</button>
            <div class="delta-display" :class="{positive: ajustDelta>0, negative: ajustDelta<0}">
              {{ ajustDelta > 0 ? '+' : '' }}{{ ajustDelta }}
            </div>
            <button class="btn btn-primary" @click="ajustDelta++">+</button>
          </div>
          <div class="ajust-preview">
            Nouveau stock : <strong>{{ Math.max(0,(ajustTarget.quantite_en_stock||0)+ajustDelta) }} {{ ajustTarget.unite_mesure }}</strong>
          </div>
          <div v-if="formError" class="alert alert-danger">{{ formError }}</div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="ajustTarget=null">Annuler</button>
          <button class="btn btn-primary" @click="doAjust" :disabled="saving || ajustDelta===0">
            {{ saving ? '…' : 'Confirmer' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Confirm delete -->
    <div class="modal-overlay" v-if="deleteTarget" @click.self="deleteTarget=null">
      <div class="modal" style="max-width:400px">
        <div class="modal-header"><h2>Confirmer la suppression</h2></div>
        <div class="modal-body">
          <p style="color:var(--muted2)">Supprimer <strong style="color:var(--text)">{{ deleteTarget.designation }}</strong> ? Cette action est irréversible.</p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="deleteTarget=null">Annuler</button>
          <button class="btn btn-danger" @click="doDelete" :disabled="saving">{{ saving ? '…' : 'Supprimer' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'

const articles = ref([])
const alertes  = ref([])
const loading  = ref(true)
const error    = ref('')
const successMsg = ref('')
const search   = ref('')
const filterStatus = ref('')
const showModal = ref(false)
const editMode  = ref(false)
const saving    = ref(false)
const formError = ref('')
const deleteTarget = ref(null)
const ajustTarget  = ref(null)
const ajustDelta   = ref(0)
let editId = null

const defaultForm = () => ({ code_article:'', designation:'', unite_mesure:'', quantite_en_stock: null, seuil_alerte: null })
const form = ref(defaultForm())

function stockStatut(a) {
  const q = a.quantite_en_stock ?? 0; const s = a.seuil_alerte ?? 0
  if (q === 0) return 'rupture'
  if (s > 0 && q <= s) return 'alerte'
  return 'ok'
}
function stockColor(a) {
  const st = stockStatut(a)
  return st === 'rupture' ? 'var(--red)' : st === 'alerte' ? 'var(--amber)' : 'var(--green)'
}
function stockLabel(a) {
  const st = stockStatut(a)
  return st === 'rupture' ? 'RUPTURE' : st === 'alerte' ? 'ALERTE' : 'OK'
}
function badgeClass(a) {
  const st = stockStatut(a)
  return st === 'rupture' ? 'badge-red' : st === 'alerte' ? 'badge-amber' : 'badge-green'
}

const filtered = computed(() => {
  let list = articles.value
  if (search.value) {
    const s = search.value.toLowerCase()
    list = list.filter(a => a.designation?.toLowerCase().includes(s) || a.code_article?.toLowerCase().includes(s))
  }
  if (filterStatus.value) list = list.filter(a => stockStatut(a) === filterStatus.value)
  return list
})

const stockStats = computed(() => [
  { label: 'Total articles', val: articles.value.length, color: 'var(--text)' },
  { label: 'Stock OK',       val: articles.value.filter(a=>stockStatut(a)==='ok').length,      color: 'var(--green)' },
  { label: 'En alerte',      val: articles.value.filter(a=>stockStatut(a)==='alerte').length,  color: 'var(--amber)' },
  { label: 'Rupture stock',  val: articles.value.filter(a=>stockStatut(a)==='rupture').length, color: 'var(--red)' },
])

async function fetchAll() {
  loading.value = true; error.value = ''
  try {
    const [artRes, alRes] = await Promise.all([
      api.get('/articles'),
      api.get('/dashboard/alertes-stock')
    ])
    articles.value = artRes.data
    alertes.value  = alRes.data
  } catch(e) {
    error.value = e.response?.data?.error || 'Erreur de chargement'
  } finally { loading.value = false }
}

function openModal(a = null) {
  formError.value = ''
  if (a) { editMode.value = true; editId = a.id_article; form.value = { ...defaultForm(), ...a } }
  else   { editMode.value = false; editId = null; form.value = defaultForm() }
  showModal.value = true
}
function closeModal() { showModal.value = false }

async function saveForm() {
  formError.value = ''
  if (!form.value.designation) { formError.value = 'La désignation est requise.'; return }
  if (!form.value.unite_mesure) { formError.value = "L'unité de mesure est requise."; return }
  saving.value = true
  try {
    if (editMode.value) {
      const { data } = await api.put(`/articles/${editId}`, form.value)
      const idx = articles.value.findIndex(a => a.id_article === editId)
      if (idx > -1) articles.value[idx] = data
    } else {
      const { data } = await api.post('/articles', form.value)
      articles.value.unshift(data)
    }
    closeModal(); flash(editMode.value ? 'Article mis à jour.' : 'Article créé.')
  } catch(e) {
    formError.value = e.response?.data?.error || 'Erreur'
  } finally { saving.value = false }
}

function openAjust(a) { ajustTarget.value = a; ajustDelta.value = 0; formError.value = '' }

async function doAjust() {
  saving.value = true; formError.value = ''
  try {
    const { data } = await api.post(`/articles/${ajustTarget.value.id_article}/ajuster-stock`, { delta: ajustDelta.value })
    const idx = articles.value.findIndex(a => a.id_article === ajustTarget.value.id_article)
    if (idx > -1) articles.value[idx] = data
    ajustTarget.value = null
    flash(`Stock ajusté (${ajustDelta.value > 0 ? '+' : ''}${ajustDelta.value}).`)
  } catch(e) {
    formError.value = e.response?.data?.error || 'Erreur'
  } finally { saving.value = false }
}

function confirmDelete(a) { deleteTarget.value = a }
async function doDelete() {
  saving.value = true
  try {
    await api.delete(`/articles/${deleteTarget.value.id_article}`)
    articles.value = articles.value.filter(a => a.id_article !== deleteTarget.value.id_article)
    deleteTarget.value = null; flash('Article supprimé.')
  } catch(e) { error.value = e.response?.data?.error || 'Erreur' }
  finally { saving.value = false }
}

import { useToast } from '@/composables/useToast'
const { success, error: toastError } = useToast()
// puis : success('Article créé.') / toastError('Erreur.')
onMounted(fetchAll)
</script>

<style scoped>
.stock-stats { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.stat-pill { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 12px 20px; display: flex; flex-direction: column; align-items: center; min-width: 110px; }
.stat-val { font-family: 'Bricolage Grotesque',sans-serif; font-size: 26px; font-weight: 800; }
.stat-lab { font-size: 11px; color: var(--muted2); text-transform: uppercase; letter-spacing: .04em; margin-top: 2px; }

.alert-banner {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  background: color-mix(in srgb,var(--amber) 10%,transparent);
  border: 1px solid color-mix(in srgb,var(--amber) 30%,transparent);
  color: var(--amber); border-radius: 10px; padding: 10px 16px; margin-bottom: 14px; font-size: 13px;
}
.alert-icon { font-size: 16px; }
.alert-list { color: var(--muted2); font-size: 12px; flex: 1; }

.filters-bar { display: flex; align-items: center; gap: 10px; padding: 10px 14px; }
.filters-bar input { flex: 1; }

.code-tag { font-family: monospace; font-size: 12px; background: var(--surface3); padding: 2px 7px; border-radius: 5px; color: var(--muted2); }
.stock-cell { display: flex; flex-direction: column; gap: 4px; }
.stock-val { font-family: 'Bricolage Grotesque',sans-serif; font-size: 16px; font-weight: 700; }
.mini-bar { height: 3px; background: var(--border); border-radius: 2px; width: 60px; overflow: hidden; }
.mini-fill { height: 100%; border-radius: 2px; transition: width .5s ease; }
.muted { color: var(--muted2); }
.actions { display: flex; gap: 4px; justify-content: flex-end; }
.row-danger td { background: color-mix(in srgb,var(--red) 4%,transparent); }
.row-warn td { background: color-mix(in srgb,var(--amber) 4%,transparent); }

.ajust-info { text-align: center; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
.ajust-name { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
.ajust-current { font-size: 13px; color: var(--muted2); }
.ajust-controls { display: flex; align-items: center; justify-content: center; gap: 20px; padding: 16px 0; }
.delta-display { font-family: 'Bricolage Grotesque',sans-serif; font-size: 36px; font-weight: 800; min-width: 80px; text-align: center; }
.delta-display.positive { color: var(--green); }
.delta-display.negative { color: var(--red); }
.ajust-preview { text-align: center; font-size: 13px; color: var(--muted2); padding-top: 8px; border-top: 1px solid var(--border); }
</style>
