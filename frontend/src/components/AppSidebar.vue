<template>
  <aside class="sidebar" :class="{ collapsed, 'mobile-open': mobileOpen }">
    <div class="sidebar-brand">
      <div class="brand-mark">F</div>
      <div class="brand-text" v-if="!collapsed || mobileOpen">
        <div class="brand-name">FIMISA</div>
        <div class="brand-sub">Andriry Milamy</div>
      </div>
      <!-- Bouton fermer sur mobile -->
      <button class="close-mobile" @click="emit('close')">✕</button>
    </div>

    <nav class="sidebar-nav">
      <div class="nav-group">
        <div class="nav-group-label" v-if="!collapsed || mobileOpen">Navigation</div>
        <RouterLink
          v-for="item in navItems" :key="item.to"
          :to="item.to" class="nav-item" active-class="active"
          @click="emit('close')"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label" v-if="!collapsed || mobileOpen">{{ item.label }}</span>
        </RouterLink>
      </div>
    </nav>

    <div class="sidebar-bottom">
      <button class="collapse-btn desktop-only" @click="collapsed = !collapsed">
        {{ collapsed ? '→' : '←' }}
      </button>
      <div class="user-row" v-if="!collapsed || mobileOpen">
        <div class="user-ava">{{ initials }}</div>
        <div class="user-info">
          <div class="user-name">{{ auth.user?.email?.split('@')[0] }}</div>
          <div class="user-role">Opérateur</div>
        </div>
        <button class="logout-btn" @click="auth.logout()" title="Déconnexion">⏻</button>
      </div>
      <div class="user-row-mini" v-else>
        <div class="user-ava">{{ initials }}</div>
        <button class="logout-btn" @click="auth.logout()">⏻</button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({ mobileOpen: { type: Boolean, default: false } })
const emit = defineEmits(['close'])

const auth = useAuthStore()
const collapsed = ref(false)
const initials = computed(() => (auth.user?.email || '??').slice(0, 2).toUpperCase())

const navItems = [
  { to: '/dashboard',     icon: '▦',  label: 'Dashboard' },
  { to: '/fournisseurs',  icon: '◉',  label: 'Fournisseurs AMI' },
  { to: '/bons-commande', icon: '📋', label: 'Bons de Commande' },
  { to: '/pv-reception', icon: '📦', label: 'PV Réception' },
  { to: '/stock',         icon: '⬡',  label: 'Stock & Articles' },
  { to: '/settings',      icon: '⚙',  label: 'Paramètres' },
]
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-w); min-width: var(--sidebar-w);
  background: var(--surface);
  border-right: 1px solid var(--border);
  display: flex; flex-direction: column;
  transition: width .22s ease, min-width .22s ease, left .25s ease;
  overflow: hidden;
}
.sidebar.collapsed { width: 60px; min-width: 60px; }

.sidebar-brand {
  display: flex; align-items: center; gap: 10px;
  padding: 20px 16px 16px;
  border-bottom: 1px solid var(--border);
}
.brand-mark {
  width: 34px; height: 34px; flex-shrink: 0;
  background: var(--teal); color: #080b12;
  border-radius: 8px; display: flex; align-items: center; justify-content: center;
  font-family: 'Bricolage Grotesque', sans-serif; font-size: 18px; font-weight: 800;
}
.brand-text { flex: 1; }
.brand-name { font-family: 'Bricolage Grotesque', sans-serif; font-size: 15px; font-weight: 800; color: var(--text); line-height: 1.2; }
.brand-sub  { font-size: 11px; color: var(--muted); letter-spacing: .03em; }

/* Bouton ✕ visible seulement sur mobile */
.close-mobile {
  display: none;
  background: none; border: none; color: var(--muted);
  font-size: 16px; padding: 4px; margin-left: auto; flex-shrink: 0;
}
@media (max-width: 640px) {
  .close-mobile { display: flex; }
  .desktop-only { display: none !important; }
}

.sidebar-nav { flex: 1; padding: 12px 8px; overflow-y: auto; }
.nav-group { display: flex; flex-direction: column; gap: 2px; }
.nav-group-label {
  font-size: 10px; font-weight: 700; color: var(--muted);
  letter-spacing: .1em; text-transform: uppercase; padding: 10px 10px 6px;
}
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 8px;
  color: var(--muted2); font-size: 13px; font-weight: 500;
  transition: all .15s; white-space: nowrap;
}
.nav-item:hover { background: var(--surface2); color: var(--text); }
.nav-item.active { background: color-mix(in srgb,var(--teal) 12%,transparent); color: var(--teal); }
.nav-icon { font-size: 16px; flex-shrink: 0; width: 20px; text-align: center; }
.nav-label { flex: 1; }

.sidebar-bottom {
  border-top: 1px solid var(--border);
  padding: 10px 8px 12px;
  display: flex; flex-direction: column; gap: 8px;
}
.collapse-btn {
  background: var(--surface2); border: 1px solid var(--border); color: var(--muted);
  border-radius: 6px; padding: 5px 8px; font-size: 12px;
  align-self: flex-end; transition: all .15s;
}
.collapse-btn:hover { color: var(--teal); border-color: var(--teal); }

.user-row { display: flex; align-items: center; gap: 8px; padding: 4px; }
.user-row-mini { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.user-ava {
  width: 30px; height: 30px; flex-shrink: 0;
  background: linear-gradient(135deg,var(--blue),var(--purple));
  border-radius: 7px; display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
}
.user-info { flex: 1; min-width: 0; }
.user-name { font-size: 12px; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.user-role { font-size: 10px; color: var(--muted); }
.logout-btn { background: none; border: none; color: var(--muted); font-size: 14px; padding: 3px; transition: color .15s; }
.logout-btn:hover { color: var(--red); }
</style>
