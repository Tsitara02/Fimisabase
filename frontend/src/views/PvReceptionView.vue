<template>
  <div class="fade-up">
    <div class="page-header">
      <div>
        <h1>PV de Réception</h1>
        <div class="sub">Réception des livraisons · mise à jour automatique du stock</div>
      </div>
      <button class="btn btn-primary" @click="openModal()">+ Nouveau PV</button>
    </div>

    <!-- Filters -->
    <div class="filters-bar card">
      <input v-model="search" placeholder="Rechercher par numéro PV, fournisseur, site…" />
      <div class="filter-stats">
        <span class="badge badge-muted">{{ pvs.length }} PV total</span>
      </div>
    </div>

    <div v-if="error"      class="alert alert-danger"  style="margin-top:12px">{{ error }}</div>
    <div v-if="successMsg" class="alert alert-success" style="margin-top:12px">{{ successMsg }}</div>

    <!-- Liste -->
    <div class="card" style="margin-top:14px;padding:0;overflow:hidden">
      <div v-if="loading" class="empty-state"><p>Chargement…</p></div>
      <div v-else-if="filtered.length === 0" class="empty-state">
        <div class="icon">📦</div>
        <p>Aucun PV de réception. Commencez par valider un Bon de Commande.</p>
      </div>
      <table class="data-table" v-else>
        <thead>
          <tr>
            <th>N° PV</th>
            <th>Date réception</th>
            <th>Bon de commande</th>
            <th>Fournisseur</th>
            <th>Site</th>
            <th>Réceptionnaire</th>
            <th style="text-align:right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="pv in filtered" :key="pv.id_pv_reception">
            <td><span class="pv-numero">{{ pv.numero_pv }}</span></td>
            <td style="color:var(--muted2);font-size:12px;white-space:nowrap">
              {{ formatDate(pv.date_reception) }}
            </td>
            <td>
              <span class="code-tag" v-if="pv.bon_commande">
                {{ pv.bon_commande.numero_bc }}
              </span>
              <span v-else style="color:var(--muted2)">—</span>
            </td>
            <td style="font-size:12px">
              {{ pv.bon_commande?.fournisseur_ami?.raison_sociale || '—' }}
            </td>
            <td style="font-size:12px;color:var(--muted2)">
              {{ pv.commune_site || '—' }}
              <span v-if="pv.fokontany_site"> / {{ pv.fokontany_site }}</span>
            </td>
            <td style="font-size:12px">
              {{ pv.personnel_fimisa ? pv.personnel_fimisa.nom + ' ' + (pv.personnel_fimisa.prenom || '') : '—' }}
            </td>
            <td>
              <div class="actions">
                <button class="btn btn-ghost btn-sm" @click="openDetail(pv)" title="Voir les lignes">👁</button>
                <button class="btn btn-ghost btn-sm btn-icon" @click="openModal(pv)" title="Modifier">✎</button>
                <div class="sep-v"></div>
                <button class="btn btn-danger btn-sm btn-icon" @click="confirmDelete(pv)" title="Supprimer">🗑</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ══════════════════════════════════════════════════════════
         Modal Création / Édition
    ══════════════════════════════════════════════════════════ -->
    <div class="modal-overlay" v-if="showModal" @click.self="closeModal">
      <div class="modal" style="max-width:700px">
        <div class="modal-header">
          <h2>{{ editMode ? 'Modifier le PV' : 'Nouveau PV de Réception' }}</h2>
          <button class="btn btn-ghost btn-icon" @click="closeModal">✕</button>
        </div>
        <div class="modal-body">

          <!-- Ligne 1 : numéro + date -->
          <div class="form-row">
            <div class="form-group">
              <label>Numéro PV *</label>
              <input v-model="form.numero_pv" placeholder="PVR-2026-001" />
            </div>
            <div class="form-group">
              <label>Date de réception</label>
              <input type="date" v-model="form.date_reception" />
            </div>
          </div>

          <!-- Ligne 2 : BC + réceptionnaire -->
          <div class="form-row">
            <div class="form-group">
              <label>Bon de Commande (validé) *</label>
              <select v-model="form.id_bon_commande" @change="onBcChange">
                <option value="">— Choisir un BC validé —</option>
                <option v-for="bc in bcsValides" :key="bc.id_bon_commande" :value="bc.id_bon_commande">
                  {{ bc.numero_bc }} — {{ bc.fournisseur_ami?.raison_sociale || '' }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Réceptionnaire FIMISA</label>
              <select v-model="form.id_receptionnaire_fimisa">
                <option value="">— Choisir —</option>
                <option v-for="p in personnel" :key="p.id_personnel" :value="p.id_personnel">
                  {{ p.nom }} {{ p.prenom || '' }} — {{ p.poste_occupe }}
                </option>
              </select>
            </div>
          </div>

          <!-- Ligne 3 : site -->
          <div class="form-row">
            <div class="form-group">
              <label>Commune / Site</label>
              <input v-model="form.commune_site" placeholder="Commune de livraison" />
            </div>
            <div class="form-group">
              <label>Fokontany</label>
              <input v-model="form.fokontany_site" placeholder="Fokontany" />
            </div>
          </div>

          <!-- Lignes de réception -->
          <div class="lignes-section">
            <div class="lignes-header">
              <span style="font-size:12px;font-weight:600;color:var(--muted2);text-transform:uppercase;letter-spacing:.04em">
                Articles reçus
              </span>
              <button type="button" class="btn btn-ghost btn-sm" @click="addLigne">+ Ajouter un article</button>
            </div>

            <!-- Suggestion depuis le BC sélectionné -->
            <div class="bc-suggestion" v-if="bcLignesSuggestion.length && form.lignes.length === 0">
              <span style="font-size:12px;color:var(--muted2)">
                📋 Articles du BC sélectionné :
              </span>
              <button type="button" class="btn btn-ghost btn-sm" @click="importerDepuisBC">
                ↓ Importer les articles du BC
              </button>
            </div>

            <div class="lignes-table-wrap">
              <table class="data-table lignes-table">
                <thead>
                  <tr>
                    <th style="width:30%">Article *</th>
                    <th style="width:20%">Qté prévisionnelle</th>
                    <th style="width:20%">Qté réellement reçue *</th>
                    <th style="width:24%">Observations</th>
                    <th style="width:6%"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="form.lignes.length === 0">
                    <td colspan="5" class="lignes-empty">
                      Choisissez un BC puis cliquez "Importer les articles", ou ajoutez manuellement
                    </td>
                  </tr>
                  <tr v-for="(l, i) in form.lignes" :key="i">
                    <td>
                      <select v-model="l.id_article" class="ligne-input">
                        <option value="">— Choisir —</option>
                        <option v-for="a in articles" :key="a.id_article" :value="a.id_article">
                          {{ a.designation }} ({{ a.unite_mesure }})
                        </option>
                      </select>
                    </td>
                    <td>
                      <input v-model.number="l.quantite_previsionnelle" type="number" min="0" class="ligne-input" placeholder="Prévue" />
                    </td>
                    <td>
                      <input v-model.number="l.quantite_livree_site" type="number" min="0" class="ligne-input"
                        placeholder="Reçue"
                        :style="{ color: l.quantite_livree_site < l.quantite_previsionnelle ? 'var(--amber)' : 'var(--green)' }" />
                    </td>
                    <td>
                      <input v-model="l.observations" class="ligne-input" placeholder="RAS" />
                    </td>
                    <td>
                      <button type="button" class="btn btn-danger btn-icon btn-sm" @click="removeLigne(i)">✕</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Résumé quantités -->
            <div class="recap-row" v-if="form.lignes.length > 0">
              <div class="recap-item">
                <span class="recap-label">Articles</span>
                <span class="recap-val">{{ form.lignes.length }}</span>
              </div>
              <div class="recap-item">
                <span class="recap-label">Total prévu</span>
                <span class="recap-val">{{ totalPrevu }}</span>
              </div>
              <div class="recap-item">
                <span class="recap-label">Total reçu</span>
                <span class="recap-val" :style="{ color: totalRecu < totalPrevu ? 'var(--amber)' : 'var(--green)' }">
                  {{ totalRecu }}
                </span>
              </div>
              <div class="recap-item" v-if="totalPrevu > 0">
                <span class="recap-label">Taux réception</span>
                <span class="recap-val" :style="{ color: tauxReception < 100 ? 'var(--amber)' : 'var(--green)' }">
                  {{ tauxReception }}%
                </span>
              </div>
            </div>
          </div>

          <div v-if="formError" class="alert alert-danger">{{ formError }}</div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Annuler</button>
          <button class="btn btn-primary" @click="saveForm" :disabled="saving">
            {{ saving ? 'Enregistrement…' : (editMode ? 'Mettre à jour' : 'Créer le PV') }}
          </button>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════
         Modal Détail PV
    ══════════════════════════════════════════════════════════ -->
    <div class="modal-overlay" v-if="detailPV" @click.self="detailPV = null">
      <div class="modal" style="max-width:640px">
        <div class="modal-header">
          <h2>{{ detailPV.numero_pv }}</h2>
          <button class="btn btn-ghost btn-icon" @click="detailPV = null">✕</button>
        </div>
        <div class="modal-body">
          <!-- Infos -->
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-key">Bon de Commande</span>
              <span class="detail-val">{{ detailPV.bon_commande?.numero_bc || '—' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-key">Date réception</span>
              <span class="detail-val">{{ formatDate(detailPV.date_reception) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-key">Fournisseur</span>
              <span class="detail-val">{{ detailPV.bon_commande?.fournisseur_ami?.raison_sociale || '—' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-key">Site</span>
              <span class="detail-val">{{ detailPV.commune_site || '—' }} {{ detailPV.fokontany_site ? '/ ' + detailPV.fokontany_site : '' }}</span>
            </div>
          </div>

          <!-- Lignes -->
          <div style="margin-top:16px">
            <div style="font-size:12px;font-weight:600;color:var(--muted2);text-transform:uppercase;letter-spacing:.04em;margin-bottom:10px">
              Articles reçus
            </div>
            <div v-if="loadingLignes" class="empty-state" style="padding:20px"><p>Chargement…</p></div>
            <table class="data-table" v-else>
              <thead>
                <tr>
                  <th>Article</th>
                  <th>Prévu</th>
                  <th>Reçu</th>
                  <th>Écart</th>
                  <th>Observations</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="detailLignes.length === 0">
                  <td colspan="5" style="text-align:center;color:var(--muted);padding:16px">Aucune ligne</td>
                </tr>
                <tr v-for="l in detailLignes" :key="l.id_ligne_pvr">
                  <td>
                    <div style="font-weight:500">{{ l.article?.designation || '—' }}</div>
                    <div style="font-size:11px;color:var(--muted)">{{ l.article?.unite_mesure }}</div>
                  </td>
                  <td>{{ l.quantite_previsionnelle }}</td>
                  <td>
                    <strong :style="{ color: l.quantite_livree_site < l.quantite_previsionnelle ? 'var(--amber)' : 'var(--green)' }">
                      {{ l.quantite_livree_site }}
                    </strong>
                  </td>
                  <td>
                    <span :style="{ color: (l.quantite_livree_site - l.quantite_previsionnelle) < 0 ? 'var(--red)' : 'var(--green)' }">
                      {{ l.quantite_livree_site - l.quantite_previsionnelle > 0 ? '+' : '' }}{{ l.quantite_livree_site - l.quantite_previsionnelle }}
                    </span>
                  </td>
                  <td style="font-size:12px;color:var(--muted2)">{{ l.observations || '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Bouton valider stock -->
          <div class="validation-zone" v-if="!detailPV.stock_mis_a_jour">
            <div class="validation-zone-title">📦 Mise à jour du stock</div>
            <p style="font-size:13px;color:var(--muted2);margin-bottom:14px">
              Valider ce PV va ajouter les quantités reçues au stock de chaque article.
              Cette action est définitive.
            </p>
            <button class="btn btn-primary" @click="validerStock(detailPV.id_pv_reception)" :disabled="saving">
              {{ saving ? '…' : '✓ Valider et mettre à jour le stock' }}
            </button>
          </div>
          <div v-else class="validation-done">
            ✓ Stock mis à jour
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="detailPV = null">Fermer</button>
        </div>
      </div>
    </div>

    <!-- Confirm delete -->
    <div class="modal-overlay" v-if="deleteTarget" @click.self="deleteTarget = null">
      <div class="modal" style="max-width:400px">
        <div class="modal-header"><h2>Supprimer le PV</h2></div>
        <div class="modal-body">
          <p style="color:var(--muted2)">
            Supprimer <strong style="color:var(--text)">{{ deleteTarget.numero_pv }}</strong>
            et toutes ses lignes ?<br>
            <span style="color:var(--red);font-size:12px">⚠ Le stock ne sera pas recalculé.</span>
          </p>
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

// ─── State ────────────────────────────────────────────────────────────────────
const pvs          = ref([])
const bcsValides   = ref([])
const personnel    = ref([])
const articles     = ref([])
const loading      = ref(true)
const loadingLignes = ref(false)
const error        = ref('')
const successMsg   = ref('')
const search       = ref('')
const showModal    = ref(false)
const editMode     = ref(false)
const saving       = ref(false)
const formError    = ref('')
const deleteTarget = ref(null)
const detailPV     = ref(null)
const detailLignes = ref([])
const bcLignesSuggestion = ref([])
let editId = null

const defaultForm = () => ({
  numero_pv:                '',
  date_reception:           new Date().toISOString().slice(0, 10),
  id_bon_commande:          '',
  id_receptionnaire_fimisa: '',
  commune_site:             '',
  fokontany_site:           '',
  lignes:                   []
})
const form = ref(defaultForm())

// ─── Helpers ──────────────────────────────────────────────────────────────────
function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}
function flash(msg) {
  successMsg.value = msg
  setTimeout(() => { successMsg.value = '' }, 3500)
}

// ─── Computed ─────────────────────────────────────────────────────────────────
const filtered = computed(() => {
  if (!search.value) return pvs.value
  const s = search.value.toLowerCase()
  return pvs.value.filter(p =>
    p.numero_pv?.toLowerCase().includes(s) ||
    p.bon_commande?.numero_bc?.toLowerCase().includes(s) ||
    p.bon_commande?.fournisseur_ami?.raison_sociale?.toLowerCase().includes(s) ||
    p.commune_site?.toLowerCase().includes(s)
  )
})
const totalPrevu  = computed(() => form.value.lignes.reduce((s, l) => s + (l.quantite_previsionnelle || 0), 0))
const totalRecu   = computed(() => form.value.lignes.reduce((s, l) => s + (l.quantite_livree_site || 0), 0))
const tauxReception = computed(() => {
  if (!totalPrevu.value) return 0
  return Math.round((totalRecu.value / totalPrevu.value) * 100)
})

// ─── Chargement ───────────────────────────────────────────────────────────────
async function fetchAll() {
  loading.value = true; error.value = ''
  try {
    const [pvRes, bcRes, persRes, artRes] = await Promise.all([
      api.get('/pv-reception'),
      api.get('/select/bons-commande-valides'),
      api.get('/select/personnel'),
      api.get('/articles'),
    ])
    pvs.value       = pvRes.data
    bcsValides.value = bcRes.data
    personnel.value  = persRes.data
    articles.value   = artRes.data
  } catch (e) {
    error.value = e.response?.data?.error || 'Erreur de chargement'
  } finally { loading.value = false }
}

// ─── Modal ────────────────────────────────────────────────────────────────────
function openModal(pv = null) {
  formError.value = ''
  bcLignesSuggestion.value = []
  if (pv) {
    editMode.value = true; editId = pv.id_pv_reception
    form.value = {
      numero_pv:                pv.numero_pv,
      date_reception:           pv.date_reception || new Date().toISOString().slice(0, 10),
      id_bon_commande:          pv.id_bon_commande || '',
      id_receptionnaire_fimisa: pv.id_receptionnaire_fimisa || '',
      commune_site:             pv.commune_site || '',
      fokontany_site:           pv.fokontany_site || '',
      lignes:                   []
    }
    api.get(`/pv-reception/${pv.id_pv_reception}`).then(({ data }) => {
      form.value.lignes = (data.lignes || []).map(l => ({ ...l }))
    }).catch(() => {})
  } else {
    editMode.value = false; editId = null
    form.value = defaultForm()
  }
  showModal.value = true
}
function closeModal() { showModal.value = false }

// Quand on change le BC sélectionné → charger les lignes pour suggestion
function onBcChange() {
  const bc = bcsValides.value.find(b => b.id_bon_commande === form.value.id_bon_commande)
  bcLignesSuggestion.value = bc?.ligne_commande || []
}

// Importer les articles du BC comme base de lignes réception
function importerDepuisBC() {
  form.value.lignes = bcLignesSuggestion.value.map(l => ({
    id_article:              '',
    quantite_previsionnelle: l.quantite_commandee || 0,
    quantite_livree_site:    l.quantite_commandee || 0,
    observations:            ''
  }))
}

function addLigne() {
  form.value.lignes.push({ id_article: '', quantite_previsionnelle: 0, quantite_livree_site: 0, observations: '' })
}
function removeLigne(i) { form.value.lignes.splice(i, 1) }

async function saveForm() {
  formError.value = ''
  if (!form.value.numero_pv.trim()) { formError.value = 'Le numéro PV est requis.'; return }
  if (!form.value.id_bon_commande)  { formError.value = 'Choisissez un Bon de Commande.'; return }
  if (form.value.lignes.length === 0) { formError.value = 'Ajoutez au moins un article reçu.'; return }
  const invalid = form.value.lignes.find(l => !l.id_article)
  if (invalid) { formError.value = 'Chaque ligne doit avoir un article sélectionné.'; return }

  const payload = {
    ...form.value,
    id_bon_commande:          form.value.id_bon_commande || null,
    id_receptionnaire_fimisa: form.value.id_receptionnaire_fimisa || null,
  }

  saving.value = true
  try {
    if (editMode.value) {
      await api.put(`/pv-reception/${editId}`, payload)
      flash('PV mis à jour.')
    } else {
      await api.post('/pv-reception', payload)
      flash('PV créé. N\'oubliez pas de valider le stock depuis le détail.')
    }
    closeModal()
    await fetchAll()
  } catch (e) {
    formError.value = e.response?.data?.error || 'Erreur lors de la sauvegarde'
  } finally { saving.value = false }
}

// ─── Détail ───────────────────────────────────────────────────────────────────
async function openDetail(pv) {
  detailPV.value = pv; detailLignes.value = []; loadingLignes.value = true
  try {
    const { data } = await api.get(`/pv-reception/${pv.id_pv_reception}`)
    detailLignes.value = data.lignes || []
  } catch (e) {
    detailLignes.value = []
  } finally { loadingLignes.value = false }
}

// ─── Valider stock ────────────────────────────────────────────────────────────
async function validerStock(id_pv) {
  saving.value = true
  try {
    const { data } = await api.post(`/pv-reception/${id_pv}/valider`)
    flash('✓ ' + data.message)
    // Marquer comme validé localement
    if (detailPV.value) detailPV.value = { ...detailPV.value, stock_mis_a_jour: true }
    const idx = pvs.value.findIndex(p => p.id_pv_reception === id_pv)
    if (idx > -1) pvs.value[idx] = { ...pvs.value[idx], stock_mis_a_jour: true }
  } catch (e) {
    error.value = e.response?.data?.error || 'Erreur lors de la mise à jour du stock'
  } finally { saving.value = false }
}

// ─── Suppression ─────────────────────────────────────────────────────────────
function confirmDelete(pv) { deleteTarget.value = pv }
async function doDelete() {
  saving.value = true
  try {
    await api.delete(`/pv-reception/${deleteTarget.value.id_pv_reception}`)
    flash(`PV ${deleteTarget.value.numero_pv} supprimé.`)
    deleteTarget.value = null
    await fetchAll()
  } catch (e) {
    error.value = e.response?.data?.error || 'Erreur de suppression'
  } finally { saving.value = false }
}

onMounted(fetchAll)
</script>

<style scoped>
.filters-bar { display: flex; align-items: center; gap: 10px; padding: 12px 16px; flex-wrap: wrap; }
.filters-bar input { flex: 1; min-width: 200px; }
.filter-stats { display: flex; gap: 8px; flex-shrink: 0; }

.pv-numero { font-family: monospace; font-size: 13px; font-weight: 700; color: var(--teal); }
.code-tag { font-family: monospace; font-size: 11px; background: var(--surface3); padding: 2px 7px; border-radius: 5px; color: var(--muted2); }
.actions { display: flex; gap: 3px; justify-content: flex-end; align-items: center; }
.sep-v { width: 1px; background: var(--border); margin: 0 2px; align-self: stretch; }

/* Lignes */
.lignes-section { background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.lignes-header  { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid var(--border); }
.bc-suggestion  { display: flex; align-items: center; justify-content: space-between; padding: 8px 14px; background: color-mix(in srgb,var(--blue) 8%,transparent); border-bottom: 1px solid var(--border); }
.lignes-table-wrap { overflow-x: auto; max-height: 260px; overflow-y: auto; }
.lignes-table   { min-width: 540px; }
.lignes-table td { padding: 7px 10px; }
.lignes-empty   { text-align: center; color: var(--muted); font-size: 12px; padding: 20px !important; }
.ligne-input    { background: var(--surface3); border: 1px solid var(--border); padding: 6px 9px; font-size: 12px; width: 100%; border-radius: 6px; color: var(--text); }
.ligne-input:focus { border-color: var(--teal); outline: none; }

/* Récap */
.recap-row   { display: flex; gap: 1px; border-top: 1px solid var(--border); }
.recap-item  { flex: 1; padding: 10px 14px; background: var(--surface3); text-align: center; }
.recap-label { display: block; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); margin-bottom: 3px; }
.recap-val   { font-family: 'Bricolage Grotesque',sans-serif; font-size: 18px; font-weight: 800; }

/* Détail */
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.detail-item { background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; }
.detail-key  { display: block; font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 4px; }
.detail-val  { font-size: 14px; font-weight: 500; }

/* Validation stock */
.validation-zone { background: color-mix(in srgb,var(--teal) 8%,transparent); border: 1px solid color-mix(in srgb,var(--teal) 25%,transparent); border-radius: 10px; padding: 16px; margin-top: 12px; }
.validation-zone-title { font-size: 12px; font-weight: 700; color: var(--teal); text-transform: uppercase; letter-spacing: .06em; margin-bottom: 8px; }
.validation-done { background: color-mix(in srgb,var(--green) 10%,transparent); border: 1px solid color-mix(in srgb,var(--green) 25%,transparent); border-radius: 10px; padding: 12px 16px; margin-top: 12px; color: var(--green); font-weight: 600; font-size: 13px; }

@media (max-width: 640px) {
  .detail-grid { grid-template-columns: 1fr; }
  .recap-row { flex-wrap: wrap; }
  .recap-item { min-width: 50%; }
}
</style>
