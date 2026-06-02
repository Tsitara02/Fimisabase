<template>
  <div class="auth-page">
    <div class="auth-card fade-up">
      <div class="auth-header">
        <span class="auth-logo">◈</span>
        <h1>Connexion</h1>
        <p class="auth-sub">Bienvenue. Entrez vos identifiants.</p>
      </div>

      <div v-if="registered" class="alert success">
        ✓ Compte créé ! Vérifiez votre email puis connectez-vous.
      </div>

      <form @submit.prevent="handleLogin">
        <div class="field">
          <label>Email</label>
          <input v-model="email" type="email" placeholder="vous@exemple.com" required autofocus />
        </div>
        <div class="field">
          <label>Mot de passe</label>
          <input v-model="password" type="password" placeholder="••••••••" required />
        </div>

        <div v-if="auth.error" class="alert danger">{{ auth.error }}</div>

        <button type="submit" class="btn btn-primary submit-btn" :disabled="auth.loading">
          <span v-if="auth.loading">Connexion…</span>
          <span v-else>Se connecter →</span>
        </button>
      </form>

      <p class="auth-switch">
        Pas de compte ? <RouterLink to="/signup">Créer un compte</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const email = ref('')
const password = ref('')
const registered = computed(() => route.query.registered === '1')

function handleLogin() {
  auth.login(email.value, password.value)
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: radial-gradient(ellipse at 30% 20%, color-mix(in srgb, var(--accent) 8%, transparent), transparent 60%),
              radial-gradient(ellipse at 70% 80%, color-mix(in srgb, var(--accent2) 6%, transparent), transparent 60%),
              var(--bg);
}
.auth-card {
  width: 100%;
  max-width: 400px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 40px 36px;
}
.auth-header { text-align: center; margin-bottom: 28px; }
.auth-logo { font-size: 32px; color: var(--accent); display: block; margin-bottom: 12px; }
h1 { font-size: 26px; margin-bottom: 6px; }
.auth-sub { color: var(--muted); font-size: 14px; }
.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 6px; color: var(--muted); }
.submit-btn { width: 100%; justify-content: center; padding: 12px; margin-top: 8px; font-size: 15px; }
.auth-switch { text-align: center; margin-top: 20px; font-size: 14px; color: var(--muted); }
.auth-switch a { color: var(--accent); font-weight: 500; }
.alert { padding: 10px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 16px; }
.alert.success { background: color-mix(in srgb, var(--success) 15%, transparent); color: var(--success); border: 1px solid color-mix(in srgb, var(--success) 30%, transparent); }
.alert.danger { background: color-mix(in srgb, var(--danger) 12%, transparent); color: #f87171; border: 1px solid color-mix(in srgb, var(--danger) 25%, transparent); }
button:disabled { opacity: 0.6; cursor: not-allowed; transform: none !important; }
</style>
