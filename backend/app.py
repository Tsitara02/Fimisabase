from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CCORS(
    app,
    origins=[
        "http://localhost:5173",          # Pour tes tests en local
        "https://fimisabase.vercel.app"   # Ton vrai frontend de production Vercel
    ],
    supports_credentials=True
)

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
        benef = supabase.table("beneficiaire").select("id_beneficiaire, genre").execute()
        total_benef = len(benef.data)
        femmes = sum(1 for b in benef.data if b.get("genre", "").strip().upper() == "F")
        hommes = total_benef - femmes

        fourn = supabase.table("fournisseur_ami").select("id_fournisseur, statut_agree").execute()
        total_fourn = len(fourn.data)
        agrees = sum(1 for f in fourn.data if f.get("statut_agree") is True)

        bc = supabase.table("bon_commande").select("statut_validation, montant_total").execute()
        total_bc = len(bc.data)
        bc_valides = sum(1 for b in bc.data if b.get("statut_validation", "").lower() == "validé")
        budget_total = sum(float(b.get("montant_total") or 0) for b in bc.data)

        dist = supabase.table("fiche_distribution").select("id_fiche_distribution").execute()
        total_dist = len(dist.data)

        alertes = supabase.table("vue_alertes_stock_critique").select("*").execute()
        nb_alertes = len(alertes.data)

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
        res = supabase.table("fournisseur_ami").select("*").order("raison_sociale").execute()
        data = res.data
        search = request.args.get("q", "")
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
    missing_f = [k for k in ["raison_sociale", "lots_soumissionnes"] if not data.get(k)]
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
    missing_a = [k for k in ["designation", "unite_mesure"] if not data.get(k)]
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
    data = request.json
    delta = int(data.get("delta", 0))
    try:
        art = supabase.table("article").select("quantite_en_stock").eq("id_article", id_a).single().execute()
        nouvelle_qte = max(0, (art.data.get("quantite_en_stock") or 0) + delta)
        res = supabase.table("article").update({"quantite_en_stock": nouvelle_qte}).eq("id_article", id_a).execute()
        return jsonify(res.data[0])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Bons de Commande ─────────────────────────────────────────────────────────

@app.route("/api/bons-commande", methods=["GET"])
@require_auth
def get_bons_commande():
    try:
        res = supabase.table("bon_commande") \
            .select("*, fournisseur_ami(raison_sociale), activite_cadre_logique(code_activite,description)") \
            .order("date_commande", desc=True).execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bons-commande/<id_bc>", methods=["GET"])
