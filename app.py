# =========================
print("APP DEMARRE")
# APP.PY COMPLET (SAAS SIMPLE)
# =========================
from werkzeug.security import generate_password_hash, check_password_hash

from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "cle-secrete-super-forte-123"

# -------------------------
# DATABASE
# -------------------------

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # USERS
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        abonnement INTEGER DEFAULT 0,
        date_fin_abonnement TEXT
    )
    ''')

    # PRODUITS PRO
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT,
        quantite INTEGER,
        prix_achat REAL,
        prix_vente REAL,
        user_id INTEGER
    )
    ''')

    # FACTURES
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS factures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id INTEGER,
        quantite INTEGER,
        total REAL,
        statut TEXT,
        user_id INTEGER,
        created_at TEXT
    )
    ''')

    try:
        cursor.execute("ALTER TABLE factures ADD COLUMN created_at TEXT")
    except:
        pass

    conn.commit()
    conn.close()

# -------------------------

# AUTH
@app.route("/")
def home():
    return redirect("/login")
# -------------------------
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/analyse_ia")
def analyse_ia():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    # récupérer données
    ventes = cursor.execute("""
        SELECT SUM(total) as total FROM factures
        WHERE user_id=? AND statut='payé'
    """, (user_id,)).fetchone()["total"] or 0

    depenses = cursor.execute("""
        SELECT SUM(p.prix_achat * f.quantite) as total
        FROM factures f
        JOIN produits p ON f.produit_id = p.id
        WHERE f.user_id=? AND f.statut='payé'
    """, (user_id,)).fetchone()["total"] or 0

    nb_produits = cursor.execute(
        "SELECT COUNT(*) as total FROM produits WHERE user_id=?",
        (user_id,)
    ).fetchone()["total"]

    conn.close()

    prompt = f"""
    Analyse ce business:

    Ventes: {ventes} FCFA
    Dépenses: {depenses} FCFA
    Produits: {nb_produits}

    Donne:
    - état du business
    - conseils
    - stratégies pour augmenter les profits
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        analyse = response.choices[0].message.content

    except Exception as e:
        analyse = f"Erreur IA: {e}"

    return render_template("ia.html", analyse=analyse)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            error = "Remplis tous les champs"
        else:
            conn = get_db()
            cursor = conn.cursor()

            from werkzeug.security import generate_password_hash
            hashed_password = generate_password_hash(password)

            try:
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, hashed_password)
                )
                conn.commit()
                conn.close()

                return redirect("/login")

            except Exception as e:
                print("ERREUR REGISTER:", e)  # 🔥 IMPORTANT
                error = "Utilisateur déjà existant ou erreur serveur"

    return render_template("register.html", error=error)
print("ROUTE LOGIN CHARGEE")
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        cursor = conn.cursor()

        user = cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()

        conn.close()

        if user is None:
            return render_template("login.html", error="Utilisateur introuvable")

        from werkzeug.security import check_password_hash

        if not check_password_hash(user["password"], password):
            return render_template("login.html", error="Mot de passe incorrect")

        session["user_id"] = user["id"]
        from flask import url_for
        return redirect(url_for("dashboard"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -------------------------
def jours_restants(user_id):
    conn = get_db()
    cursor = conn.cursor()

    user = cursor.execute(
        "SELECT date_fin_abonnement FROM users WHERE id=?",
        (user_id,)
    ).fetchone()

    conn.close()

    if user and user["date_fin_abonnement"]:
        date_fin = datetime.strptime(user["date_fin_abonnement"], "%Y-%m-%d")
        jours = (date_fin - datetime.now()).days
        return jours

    return None
# DASHBOARD
# -------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    if not verifier_abonnement(session["user_id"]):
        return redirect("/abonnement")

    import json

    conn = get_db()
    cursor = conn.cursor()
    user_id = session["user_id"]

    # 📦 PRODUITS
    produits = cursor.execute(
        "SELECT * FROM produits WHERE user_id=?",
        (user_id,)
    ).fetchall()

    nb_produits = len(produits)

    # 📄 FACTURES
    factures = cursor.execute(
        "SELECT * FROM factures WHERE user_id=?",
        (user_id,)
    ).fetchall()

    nb_factures = len(factures)

    # 💰 VENTES (sécurisé)
    result = cursor.execute("""
        SELECT SUM(total) as total FROM factures
        WHERE user_id=? AND statut='payé'
    """, (user_id,)).fetchone()

    ventes = result["total"] if result and result["total"] else 0

    # 💸 DEPENSES
    result = cursor.execute("""
        SELECT SUM(p.prix_achat * f.quantite) as total
        FROM factures f
        JOIN produits p ON f.produit_id = p.id
        WHERE f.user_id=? AND f.statut='payé'
    """, (user_id,)).fetchone()

    depenses = result["total"] if result and result["total"] else 0

    # 📈 BENEFICE
    benefice = ventes - depenses

    # ⚠️ STOCK FAIBLE (LISTE)
    stock_faible = cursor.execute("""
        SELECT nom, quantite
        FROM produits
        WHERE quantite <= 5 AND user_id=?
    """, (user_id,)).fetchall()

    # 🔔 ABONNEMENT
    jours = jours_restants(user_id)
    notification = None

    if jours is not None:
        if jours <= 7 and jours > 0:
            notification = f"⚠️ Ton abonnement expire dans {jours} jours"
        elif jours <= 0:
            notification = "❌ Ton abonnement est expiré"

    # 📊 GRAPHIQUE SIMPLE (TOP 5 FACTURES)
    labels = []
    ventes_data = []

    for f in factures[-5:]:
        labels.append(f"Facture {f['id']}")
        ventes_data.append(f["total"] if f["total"] else 0)

    # 🏆 TOP PRODUITS
    try:
        top_produits = cursor.execute("""
            SELECT p.nom, SUM(f.quantite) as total_vendu
            FROM factures f
            JOIN produits p ON f.produit_id = p.id
            WHERE f.user_id=?
            GROUP BY p.nom
            ORDER BY total_vendu DESC
            LIMIT 5
        """, (user_id,)).fetchall()
    except:
        top_produits = []

    conn.close()

    return render_template(
        "dashboard.html",
        produits=produits,
        factures=factures,
        ventes=ventes,
        depenses=depenses,
        benefice=benefice,
        stock_faible=stock_faible,
        labels=json.dumps(labels),
        ventes_data=json.dumps(ventes_data),
        top_produits=top_produits,
        notification=notification,
        nb_produits=nb_produits,
        nb_factures=nb_factures
    )


    
# -------------------------
# PRODUITS (ABONNEMENT REQUIS)
# -------------------------

@app.route("/produits")
def produits():
    if "user_id" not in session:
        return redirect("/login")
    if not verifier_abonnement(session["user_id"]):
        return redirect("/abonnement")

    conn = get_db()
    cursor = conn.cursor()

    user_id = session["user_id"]

    produits = cursor.execute(
        "SELECT * FROM produits WHERE user_id=?",
        (user_id,)
    ).fetchall()

    conn.close()

    return render_template("produits.html", produits=produits)

@app.route("/ajouter_produit", methods=["GET", "POST"])
def ajouter_produit():
    if "user_id" not in session:
        return redirect("/login")
    if not verifier_abonnement(session["user_id"]):
        return redirect("/abonnement")

    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        # 🔐 récupération sécurisée
        nom = request.form.get("nom")
        quantite = request.form.get("quantite")
        prix_achat = request.form.get("prix_achat")
        prix_vente = request.form.get("prix_vente")

        # ❌ vérification champs
        if not nom or not quantite or not prix_achat or not prix_vente:
            return "❌ Tous les champs sont obligatoires"

        quantite = int(quantite)
        prix_achat = float(prix_achat)
        prix_vente = float(prix_vente)
        user_id = session["user_id"]

        produit = cursor.execute(
            "SELECT * FROM produits WHERE nom=? AND user_id=?",
            (nom, user_id)
        ).fetchone()

        if produit:
            cursor.execute(
                "UPDATE produits SET quantite=quantite+? WHERE id=?",
                (quantite, produit["id"])
            )
        else:
            cursor.execute(
                "INSERT INTO produits (nom, quantite, prix_achat, prix_vente, user_id) VALUES (?, ?, ?, ?, ?)",
                (nom, quantite, prix_achat, prix_vente, user_id)
            )

        conn.commit()
        conn.close()

        return redirect("/produits")

    conn.close()
    return render_template("ajouter_produit.html")
# -------------------------
# ABONNEMENT (SIMULATION)
# -------------------------

@app.route("/abonnement", methods=["GET", "POST"])
def abonnement():
    try:
        # 🔐 Vérifier connexion
        if "user_id" not in session:
            return redirect("/login")

        user_id = session["user_id"]

        conn = get_db()
        cursor = conn.cursor()

        # 🔍 Vérifier utilisateur
        user = cursor.execute(
            "SELECT * FROM users WHERE id=?",
            (user_id,)
        ).fetchone()

        if user is None:
            conn.close()
            return redirect("/login")

        # 💰 Activer abonnement (simulation paiement réussi)
        cursor.execute(
            "UPDATE users SET abonnement = 1 WHERE id=?",
            (user_id,)
        )

        conn.commit()
        conn.close()

        # ✅ redirection vers abonnement
        return redirect("/abonnement")

    except Exception as e:
        print("ERREUR PAIEMENT ABONNEMENT:", e)
        return "Erreur paiement abonnement"
# -------------------------
# RUN
# -------------------------

# -------------------------
# FACTURES
# -------------------------

@app.route("/factures")
def factures():
    if "user_id" not in session:
        return redirect("/login")
    if not verifier_abonnement(session["user_id"]):
        return redirect("/abonnement")

    conn = get_db()
    factures = conn.execute("""
SELECT factures.*, produits.nom AS nom_produit
FROM factures
JOIN produits ON factures.produit_id = produits.id
WHERE factures.user_id=?
""", (session["user_id"],)).fetchall()
    conn.close()

    return render_template("factures.html", factures=factures)

@app.route("/ajouter_facture", methods=["GET", "POST"])
def ajouter_facture():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    user_id = session["user_id"]

    # 📦 récupérer produits de l'utilisateur
    produits = cursor.execute(
        "SELECT * FROM produits WHERE user_id=?",
        (user_id,)
    ).fetchall()

    if request.method == "POST":
        produit_id = int(request.form["produit_id"])
        quantite = int(request.form["quantite"])
        statut = request.form["statut"]

        # 🔍 récupérer produit sécurisé
        produit = cursor.execute(
            "SELECT * FROM produits WHERE id=? AND user_id=?",
            (produit_id, user_id)
        ).fetchone()

        # ❌ produit introuvable
        if produit is None:
            conn.close()
            return "❌ Produit introuvable"

        # ❌ stock insuffisant
        if quantite > produit["quantite"]:
            conn.close()
            return "❌ Stock insuffisant"

        # 💰 calcul total
        total = produit["prix_vente"] * quantite

        # 📉 mise à jour stock
        nouvelle_qte = produit["quantite"] - quantite

        cursor.execute(
            "UPDATE produits SET quantite=? WHERE id=?",
            (nouvelle_qte, produit_id)
        )

        # 🧾 insertion facture
        from datetime import datetime 
        date_now = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute(
            "INSERT INTO factures (produit_id, quantite, total, statut, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
            (produit_id, quantite, total, statut, user_id, date_now)
        )

        conn.commit()
        conn.close()

        return redirect("/factures")

    conn.close()
    return render_template("ajouter_facture.html", produits=produits)


# =========================
# -------------------------

init_db()
# RUN
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
