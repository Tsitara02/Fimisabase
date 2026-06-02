<template>
  <div class="auth-page">
    <div class="auth-card fade-up">
      <div class="auth-header">
        <span class="auth-logo">◈</span>
        <h1>Créer un compte</h1>
        <p class="auth-sub">Rejoignez-nous. C'est gratuit.</p>
      </div>

      <form @submit.prevent="handleSignup">
        <div class="field">
          <label>Email</label>
          <input v-model="email" type="email" placeholder="vous@exemple.com" required autofocus />
        </div>
        <div class="field">
          <label>Mot de passe</label>
          <input v-model="password" type="password" placeholder="Min. 8 caractères" minlength="8" required />
        </div>

        <div v-if="auth.error" class="alert danger">{{ auth.error }}</div>

        <button type="submit" class="btn btn-primary submit-btn" :disabled="auth.loading">
          <span v-if="auth.loading">Création…</span>
          <span v-else>Créer mon compte →</span>
        </button>
      </form>

      <p class="auth-switch">
        Déjà un compte ? <RouterLink to="/login">Se connecter</RouterLink>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const email = ref('')
const password = ref('')

function handleSignup() {
  auth.signup(email.value, password.value)
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: radial-gradient(ellipse at 70% 20%, color-mix(in srgb, var(--accent2) 8%, transparent), transparent 60%),
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
.auth-logo { font-size: 32px; color: var(--accent2); display: block; margin-bottom: 12px; }
h1 { font-size: 26px; margin-bottom: 6px; }
.auth-sub { color: var(--muted); font-size: 14px; }
.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 6px; color: var(--muted); }
.submit-btn { width: 100%; justify-content: center; padding: 12px; margin-top: 8px; font-size: 15px; background: var(--accent2); }
.submit-btn:hover { background: #7c3aed; }
.auth-switch { text-align: center; margin-top: 20px; font-size: 14px; color: var(--muted); }
.auth-switch a { color: var(--accent2); font-weight: 500; }
.alert { padding: 10px 14px; border-radius: 8px; font-size: 13px; margin-bottom: 16px; }
.alert.danger { background: color-mix(in srgb, var(--danger) 12%, transparent); color: #f87171; border: 1px solid color-mix(in srgb, var(--danger) 25%, transparent); }
button:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
