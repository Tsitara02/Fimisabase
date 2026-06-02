<template>
  <div class="fade-up">
    <div class="page-header">
      <h1>Paramètres</h1>
      <p class="page-sub">Votre compte et préférences</p>
    </div>

    <div class="settings-grid">
      <div class="card">
        <h3>Profil</h3>
        <div class="profile-row">
          <div class="big-avatar">{{ initials }}</div>
          <div>
            <div class="profile-email">{{ auth.user?.email }}</div>
            <div class="profile-id">ID: {{ auth.user?.id?.slice(0, 16) }}…</div>
          </div>
        </div>
      </div>

      <div class="card danger-zone">
        <h3>Zone de danger</h3>
        <p class="zone-desc">La déconnexion efface votre session.</p>
        <button class="btn btn-danger" @click="auth.logout()">⏻ Se déconnecter</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const initials = computed(() => (auth.user?.email || '').slice(0, 2).toUpperCase())
</script>

<style scoped>
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 28px; }
.page-sub { color: var(--muted); margin-top: 4px; }
.settings-grid { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }
.card h3 { font-size: 15px; margin-bottom: 16px; color: var(--muted); font-family: 'DM Sans', sans-serif; font-weight: 500; text-transform: uppercase; letter-spacing: .06em; font-size: 11px; }
.profile-row { display: flex; align-items: center; gap: 16px; }
.big-avatar {
  width: 52px; height: 52px;
  background: linear-gradient(135deg, var(--accent), var(--accent2));
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; font-weight: 700; flex-shrink: 0;
}
.profile-email { font-weight: 500; font-size: 15px; }
.profile-id { font-size: 12px; color: var(--muted); margin-top: 3px; font-family: monospace; }
.danger-zone { border-color: color-mix(in srgb, var(--danger) 30%, transparent); }
.zone-desc { font-size: 13px; color: var(--muted); margin-bottom: 16px; }
</style>
