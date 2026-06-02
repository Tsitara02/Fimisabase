<template>
  <div class="fade-up">
    <div class="page-header">
      <div>
        <h1>Dashboard FIMISA</h1>
        <div class="sub">Projet Andriry Milamy · PNUD</div>
      </div>
      <div class="header-right">
        <span class="date-pill">{{ today }}</span>
      </div>
    </div>

    <!-- KPI grid -->
    <div class="kpi-grid stagger" v-if="!loading">
      <div class="kpi-card" v-for="kpi in kpis" :key="kpi.label">
        <div class="kpi-top">
          <div class="kpi-icon" :style="{background: kpi.bg, color: kpi.color}">{{ kpi.icon }}</div>
          <div class="kpi-trend" v-if="kpi.sub">{{ kpi.sub }}</div>
        </div>
        <div class="kpi-value">{{ kpi.value }}</div>
        <div class="kpi-label">{{ kpi.label }}</div>
        <div class="kpi-bar" v-if="kpi.pct !== undefined">
          <div class="kpi-fill" :style="{width: kpi.pct+'%', background: kpi.color}"></div>
        </div>
      </div>
    </div>
    <div class="kpi-grid" v-else>
      <div class="kpi-card skeleton" v-for="i in 5" :key="i"></div>
    </div>

    <!-- Two columns -->
    <div class="dash-cols">
      <!-- Alertes stock -->
      <div class="card">
        <div class="card-header">
          <h3>⚠ Alertes Stock Critique</h3>
          <RouterLink to="/stock" class="btn btn-ghost btn-sm">Voir stock →</RouterLink>
        </div>
        <div v-if="loadingAlerts" class="empty-state"><p>Chargement…</p></div>
        <div v-else-if="alertes.length === 0" class="empty-state">
          <div class="icon">✓</div><p>Aucune alerte critique</p>
        </div>
        <table class="data-table" v-else>
          <thead><tr><th>Article</th><th>Stock</th><th>Seuil</th><th>Statut</th></tr></thead>
          <tbody>
            <tr v-for="a in alertes" :key="a.code_article">
              <td>
                <div class="art-name">{{ a.designation }}</div>
                <div class="art-code">{{ a.code_article }}</div>
              </td>
              <td><strong :style="{color: a.quantite_en_stock === 0 ? 'var(--red)' : 'var(--amber)'}">{{ a.quantite_en_stock }}</strong> {{ a.unite_mesure }}</td>
              <td class="muted">{{ a.seuil_alerte }}</td>
              <td>
                <span class="badge" :class="a.quantite_en_stock === 0 ? 'badge-red' : 'badge-amber'">
                  {{ a.statut_urgence || (a.quantite_en_stock === 0 ? 'RUPTURE' : 'CRITIQUE') }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Distributions récentes -->
      <div class="card">
        <div class="card-header">
          <h3>↓ Distributions Récentes</h3>
        </div>
        <div v-if="loadingDist" class="empty-state"><p>Chargement…</p></div>
        <div v-else-if="distributions.length === 0" class="empty-state">
          <div class="icon">◫</div><p>Aucune distribution récente</p>
        </div>
        <div class="dist-list" v-else>
          <div class="dist-row" v-for="d in distributions" :key="d.date_distribution+d.beneficiaire_nom">
            <div class="dist-avatar">{{ (d.beneficiaire_nom||'?').charAt(0) }}</div>
            <div class="dist-info">
              <div class="dist-name">{{ d.beneficiaire_nom || '—' }}</div>
              <div class="dist-meta">{{ d.code_activite }} · {{ d.commune || d.fokontany || '—' }}</div>
            </div>
            <div class="dist-right">
              <div class="dist-date">{{ formatDate(d.date_distribution) }}</div>
              <span class="badge badge-blue">{{ d.genre === 'F' ? '♀' : '♂' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import api from '@/api'

const loading = ref(true)
const loadingAlerts = ref(true)
const loadingDist = ref(true)
const stats = ref(null)
const alertes = ref([])
const distributions = ref([])

const today = computed(() => new Date().toLocaleDateString('fr-FR', {weekday:'long',day:'numeric',month:'long',year:'numeric'}))

function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('fr-FR', {day:'2-digit',month:'short'})
}

const kpis = computed(() => {
  if (!stats.value) return []
  const s = stats.value
  return [
    { label: 'Bénéficiaires', value: s.beneficiaires.total, icon: '◎', color: 'var(--teal)',   bg: 'color-mix(in srgb,var(--teal) 12%,transparent)',   sub: `${s.beneficiaires.femmes}F / ${s.beneficiaires.hommes}H`, pct: s.beneficiaires.total ? (s.beneficiaires.femmes/s.beneficiaires.total*100) : 0 },
    { label: 'Fournisseurs AMI', value: s.fournisseurs.total, icon: '◉', color: 'var(--blue)', bg: 'color-mix(in srgb,var(--blue) 12%,transparent)',   sub: `${s.fournisseurs.agrees} agréés`, pct: s.fournisseurs.total ? (s.fournisseurs.agrees/s.fournisseurs.total*100) : 0 },
    { label: 'Bons de Commande', value: s.commandes.total, icon: '▦',   color: 'var(--purple)',bg: 'color-mix(in srgb,var(--purple) 12%,transparent)', sub: `${s.commandes.validees} validés`, pct: s.commandes.total ? (s.commandes.validees/s.commandes.total*100) : 0 },
    { label: 'Distributions',   value: s.distributions.total, icon: '↓', color: 'var(--green)', bg: 'color-mix(in srgb,var(--green) 12%,transparent)', sub: 'fiches terrain' },
    { label: 'Alertes Stock',   value: s.stock.alertes_critiques, icon: '⚠', color: s.stock.alertes_critiques > 0 ? 'var(--red)' : 'var(--green)', bg: s.stock.alertes_critiques > 0 ? 'color-mix(in srgb,var(--red) 12%,transparent)' : 'color-mix(in srgb,var(--green) 12%,transparent)', sub: `${s.stock.total_articles} articles total` },
  ]
})

onMounted(async () => {
  try {
    const { data } = await api.get('/dashboard/stats')
    stats.value = data
  } finally { loading.value = false }

  try {
    const { data } = await api.get('/dashboard/alertes-stock')
    alertes.value = data
  } finally { loadingAlerts.value = false }

  try {
    const { data } = await api.get('/dashboard/distributions-recentes')
    distributions.value = data
  } finally { loadingDist.value = false }
})
</script>

<style scoped>
.header-right { display: flex; align-items: center; }
.date-pill { background: var(--surface2); border: 1px solid var(--border); border-radius: 20px; padding: 6px 14px; font-size: 12px; color: var(--muted2); text-transform: capitalize; }

.kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(175px,1fr)); gap: 14px; margin-bottom: 24px; }
.kpi-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 18px 20px; transition: border-color .2s, transform .2s; }
.kpi-card:hover { border-color: var(--border2); transform: translateY(-2px); }
.kpi-card.skeleton { min-height: 110px; background: linear-gradient(90deg,var(--surface) 25%,var(--surface2) 50%,var(--surface) 75%); background-size: 200% 100%; animation: shimmer 1.4s infinite; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

.kpi-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.kpi-icon { width: 36px; height: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; font-size: 17px; }
.kpi-trend { font-size: 11px; color: var(--muted2); text-align: right; }
.kpi-value { font-family: 'Bricolage Grotesque',sans-serif; font-size: 32px; font-weight: 800; line-height: 1; }
.kpi-label { font-size: 12px; color: var(--muted2); margin: 5px 0 10px; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; }
.kpi-bar { height: 3px; background: var(--border); border-radius: 2px; overflow: hidden; }
.kpi-fill { height: 100%; border-radius: 2px; transition: width .8s ease; }

.dash-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 900px) { .dash-cols { grid-template-columns: 1fr; } }

.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-header h3 { font-size: 14px; font-family: 'Instrument Sans',sans-serif; font-weight: 600; }

.art-name { font-weight: 500; }
.art-code { font-size: 11px; color: var(--muted); font-family: monospace; }
.muted { color: var(--muted2); }

.dist-list { display: flex; flex-direction: column; gap: 1px; }
.dist-row { display: flex; align-items: center; gap: 10px; padding: 10px 6px; border-bottom: 1px solid var(--border); }
.dist-row:last-child { border-bottom: none; }
.dist-avatar { width: 32px; height: 32px; border-radius: 8px; background: var(--surface3); color: var(--teal); display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 700; flex-shrink: 0; }
.dist-info { flex: 1; min-width: 0; }
.dist-name { font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dist-meta { font-size: 11px; color: var(--muted); }
.dist-right { text-align: right; flex-shrink: 0; display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.dist-date { font-size: 11px; color: var(--muted); }
</style>
