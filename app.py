# =========================
# APP.PY COMPLET (SAAS SIMPLE)
# =========================

from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "n'importe_quoi_de_secret"

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
        abonnement INTEGER DEFAULT 0
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
        user_id INTEGER
    )
    ''')

    conn.commit()
    conn.close()

# -------------------------
# AUTH
@app.route("/")
def home():
    return redirect("/login")
# -------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        try:
            username = request.form.get("username")
            password = request.form.get("password")

            conn = get_db()
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )

            conn.commit()
            conn.close()

            return redirect("/login")

        except Exception as e:
            return f"ERREUR: {str(e)}"  # 🔥 pour voir vrai problème

    return render_template("register.html", error=error)

@app.route("/login", methods=["GET", "POST"]) 
def login():
    error = None

    # Vérifier si déjà connecté
    if "user_id" in session:
        return redirect("/dashboard")

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Vérification simple
        if not username or not password:
            error = "❌ Tous les champs sont obligatoires"
            return render_template("login.html", error=error)

        conn = get_db()
        cursor = conn.cursor()

        user = cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        conn.close()

        if user:
            session["user_id"] = user["id"]
            return redirect("/dashboard")
        else:
            error = "❌ Identifiant ou mot de passe incorrect"

    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -------------------------
# DASHBOARD
# -------------------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    user_id = session["user_id"]

    # 📦 PRODUITS
    produits = cursor.execute(
        "SELECT * FROM produits WHERE user_id=?",
        (user_id,)
    ).fetchall()

    total_produits = len(produits)

    # 📄 FACTURES
    factures = cursor.execute(
        "SELECT * FROM factures WHERE user_id=?",
        (user_id,)
    ).fetchall()

    total_factures = len(factures)

    # 💰 VENTES
    ventes = cursor.execute("""
        SELECT SUM(total) as total FROM factures
        WHERE user_id=? AND statut='payé'
    """, (user_id,)).fetchone()["total"] or 0

    # 💸 DÉPENSES
    depenses = cursor.execute("""
        SELECT SUM(p.prix_achat * f.quantite) as total
        FROM factures f
        JOIN produits p ON f.produit_id = p.id
        WHERE f.user_id=? AND f.statut='payé'
    """, (user_id,)).fetchone()["total"] or 0

    # 📈 BÉNÉFICE
    benefice = ventes - depenses

    # 📦 STOCK FAIBLE
    stock_faible = len([p for p in produits if p["quantite"] < 5])

    conn.close()

    import json

# ...

labels = []
ventes_data = []

for f in factures[-10:]:
    labels.append(str(f["id"]))
    ventes_data.append(f["total"])

return render_template(
    "dashboard.html",
    produits=produits,
    factures=factures,
    total_produits=total_produits,
    total_factures=total_factures,
    ventes=ventes,
    depenses=depenses,
    benefice=benefice,
    stock_faible=stock_faible,
    labels=json.dumps(labels),
    ventes_data=json.dumps(ventes_data)
)
# -------------------------
# PRODUITS (ABONNEMENT REQUIS)
# -------------------------

@app.route("/produits")
def produits():
    if "user_id" not in session:
        return redirect("/login")

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
    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        conn = get_db()
        conn.execute("UPDATE users SET abonnement=1 WHERE id=?", (session["user_id"],))
        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("abonnement.html")

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
        cursor.execute(
            "INSERT INTO factures (produit_id, quantite, total, statut, user_id) VALUES (?, ?, ?, ?, ?)",
            (produit_id, quantite, total, statut, user_id)
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
