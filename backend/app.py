from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"], supports_credentials=True)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

missing = [k for k, v in {"SUPABASE_URL": SUPABASE_URL, "SUPABASE_ANON_KEY": SUPABASE_ANON_KEY}.items() if not v]
if missing:
    raise SystemExit(f"\n❌ Variables manquantes dans .env : {', '.join(missing)}\n")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


# ─── Auth middleware ───────────────────────────────────────────────────────────

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Token manquant"}), 401
        token = auth_header.split(" ")[1]
        try:
            user = supabase.auth.get_user(token)
            request.user = user.user
        except Exception:
            return jsonify({"error": "Token invalide"}), 401
        return f(*args, **kwargs)
    return decorated


# ─── Auth ─────────────────────────────────────────────────────────────────────

@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.json
    try:
        res = supabase.auth.sign_up({"email": data["email"], "password": data["password"]})
        return jsonify({"message": "Compte créé.", "user": res.user.email if res.user else None})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.json
    try:
        res = supabase.auth.sign_in_with_password({"email": data["email"], "password": data["password"]})
        return jsonify({
            "access_token": res.session.access_token,
            "refresh_token": res.session.refresh_token,
            "user": {"id": res.user.id, "email": res.user.email}
        })
    except Exception as e:
        return jsonify({"error": "Email ou mot de passe incorrect"}), 401

@app.route("/api/auth/logout", methods=["POST"])
@require_auth
def logout():
    supabase.auth.sign_out()
    return jsonify({"message": "Déconnexion réussie"})

@app.route("/api/auth/me", methods=["GET"])
@require_auth
def me():
    u = request.user
    return jsonify({"id": u.id, "email": u.email})


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route("/api/dashboard/stats", methods=["GET"])
@require_auth
def dashboard_stats():
    try:
        # Bénéficiaires total + genre
        benef = supabase.table("beneficiaire").select("id_beneficiaire, genre").execute()
        total_benef = len(benef.data)
        femmes = sum(1 for b in benef.data if b.get("genre", "").strip().upper() == "F")
        hommes = total_benef - femmes

        # Fournisseurs AMI agréés
        fourn = supabase.table("fournisseur_ami").select("id_fournisseur, statut_agree").execute()
        total_fourn = len(fourn.data)
        agrees = sum(1 for f in fourn.data if f.get("statut_agree") is True)

        # Bons de commande
        bc = supabase.table("bon_commande").select("statut_validation, montant_total").execute()
        total_bc = len(bc.data)
        bc_valides = sum(1 for b in bc.data if b.get("statut_validation", "").lower() == "validé")
        budget_total = sum(float(b.get("montant_total") or 0) for b in bc.data)

        # Distributions
        dist = supabase.table("fiche_distribution").select("id_fiche_distribution").execute()
        total_dist = len(dist.data)

        # Articles en alerte de stock
        alertes = supabase.table("vue_alertes_stock_critique").select("*").execute()
        nb_alertes = len(alertes.data)

        # Stock articles
        articles = supabase.table("article").select("quantite_en_stock, seuil_alerte").execute()
        total_articles = len(articles.data)

        return jsonify({
            "beneficiaires": {"total": total_benef, "femmes": femmes, "hommes": hommes},
            "fournisseurs": {"total": total_fourn, "agrees": agrees},
            "commandes": {"total": total_bc, "validees": bc_valides, "budget_total": round(budget_total, 2)},
            "distributions": {"total": total_dist},
            "stock": {"total_articles": total_articles, "alertes_critiques": nb_alertes},
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/dashboard/distributions-recentes", methods=["GET"])
@require_auth
def distributions_recentes():
    try:
        res = supabase.table("vue_suivi_distributions_terrain") \
            .select("*").order("date_distribution", desc=True).limit(10).execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/dashboard/alertes-stock", methods=["GET"])
@require_auth
def alertes_stock_dashboard():
    try:
        res = supabase.table("vue_alertes_stock_critique").select("*").execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Fournisseurs AMI ─────────────────────────────────────────────────────────

@app.route("/api/fournisseurs", methods=["GET"])
@require_auth
def get_fournisseurs():
    try:
        search = request.args.get("q", "")
        query = supabase.table("fournisseur_ami").select("*").order("raison_sociale")
        res = query.execute()
        data = res.data
        if search:
            s = search.lower()
            data = [f for f in data if s in f.get("raison_sociale", "").lower()
                    or s in (f.get("responsable_nom") or "").lower()
                    or s in (f.get("email") or "").lower()]
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/fournisseurs/<id_f>", methods=["GET"])
@require_auth
def get_fournisseur(id_f):
    try:
        res = supabase.table("fournisseur_ami").select("*").eq("id_fournisseur", id_f).single().execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route("/api/fournisseurs", methods=["POST"])
@require_auth
def create_fournisseur():
    data = request.json
    required = ["raison_sociale", "lots_soumissionnes"]
    missing_f = [k for k in required if not data.get(k)]
    if missing_f:
        return jsonify({"error": f"Champs requis : {', '.join(missing_f)}"}), 400
    try:
        res = supabase.table("fournisseur_ami").insert(data).execute()
        return jsonify(res.data[0]), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/fournisseurs/<id_f>", methods=["PUT"])
@require_auth
def update_fournisseur(id_f):
    data = request.json
    data.pop("id_fournisseur", None)
    try:
        res = supabase.table("fournisseur_ami").update(data).eq("id_fournisseur", id_f).execute()
        return jsonify(res.data[0])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/fournisseurs/<id_f>", methods=["DELETE"])
@require_auth
def delete_fournisseur(id_f):
    try:
        supabase.table("fournisseur_ami").delete().eq("id_fournisseur", id_f).execute()
        return jsonify({"message": "Fournisseur supprimé"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Stock / Articles ─────────────────────────────────────────────────────────

@app.route("/api/articles", methods=["GET"])
@require_auth
def get_articles():
    try:
        res = supabase.table("article").select("*").order("designation").execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/articles/<id_a>", methods=["GET"])
@require_auth
def get_article(id_a):
    try:
        res = supabase.table("article").select("*").eq("id_article", id_a).single().execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route("/api/articles", methods=["POST"])
@require_auth
def create_article():
    data = request.json
    required = ["designation", "unite_mesure"]
    missing_a = [k for k in required if not data.get(k)]
    if missing_a:
        return jsonify({"error": f"Champs requis : {', '.join(missing_a)}"}), 400
    try:
        res = supabase.table("article").insert(data).execute()
        return jsonify(res.data[0]), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/articles/<id_a>", methods=["PUT"])
@require_auth
def update_article(id_a):
    data = request.json
    data.pop("id_article", None)
    try:
        res = supabase.table("article").update(data).eq("id_article", id_a).execute()
        return jsonify(res.data[0])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/articles/<id_a>", methods=["DELETE"])
@require_auth
def delete_article(id_a):
    try:
        supabase.table("article").delete().eq("id_article", id_a).execute()
        return jsonify({"message": "Article supprimé"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/articles/<id_a>/ajuster-stock", methods=["POST"])
@require_auth
def ajuster_stock(id_a):
    """Ajuste le stock : delta positif = entrée, négatif = sortie."""
    data = request.json
    delta = int(data.get("delta", 0))
    try:
        art = supabase.table("article").select("quantite_en_stock").eq("id_article", id_a).single().execute()
        nouvelle_qte = max(0, (art.data.get("quantite_en_stock") or 0) + delta)
        res = supabase.table("article").update({"quantite_en_stock": nouvelle_qte}).eq("id_article", id_a).execute()
        return jsonify(res.data[0])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
