<<<<<<< HEAD
# Flask + Vue + Supabase Starter

Stack : **Flask** (API REST) · **Vue 3 + Vite** (frontend) · **Supabase** (auth + BDD)

---

## 🗂 Structure

```
project/
├── backend/
│   ├── app.py              # Flask API
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── api.js           # Axios + interceptors token
    │   ├── stores/auth.js   # Pinia : login / signup / logout
    │   ├── router/          # Vue Router + guards
    │   ├── views/           # Login, Signup, Dashboard, Items, Settings
    │   └── components/      # AppSidebar (collapsible)
    └── vite.config.js       # Proxy /api → Flask:5000
```

---

## ⚙️ Configuration Supabase

1. Créez un projet sur https://supabase.com
2. Récupérez vos clés dans **Project Settings → API**
3. Créez la table `items` dans l'éditeur SQL :

```sql
create table items (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid references auth.users,
  name        text not null,
  description text,
  created_at  timestamptz default now()
);

-- RLS : chaque user voit ses items
alter table items enable row level security;
create policy "own items" on items
  for all using (auth.uid() = user_id);
```

---

## 🚀 Démarrage

### Backend

```bash
cd backend
cp .env.example .env        # Remplissez SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY
pip install -r requirements.txt
python app.py               # http://localhost:5000
```

### Frontend

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

Le proxy Vite redirige `/api/*` → `http://localhost:5000/api/*`.

---

## 🔐 Auth flow

```
[Login form] → POST /api/auth/login → Supabase.signInWithPassword
                                    ← { access_token, user }
[Axios interceptor] → ajoute Bearer token à chaque requête
[require_auth decorator] → vérifie token via supabase.auth.get_user()
```

---

## 📡 Routes Flask

| Méthode | Route | Auth | Description |
|---------|-------|------|-------------|
| POST | /api/auth/signup | ✗ | Inscription |
| POST | /api/auth/login | ✗ | Connexion → JWT |
| POST | /api/auth/logout | ✓ | Déconnexion |
| GET  | /api/auth/me | ✓ | Profil utilisateur |
| GET  | /api/dashboard/stats | ✓ | Statistiques |
| GET  | /api/items | ✓ | Liste des items |
| POST | /api/items | ✓ | Créer un item |
| DELETE | /api/items/:id | ✓ | Supprimer un item |
=======
# Fimisabase
Nouvel application de FIMISA connecter a supabase
>>>>>>> 72ae6b0e78ab1f63913b183c686be58ea6a9f742
