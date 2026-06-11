<template>
  <div class="fade-up">
    <div class="page-header">
      <div>
        <h1>Bons de Commande</h1>
        <div class="sub">Gestion des achats fournisseurs AMI</div>
      </div>
      <button class="btn btn-primary" @click="openModal()">+ Nouveau BC</button>
    </div>

    <!-- Filters -->
    <div class="filters-bar card">
      <input v-model="search" placeholder="Rechercher par numéro BC, fournisseur…" />
      <select v-model="filterStatut" style="width:auto;min-width:150px">
        <option value="">Tous les statuts</option>
        <option value="en_attente">En attente</option>
        <option value="validé">Validé</option>
        <option value="refusé">Refusé</option>
      </select>
      <div class="filter-stats">
        <span class="badge badge-amber">{{ enAttente }} en attente</span>
        <span class="badge badge-green">{{ valides }} validés</span>
        <span class="badge badge-muted">{{ total }} total</span>
      </div>
    </div>

    <!-- Alerts -->
    <div v-if="error"      class="alert alert-danger"  style="margin-top:12px">{{ error }}</div>
    <div v-if="successMsg" class="alert alert-success" style="margin-top:12px">{{ successMsg }}</div>

    <!-- Table -->
    <div class="card" style="margin-top:14px;padding:0;overflow:hidden">
      <div v-if="loading" class="empty-state"><p>Chargement…</p></div>
      <div v-else-if="filtered.length === 0" class="empty-state">
        <div class="icon">📋</div>
        <p>Aucun bon de commande. Cliquez "+ Nouveau BC" pour commencer.</p>
      </div>
      <table class="data-table" v-else>
        <thead>
          <tr>
            <th>N° BC</th>
            <th>Date</th>
            <th>Fournisseur</th>
            <th>Activité</th>
            <th>Montant</th>
            <th>Statut</th>
            <th style="text-align:right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="bc in filtered" :key="bc.id_bon_commande">
            <td><span class="bc-numero">{{ bc.numero_bc }}</span></td>
            <td style="color:var(--muted2);font-size:12px;white-space:nowrap">{{ formatDate(bc.date_commande) }}</td>
            <td>
              <div class="fourn-cell">
                <div class="fourn-ava-sm" :class="avatarClass(bc.fournisseur_ami?.raison_sociale)">
                  {{ initiales(bc.fournisseur_ami?.raison_sociale) }}
                </div>
                <span>{{ bc.fournisseur_ami?.raison_sociale || '—' }}</span>
              </div>
            </td>
            <td>
              <span class="code-tag" v-if="bc.activite_cadre_logique">
                {{ bc.activite_cadre_logique.code_activite }}
              </span>
              <span v-else style="color:var(--muted2)">—</span>
            </td>
            <td><strong>{{ formatMontant(bc.montant_total) }}</strong></td>
            <td>
              <span class="badge" :class="statutClass(bc.statut_validation)">
                {{ statutLabel(bc.statut_validation) }}
              </span>
            </td>
            <td>
              <div class="actions">
                <button class="btn btn-ghost btn-sm" @click="openDetail(bc)" title="Détails / Lignes">👁</button>
                <button class="btn btn-ghost btn-sm btn-icon" @click="openModal(bc)" title="Modifier"
                  :disabled="bc.statut_validation === 'validé'">✎</button>
                <template v-if="bc.statut_validation === 'en_attente'">
                  <button class="btn btn-ghost btn-sm" style="color:var(--green)" @click="valider(bc.id_bon_commande,'validé')" title="Valider">✓</button>
                  <button class="btn btn-ghost btn-sm" style="color:var(--red)"   @click="valider(bc.id_bon_commande,'refusé')" title="Refuser">✕</button>
                </template>
                <div class="sep-v"></div>
                <button class="btn btn-danger btn-sm btn-icon" @click="confirmDelete(bc)"
                  :disabled="bc.statut_validation === 'validé'" title="Supprimer">🗑</button>
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
      <div class="modal" style="max-width:680px">
        <div class="modal-header">
          <h2>{{ editMode ? 'Modifier le BC' : 'Nouveau Bon de Commande' }}</h2>
          <button class="btn btn-ghost btn-icon" @click="closeModal">✕</button>
        </div>

        <div class="modal-body">
          <!-- Ligne 1 : numéro + date -->
          <div class="form-row">
            <div class="form-group">
              <label>Numéro BC *</label>
              <input v-model="form.numero_bc" placeholder="BC-2026-001" />
            </div>
            <div class="form-group">
              <label>Date de commande</label>
              <input type="date" v-model="form.date_commande" />
            </div>
          </div>

          <!-- Ligne 2 : fournisseur + activité -->
          <div class="form-row">
            <div class="form-group">
              <label>Fournisseur AMI</label>
              <select v-model="form.id_fournisseur">
                <option value="">— Choisir —</option>
                <option v-for="f in fournisseurs" :key="f.id_fournisseur" :value="f.id_fournisseur">
                  {{ f.raison_sociale }}{{ f.statut_agree ? ' ✓' : '' }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Activité concernée</label>
              <select v-model="form.id_activite">
                <option value="">— Choisir —</option>
                <option v-for="a in activites" :key="a.id_activite" :value="a.id_activite">
                  {{ a.code_activite }} — {{ truncate(a.description, 45) }}
                </option>
              </select>
            </div>
          </div>

          <!-- Lignes de commande -->
          <div class="lignes-section">
            <div class="lignes-header">
              <span style="font-size:12px;font-weight:600;color:var(--muted2);text-transform:uppercase;letter-spacing:.04em">
                Articles commandés
              </span>
              <button type="button" class="btn btn-ghost btn-sm" @click="addLigne">+ Ajouter une ligne</button>
            </div>

            <div class="lignes-table-wrap">
              <table class="data-table lignes-table">
                <thead>
                  <tr>
                    <th style="width:42%">Désignation *</th>
                    <th style="width:14%">Quantité *</th>
                    <th style="width:20%">Prix unitaire (Ar) *</th>
                    <th style="width:18%">Total</th>
                    <th style="width:6%"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="form.lignes.length === 0">
                    <td colspan="5" class="lignes-empty">Cliquez "+ Ajouter une ligne" pour commencer</td>
                  </tr>
                  <tr v-for="(l, i) in form.lignes" :key="i">
                    <td><input v-model="l.designation_article" placeholder="Nom de l'article" class="ligne-input" /></td>
                    <td><input v-model.number="l.quantite_commandee" type="number" min="1" class="ligne-input" @input="calcTotal(l)" /></td>
                    <td><input v-model.number="l.prix_unitaire" type="number" min="0" step="1" class="ligne-input" @input="calcTotal(l)" /></td>
                    <td class="ligne-total">{{ formatMontant(l.prix_total) }}</td>
                    <td>
                      <button type="button" class="btn btn-danger btn-icon btn-sm" @click="removeLigne(i)">✕</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Total général -->
            <div class="montant-total-row">
              <span class="montant-label">Montant total</span>
              <span class="montant-val">{{ formatMontant(montantTotal) }}</span>
            </div>
          </div>

          <div v-if="formError" class="alert alert-danger">{{ formError }}</div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-ghost" @click="closeModal">Annuler</button>
          <button class="btn btn-primary" @click="saveForm" :disabled="saving">
            {{ saving ? 'Enregistrement…' : (editMode ? 'Mettre à jour' : 'Créer le BC') }}
          </button>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════
         Modal Détail / Lignes
    ══════════════════════════════════════════════════════════ -->
    <div class="modal-overlay" v-if="detailBC" @click.self="detailBC = null">
      <div class="modal" style="max-width:620px">
        <div class="modal-header">
          <div style="display:flex;align-items:center;gap:10px">
            <h2>{{ detailBC.numero_bc }}</h2>
            <span class="badge" :class="statutClass(detailBC.statut_validation)">
              {{ statutLabel(detailBC.statut_validation) }}
            </span>
          </div>
          <button class="btn btn-ghost btn-icon" @click="detailBC = null">✕</button>
        </div>
        <div class="modal-body">
          <!-- Infos générales -->
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-key">Fournisseur</span>
              <span class="detail-val">{{ detailBC.fournisseur_ami?.raison_sociale || '—' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-key">Date commande</span>
              <span class="detail-val">{{ formatDate(detailBC.date_commande) }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-key">Activité</span>
              <span class="detail-val">{{ detailBC.activite_cadre_logique?.code_activite || '—' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-key">Montant total</span>
              <span class="detail-val" style="color:var(--teal);font-weight:700;font-size:16px">
                {{ formatMontant(detailBC.montant_total) }}
              </span>
            </div>
          </div>

          <!-- Lignes -->
          <div style="margin-top:16px">
            <div style="font-size:12px;font-weight:600;color:var(--muted2);text-transform:uppercase;letter-spacing:.04em;margin-bottom:10px">
              Lignes de commande
            </div>
            <div v-if="loadingLignes" style="color:var(--muted);font-size:13px;padding:12px;text-align:center">
              Chargement des lignes…
            </div>
            <table class="data-table" v-else>
              <thead>
                <tr><th>Article</th><th>Qté</th><th>Prix unit.</th><th>Total ligne</th></tr>
              </thead>
              <tbody>
                <tr v-if="detailLignes.length === 0">
                  <td colspan="4" style="text-align:center;color:var(--muted);padding:16px">Aucune ligne enregistrée</td>
                </tr>
                <tr v-for="l in detailLignes" :key="l.id_ligne_bc">
                  <td>{{ l.designation_article }}</td>
                  <td><strong>{{ l.quantite_commandee }}</strong></td>
                  <td style="color:var(--muted2);font-size:12px">{{ formatMontant(l.prix_unitaire) }}</td>
                  <td><strong style="color:var(--teal)">{{ formatMontant(l.prix_total) }}</strong></td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Zone validation si en attente -->
          <div class="validation-zone" v-if="detailBC.statut_validation === 'en_attente'">
            <div class="validation-zone-title">⚡ Décision de validation</div>
            <div style="display:flex;gap:10px;flex-wrap:wrap">
              <button class="btn btn-primary" @click="valider(detailBC.id_bon_commande,'validé')" :disabled="saving">
                ✓ Valider ce BC
              </button>
              <button class="btn btn-danger" @click="valider(detailBC.id_bon_commande,'refusé')" :disabled="saving">
                ✕ Refuser ce BC
              </button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="detailBC = null">Fermer</button>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════════════════════
         Modal Confirmation suppression
    ══════════════════════════════════════════════════════════ -->
    <div class="modal-overlay" v-if="deleteTarget" @click.self="deleteTarget = null">
      <div class="modal" style="max-width:400px">
        <div class="modal-header"><h2>Supprimer le BC</h2></div>
        <div class="modal-body">
          <p style="color:var(--muted2)">
            Supprimer <strong style="color:var(--text)">{{ deleteTarget.numero_bc }}</strong>
            et toutes ses lignes ?<br>
            <span style="font-size:12px">Cette action est irréversible.</span>
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn btn-ghost" @click="deleteTarget = null">Annuler</button>
          <button class="btn btn-danger" @click="doDelete" :disabled="saving">
            {{ saving ? '…' : 'Supprimer définitivement' }}
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
const bcs           = ref([])
const fournisseurs  = ref([])
const activites     = ref([])
const loading       = ref(true)
const loadingLignes = ref(false)
const error         = ref('')
const successMsg    = ref('')
const search        = ref('')
const filterStatut  = ref('')
const showModal     = ref(false)
const editMode      = ref(false)
const saving        = ref(false)
const formError     = ref('')
const deleteTarget  = ref(null)
const detailBC      = ref(null)
const detailLignes  = ref([])
let editId = null

const defaultForm = () => ({
  numero_bc:         '',
  date_commande:     new Date().toISOString().slice(0, 10),
  id_fournisseur:    '',
  id_activite:       '',
  statut_validation: 'en_attente',
  lignes:            []
})
const form = ref(defaultForm())

// ─── Helpers ──────────────────────────────────────────────────────────────────
function initiales(nom) {
  if (!nom) return '?'
  const w = nom.trim().split(/\s+/).filter(Boolean)
  return w.length >= 2 ? (w[0][0] + w[1][0]).toUpperCase() : nom.slice(0, 2).toUpperCase()
}
function avatarClass(nom) {
  const l = ((nom || ' ')[0]).toLowerCase()
  const map = { a:'teal',b:'teal',c:'teal', d:'blue',e:'blue',f:'blue', g:'purple',h:'purple',i:'purple',
                j:'amber',k:'amber',l:'amber', m:'green',n:'green',o:'green', p:'blue',q:'blue',r:'blue',
                s:'blue',t:'blue',u:'blue', v:'purple',w:'purple',x:'purple',y:'muted',z:'muted' }
  return 'avatar-' + l
}
function truncate(str, n) { return str && str.length > n ? str.slice(0, n) + '…' : str || '' }
function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}
function formatMontant(m) {
  if (m === null || m === undefined || m === '') return '—'
  return new Intl.NumberFormat('fr-FR').format(m) + ' Ar'
}
function statutClass(s) {
  return { 'en_attente': 'badge-amber', 'validé': 'badge-green', 'refusé': 'badge-red' }[s] || 'badge-muted'
}
function statutLabel(s) {
  return { 'en_attente': '⏳ En attente', 'validé': '✓ Validé', 'refusé': '✕ Refusé' }[s] || s || '—'
}
function calcTotal(l) {
  l.prix_total = Math.round((l.quantite_commandee || 0) * (l.prix_unitaire || 0))
}
function flash(msg) {
  successMsg.value = msg
  setTimeout(() => { successMsg.value = '' }, 3500)
}

// ─── Computed ─────────────────────────────────────────────────────────────────
const filtered = computed(() => {
  let list = bcs.value
  if (search.value) {
    const s = search.value.toLowerCase()
    list = list.filter(b =>
      b.numero_bc?.toLowerCase().includes(s) ||
      b.fournisseur_ami?.raison_sociale?.toLowerCase().includes(s)
    )
  }
  if (filterStatut.value) list = list.filter(b => b.statut_validation === filterStatut.value)
  return list
})
const total      = computed(() => bcs.value.length)
const enAttente  = computed(() => bcs.value.filter(b => b.statut_validation === 'en_attente').length)
const valides    = computed(() => bcs.value.filter(b => b.statut_validation === 'validé').length)
const montantTotal = computed(() => form.value.lignes.reduce((s, l) => s + (l.prix_total || 0), 0))

// ─── Chargement ───────────────────────────────────────────────────────────────
async function fetchAll() {
  loading.value = true; error.value = ''
  try {
    const [bcRes, fRes, aRes] = await Promise.all([
      api.get('/bons-commande'),
      api.get('/select/fournisseurs'),
      api.get('/select/activites'),
    ])
    bcs.value          = bcRes.data
    fournisseurs.value = fRes.data
    activites.value    = aRes.data
  } catch (e) {
    error.value = e.response?.data?.error || 'Erreur de chargement des données'
  } finally {
    loading.value = false
  }
}

// ─── Modal création/édition ───────────────────────────────────────────────────
function openModal(bc = null) {
  formError.value = ''
  if (bc) {
    editMode.value = true
    editId = bc.id_bon_commande
    form.value = {
      numero_bc:         bc.numero_bc,
      date_commande:     bc.date_commande || new Date().toISOString().slice(0, 10),
      id_fournisseur:    bc.id_fournisseur  || '',
      id_activite:       bc.id_activite     || '',
      statut_validation: bc.statut_validation,
      lignes:            []
    }
    // Charger les lignes existantes
    api.get(`/bons-commande/${bc.id_bon_commande}`).then(({ data }) => {
      form.value.lignes = (data.lignes || []).map(l => ({ ...l }))
    }).catch(() => {})
  } else {
    editMode.value = false
    editId = null
    form.value = defaultForm()
  }
  showModal.value = true
}
function closeModal() { showModal.value = false }

function addLigne() {
  form.value.lignes.push({ designation_article: '', quantite_commandee: 1, prix_unitaire: 0, prix_total: 0 })
}
function removeLigne(i) { form.value.lignes.splice(i, 1) }

async function saveForm() {
  formError.value = ''
  if (!form.value.numero_bc.trim()) {
    formError.value = 'Le numéro BC est requis.'; return
  }
  if (form.value.lignes.length === 0) {
    formError.value = 'Ajoutez au moins une ligne de commande.'; return
  }
  const invalid = form.value.lignes.find(l =>
    !l.designation_article || !l.quantite_commandee || l.prix_unitaire === null || l.prix_unitaire === ''
  )
  if (invalid) {
    formError.value = 'Chaque ligne doit avoir une désignation, une quantité et un prix unitaire.'; return
  }

  const payload = {
    ...form.value,
    id_fournisseur: form.value.id_fournisseur || null,
    id_activite:    form.value.id_activite    || null,
  }

  saving.value = true
  try {
    if (editMode.value) {
      await api.put(`/bons-commande/${editId}`, payload)
      flash('Bon de commande mis à jour.')
    } else {
      await api.post('/bons-commande', payload)
      flash('Bon de commande créé avec succès.')
    }
    closeModal()
    await fetchAll()
  } catch (e) {
    formError.value = e.response?.data?.error || 'Erreur lors de la sauvegarde'
  } finally {
    saving.value = false
  }
}

// ─── Détail ───────────────────────────────────────────────────────────────────
async function openDetail(bc) {
  detailBC.value = bc
  detailLignes.value = []
  loadingLignes.value = true
  try {
    const { data } = await api.get(`/bons-commande/${bc.id_bon_commande}`)
    detailLignes.value = data.lignes || []
  } catch (e) {
    detailLignes.value = []
  } finally {
    loadingLignes.value = false
  }
}

// ─── Validation ───────────────────────────────────────────────────────────────
async function valider(id, statut) {
  saving.value = true
  try {
    await api.post(`/bons-commande/${id}/valider`, { statut })
    flash(statut === 'validé' ? '✓ BC validé avec succès.' : 'BC refusé.')
    if (detailBC.value?.id_bon_commande === id) {
      detailBC.value = { ...detailBC.value, statut_validation: statut }
    }
    await fetchAll()
  } catch (e) {
    error.value = e.response?.data?.error || 'Erreur de validation'
  } finally {
    saving.value = false
  }
}

// ─── Suppression ─────────────────────────────────────────────────────────────
function confirmDelete(bc) { deleteTarget.value = bc }
async function doDelete() {
  saving.value = true
  try {
    await api.delete(`/bons-commande/${deleteTarget.value.id_bon_commande}`)
    flash(`BC ${deleteTarget.value.numero_bc} supprimé.`)
    deleteTarget.value = null
    await fetchAll()
  } catch (e) {
    error.value = e.response?.data?.error || 'Erreur de suppression'
  } finally {
    saving.value = false
  }
}

onMounted(fetchAll)
</script>

<style scoped>
/* Filters */
.filters-bar { display: flex; align-items: center; gap: 10px; padding: 12px 16px; flex-wrap: wrap; }
.filters-bar input { flex: 1; min-width: 180px; }
.filter-stats { display: flex; gap: 8px; flex-shrink: 0; }

/* Table */
.bc-numero { font-family: monospace; font-size: 13px; font-weight: 700; color: var(--teal); }
.fourn-cell { display: flex; align-items: center; gap: 8px; }
.fourn-ava-sm {
  width: 26px; height: 26px; border-radius: 6px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 800;
  background: color-mix(in srgb,var(--teal) 18%,transparent);
  color: var(--teal);
}
.code-tag { font-family: monospace; font-size: 11px; background: var(--surface3); padding: 2px 7px; border-radius: 5px; color: var(--muted2); }
.actions { display: flex; gap: 3px; justify-content: flex-end; align-items: center; }
.sep-v { width: 1px; background: var(--border); margin: 0 2px; align-self: stretch; }

/* Lignes commande dans le formulaire */
.lignes-section { background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.lignes-header  { display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; border-bottom: 1px solid var(--border); }
.lignes-table-wrap { overflow-x: auto; max-height: 280px; overflow-y: auto; }
.lignes-table   { min-width: 500px; }
.lignes-table td { padding: 7px 10px; }
.lignes-empty   { text-align: center; color: var(--muted); font-size: 12px; padding: 20px !important; }
.ligne-input    { background: var(--surface3); border: 1px solid var(--border); padding: 6px 9px; font-size: 12px; width: 100%; border-radius: 6px; color: var(--text); }
.ligne-input:focus { border-color: var(--teal); outline: none; box-shadow: 0 0 0 2px color-mix(in srgb,var(--teal) 15%,transparent); }
.ligne-total    { font-size: 13px; font-weight: 700; color: var(--teal); white-space: nowrap; }
.montant-total-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border-top: 1px solid var(--border); background: var(--surface3); }
.montant-label  { font-size: 12px; font-weight: 600; color: var(--muted2); text-transform: uppercase; letter-spacing: .05em; }
.montant-val    { font-family: 'Bricolage Grotesque',sans-serif; font-size: 22px; font-weight: 800; color: var(--teal); }

/* Détail modal */
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.detail-item { background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; }
.detail-key  { display: block; font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 4px; }
.detail-val  { font-size: 14px; font-weight: 500; }

/* Zone validation */
.validation-zone { background: color-mix(in srgb,var(--amber) 8%,transparent); border: 1px solid color-mix(in srgb,var(--amber) 25%,transparent); border-radius: 10px; padding: 16px; margin-top: 12px; }
.validation-zone-title { font-size: 12px; font-weight: 700; color: var(--amber); text-transform: uppercase; letter-spacing: .06em; margin-bottom: 12px; }

/* Responsive */
@media (max-width: 640px) {
  .detail-grid { grid-template-columns: 1fr; }
  .filters-bar { flex-direction: column; align-items: stretch; }
  .filters-bar input { min-width: unset; }
}
</style>