@require_auth
def get_bon_commande(id_bc):
    try:
        bc = supabase.table("bon_commande") \
            .select("*, fournisseur_ami(raison_sociale), activite_cadre_logique(code_activite,description)") \
            .eq("id_bon_commande", id_bc).single().execute()
        lignes = supabase.table("ligne_commande") \
            .select("*").eq("id_bon_commande", id_bc).execute()
        return jsonify({**bc.data, "lignes": lignes.data})
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route("/api/bons-commande", methods=["POST"])
@require_auth
def create_bon_commande():
    data = request.json
    lignes = data.pop("lignes", [])
    if not data.get("numero_bc"):
        return jsonify({"error": "numero_bc requis"}), 400
    try:
        montant_total = sum(
            float(l.get("prix_unitaire", 0)) * int(l.get("quantite_commandee", 0))
            for l in lignes
        )
        data["montant_total"] = montant_total
        data.setdefault("statut_validation", "en_attente")
        bc = supabase.table("bon_commande").insert(data).execute()
        id_bc = bc.data[0]["id_bon_commande"]
        if lignes:
            for l in lignes:
                l["id_bon_commande"] = id_bc
                l["prix_total"] = float(l.get("prix_unitaire", 0)) * int(l.get("quantite_commandee", 0))
            supabase.table("ligne_commande").insert(lignes).execute()
        return jsonify({**bc.data[0], "lignes": lignes}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bons-commande/<id_bc>", methods=["PUT"])
@require_auth
def update_bon_commande(id_bc):
    data = request.json
    lignes = data.pop("lignes", None)
    data.pop("id_bon_commande", None)
    # Supprimer les clés de jointure retournées par Supabase
    data.pop("fournisseur_ami", None)
    data.pop("activite_cadre_logique", None)
    try:
        if lignes is not None:
            montant_total = sum(
                float(l.get("prix_unitaire", 0)) * int(l.get("quantite_commandee", 0))
                for l in lignes
            )
            data["montant_total"] = montant_total
        bc = supabase.table("bon_commande").update(data).eq("id_bon_commande", id_bc).execute()
        if lignes is not None:
            supabase.table("ligne_commande").delete().eq("id_bon_commande", id_bc).execute()
            for l in lignes:
                l["id_bon_commande"] = id_bc
                l.pop("id_ligne_bc", None)
                l["prix_total"] = float(l.get("prix_unitaire", 0)) * int(l.get("quantite_commandee", 0))
            if lignes:
                supabase.table("ligne_commande").insert(lignes).execute()
        return jsonify(bc.data[0])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bons-commande/<id_bc>/valider", methods=["POST"])
@require_auth
def valider_bon_commande(id_bc):
    data = request.json
    statut = data.get("statut")
    if statut not in ["validé", "refusé"]:
        return jsonify({"error": "statut invalide — utiliser 'validé' ou 'refusé'"}), 400
    try:
        update = {"statut_validation": statut}
        res = supabase.table("bon_commande").update(update).eq("id_bon_commande", id_bc).execute()
        return jsonify(res.data[0])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bons-commande/<id_bc>", methods=["DELETE"])
@require_auth
def delete_bon_commande(id_bc):
    try:
        supabase.table("ligne_commande").delete().eq("id_bon_commande", id_bc).execute()
        supabase.table("bon_commande").delete().eq("id_bon_commande", id_bc).execute()
        return jsonify({"message": "BC supprimé"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Selects (listes déroulantes) ─────────────────────────────────────────────

@app.route("/api/select/fournisseurs", methods=["GET"])
@require_auth
def select_fournisseurs():
    try:
        res = supabase.table("fournisseur_ami") \
            .select("id_fournisseur,raison_sociale,statut_agree") \
            .order("raison_sociale").execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/select/activites", methods=["GET"])
@require_auth
def select_activites():
    try:
        res = supabase.table("activite_cadre_logique") \
            .select("id_activite,code_activite,description") \
            .order("code_activite").execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/select/personnel", methods=["GET"])
@require_auth
def select_personnel():
    try:
        res = supabase.table("personnel_fimisa") \
            .select("id_personnel,nom,prenom,poste_occupe") \
            .order("nom").execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── PV Réception ─────────────────────────────────────────────────────────────

@app.route("/api/pv-reception", methods=["GET"])
@require_auth
def get_pvs():
    try:
        res = supabase.table("pv_reception") \
            .select("*, bon_commande(numero_bc, fournisseur_ami(raison_sociale)), personnel_fimisa(nom, prenom)") \
            .order("date_reception", desc=True).execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/pv-reception/<id_pv>", methods=["GET"])
@require_auth
def get_pv(id_pv):
    try:
        pv = supabase.table("pv_reception") \
            .select("*, bon_commande(numero_bc, id_fournisseur, fournisseur_ami(raison_sociale)), personnel_fimisa(nom, prenom)") \
            .eq("id_pv_reception", id_pv).single().execute()
        lignes = supabase.table("ligne_reception") \
            .select("*, article(designation, unite_mesure)") \
            .eq("id_pv_reception", id_pv).execute()
        return jsonify({**pv.data, "lignes": lignes.data})
    except Exception as e:
        return jsonify({"error": str(e)}), 404

@app.route("/api/pv-reception", methods=["POST"])
@require_auth
def create_pv():
    data = request.json
    lignes = data.pop("lignes", [])
    if not data.get("numero_pv"):
        return jsonify({"error": "numero_pv requis"}), 400
    try:
        pv = supabase.table("pv_reception").insert(data).execute()
        id_pv = pv.data[0]["id_pv_reception"]
        if lignes:
            for l in lignes:
                l["id_pv_reception"] = id_pv
                l.pop("id_ligne_pvr", None)
            supabase.table("ligne_reception").insert(lignes).execute()
        return jsonify({**pv.data[0], "lignes": lignes}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/pv-reception/<id_pv>", methods=["PUT"])
@require_auth
def update_pv(id_pv):
    data = request.json
    lignes = data.pop("lignes", None)
    data.pop("id_pv_reception", None)
    data.pop("bon_commande", None)
    data.pop("personnel_fimisa", None)
    try:
        pv = supabase.table("pv_reception").update(data).eq("id_pv_reception", id_pv).execute()
        if lignes is not None:
            supabase.table("ligne_reception").delete().eq("id_pv_reception", id_pv).execute()
            for l in lignes:
                l["id_pv_reception"] = id_pv
                l.pop("id_ligne_pvr", None)
                l.pop("article", None)
            if lignes:
                supabase.table("ligne_reception").insert(lignes).execute()
        return jsonify(pv.data[0])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/pv-reception/<id_pv>/valider", methods=["POST"])
@require_auth
def valider_pv(id_pv):
    """Valide le PV et met à jour le stock pour chaque ligne reçue."""
    try:
        # Récupérer les lignes de réception
        lignes = supabase.table("ligne_reception") \
            .select("id_article, quantite_livree_site") \
            .eq("id_pv_reception", id_pv).execute()

        # Mettre à jour le stock pour chaque article
        for l in lignes.data:
            if not l.get("id_article"):
                continue
            art = supabase.table("article") \
                .select("quantite_en_stock") \
                .eq("id_article", l["id_article"]).single().execute()
            stock_actuel = art.data.get("quantite_en_stock") or 0
            nouveau_stock = stock_actuel + int(l.get("quantite_livree_site") or 0)
            supabase.table("article") \
                .update({"quantite_en_stock": nouveau_stock}) \
                .eq("id_article", l["id_article"]).execute()

        return jsonify({"message": f"PV validé. {len(lignes.data)} article(s) mis à jour."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/pv-reception/<id_pv>", methods=["DELETE"])
@require_auth
def delete_pv(id_pv):
    try:
        supabase.table("ligne_reception").delete().eq("id_pv_reception", id_pv).execute()
        supabase.table("pv_reception").delete().eq("id_pv_reception", id_pv).execute()
        return jsonify({"message": "PV supprimé"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/select/bons-commande-valides", methods=["GET"])
@require_auth
def select_bc_valides():
    """Retourne uniquement les BC validés pour le select du PV."""
    try:
        res = supabase.table("bon_commande") \
            .select("id_bon_commande, numero_bc, fournisseur_ami(raison_sociale), ligne_commande(designation_article, quantite_commandee, id_bon_commande)") \
            .eq("statut_validation", "validé") \
            .order("date_commande", desc=True).execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/select/articles", methods=["GET"])
@require_auth
def select_articles():
    try:
        res = supabase.table("article") \
            .select("id_article, code_article, designation, unite_mesure, quantite_en_stock") \
            .order("designation").execute()
        return jsonify(res.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)