from flask import Flask, render_template, request, redirect, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os
import json
import io
from reportlab.pdfgen import canvas

# =========================
# CONFIG APP
# =========================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")

# =========================
# OPENAI (OPTIONNEL)
# =========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if OPENAI_API_KEY:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None


# =========================
# DATABASE
# =========================
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        abonnement INTEGER DEFAULT 0,
        date_fin_abonnement TEXT
    )
    """)

    # PRODUITS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS produits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT,
        quantite INTEGER,
        prix_achat REAL,
        prix_vente REAL,
        user_id INTEGER
    )
    """)

    # FACTURES (parent)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS factures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total REAL DEFAULT 0,
        statut TEXT,
        user_id INTEGER,
        created_at TEXT
    )
    """)

    # FACTURE ITEMS (multi produits)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facture_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        facture_id INTEGER,
        produit_id INTEGER,
        quantite INTEGER,
        prix_unitaire REAL,
        total REAL
    )
    """)

    conn.commit()
    conn.close()


# =========================
# ABONNEMENT LOGIC
# =========================
def verifier_abonnement(user_id):
    conn = get_db()
    cursor = conn.cursor()

    user = cursor.execute("""
        SELECT abonnement, date_fin_abonnement
        FROM users
        WHERE id=?
    """, (user_id,)).fetchone()

    conn.close()

    if not user:
        return False

    if user["abonnement"] != 1:
        return False

    if not user["date_fin_abonnement"]:
        return False

    date_fin = datetime.strptime(user["date_fin_abonnement"], "%Y-%m-%d")
    return date_fin >= datetime.now()


def jours_restants(user_id):
    conn = get_db()
    cursor = conn.cursor()

    user = cursor.execute("""
        SELECT date_fin_abonnement
        FROM users
        WHERE id=?
    """, (user_id,)).fetchone()

    conn.close()

    if not user or not user["date_fin_abonnement"]:
        return 0

    date_fin = datetime.strptime(user["date_fin_abonnement"], "%Y-%m-%d")
    return max((date_fin - datetime.now()).days, 0)


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return redirect("/login")


# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO users (username, password)
                VALUES (?, ?)
            """, (username, generate_password_hash(password)))

            conn.commit()
            conn.close()

            return redirect("/login")

        except:
            conn.close()
            error = "Utilisateur déjà existant"

    return render_template("register.html", error=error)


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cursor = conn.cursor()

        user = cursor.execute("""
            SELECT * FROM users WHERE username=?
        """, (username,)).fetchone()

        conn.close()

        if not user:
            error = "Utilisateur introuvable"

        elif not check_password_hash(user["password"], password):
            error = "Mot de passe incorrect"

        else:
            session["user_id"] = user["id"]

            if verifier_abonnement(user["id"]):
                return redirect("/dashboard")
            else:
                return redirect("/abonnement")

    return render_template("login.html", error=error)


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# ABONNEMENT PAGE

# =========================
# ACTIVER ABONNEMENT


# =========================
# INIT DB
# =========================
init_db()

# =========================
# ABONNEMENT
# =========================
@app.route("/abonnement")
def abonnement():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    actif = verifier_abonnement(user_id)
    jours = jours_restants(user_id)

    # statut visuel propre
    if actif:
        statut = "Abonnement actif"
        couleur = "green"
    else:
        statut = "Abonnement expiré"
        couleur = "red"

    return render_template(
        "abonnement.html",
        actif=actif,
        jours=jours,
        statut=statut,
        couleur=couleur
    )


@app.route("/payer_abonnement", methods=["POST"])
def payer_abonnement():
    try:
        if "user_id" not in session:
            return redirect("/login")

        user_id = session["user_id"]

        conn = get_db()
        cursor = conn.cursor()

        # vérifier que user existe
        user = cursor.execute(
            "SELECT id FROM users WHERE id=?",
            (user_id,)
        ).fetchone()

        if not user:
            return "Utilisateur introuvable", 500

        date_fin = datetime.now() + timedelta(days=30)

        cursor.execute("""
            UPDATE users
            SET abonnement=1,
                date_fin_abonnement=?
            WHERE id=?
        """, (date_fin.strftime("%Y-%m-%d"), user_id))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    except Exception as e:
        print("🔥 ERREUR ABONNEMENT:", str(e))
        return f"Erreur serveur: {e}", 500

# =========================
# DASHBOARD (CORRIGÉ + COMPLET)
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    if not verifier_abonnement(user_id):
        return redirect("/abonnement")

    conn = get_db()
    cursor = conn.cursor()

    # 📦 PRODUITS
    produits = cursor.execute("""
        SELECT * FROM produits WHERE user_id=?
    """, (user_id,)).fetchall()

    # 📄 FACTURES
    factures = cursor.execute("""
        SELECT * FROM factures WHERE user_id=? ORDER BY id DESC
    """, (user_id,)).fetchall()

    # 🔢 CORRECTION TOTAL PRODUITS (important)
    total_produits = cursor.execute("""
        SELECT SUM(quantite) as total FROM produits WHERE user_id=?
    """, (user_id,)).fetchone()["total"] or 0

    # 🔢 FACTURES COUNT FIX
    total_factures = cursor.execute("""
        SELECT COUNT(*) as total FROM factures WHERE user_id=?
    """, (user_id,)).fetchone()["total"] or 0

    # 💰 VENTES
    ventes = cursor.execute("""
        SELECT SUM(total) total
        FROM factures
        WHERE user_id=? AND statut='payé'
    """, (user_id,)).fetchone()["total"] or 0

    # 💸 DÉPENSES
    depenses = cursor.execute("""
        SELECT SUM(p.prix_achat * f.quantite) total
        FROM factures f
        JOIN produits p ON p.id=f.produit_id
        WHERE f.user_id=? AND f.statut='payé'
    """, (user_id,)).fetchone()["total"] or 0

    benefice = ventes - depenses

    # ⚠️ STOCK FAIBLE (LISTE OK)
    stock_faible = cursor.execute("""
        SELECT * FROM produits
        WHERE user_id=? AND quantite <= 5
        ORDER BY quantite ASC
    """, (user_id,)).fetchall()

    # 🏆 TOP PRODUITS
    top_produits = cursor.execute("""
        SELECT p.nom, SUM(f.quantite) as total_vendu
        FROM factures f
        JOIN produits p ON p.id=f.produit_id
        WHERE f.user_id=?
        GROUP BY p.nom
        ORDER BY total_vendu DESC
        LIMIT 5
    """, (user_id,)).fetchall()

    conn.close()

    # 📊 GRAPHIQUE
    labels = [f"Facture {f['id']}" for f in factures[:5]]
    ventes_data = [f["total"] for f in factures[:5]]

    # 📅 ABONNEMENT
    jours = jours_restants(user_id)
    abonnement_actif = verifier_abonnement(user_id)

    if abonnement_actif:
        statut_abonnement = "Abonnement actif"
        couleur_abonnement = "green"
    else:
        statut_abonnement = "Abonnement expiré"
        couleur_abonnement = "red"

    notification = None
    if jours <= 7 and jours > 0:
        notification = f"⚠️ Abonnement expire dans {jours} jours"

    return render_template(
        "dashboard.html",
        produits=produits,
        factures=factures,
        ventes=ventes,
        depenses=depenses,
        benefice=benefice,
        stock_faible=stock_faible,
        top_produits=top_produits,

        total_produits=total_produits,
        total_factures=total_factures,

        labels=json.dumps(labels),
        ventes_data=json.dumps(ventes_data),
        benefice_data=json.dumps([ventes, depenses]),

        abonnement_actif=abonnement_actif,
        statut_abonnement=statut_abonnement,
        couleur_abonnement=couleur_abonnement,

        jours_restants=jours,
        notification=notification
    )

#====================================================
@app.route("/edit_facture/<int:facture_id>", methods=["GET", "POST"])
def edit_facture(facture_id):
    if "user_id" not in session:
        return redirect("/login")

    if not verifier_abonnement(session["user_id"]):
        return redirect("/abonnement")

    conn = get_db()
    cursor = conn.cursor()

    facture = cursor.execute("""
        SELECT * FROM factures
        WHERE id=? AND user_id=?
    """, (facture_id, session["user_id"])).fetchone()

    if not facture:
        conn.close()
        return "Facture introuvable"

    produits = cursor.execute("""
        SELECT * FROM produits WHERE user_id=?
    """, (session["user_id"],)).fetchall()

    if request.method == "POST":
        produit_id = int(request.form["produit_id"])
        quantite = int(request.form["quantite"])
        statut = request.form["statut"]

        produit = cursor.execute("""
            SELECT * FROM produits WHERE id=? AND user_id=?
        """, (produit_id, session["user_id"])).fetchone()

        if not produit:
            conn.close()
            return "Produit introuvable"

        total = produit["prix_vente"] * quantite

        cursor.execute("""
            UPDATE factures
            SET produit_id=?, quantite=?, total=?, statut=?
            WHERE id=? AND user_id=?
        """, (produit_id, quantite, total, statut, facture_id, session["user_id"]))

        conn.commit()
        conn.close()

        return redirect("/factures")

    conn.close()
    return render_template("edit_facture.html", facture=facture, produits=produits)


@app.route("/add_item_facture/<int:facture_id>", methods=["POST"])
def add_item_facture(facture_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    produit_id = int(request.form["produit_id"])
    quantite = int(request.form["quantite"])

    produit = cursor.execute("""
        SELECT * FROM produits WHERE id=?
    """, (produit_id,)).fetchone()

    if not produit:
        conn.close()
        return "Produit introuvable"

    total = produit["prix_vente"] * quantite

    cursor.execute("""
        INSERT INTO facture_items (facture_id, produit_id, quantite, prix_unitaire, total)
        VALUES (?, ?, ?, ?, ?)
    """, (
        facture_id,
        produit_id,
        quantite,
        produit["prix_vente"],
        total
    ))

    conn.commit()
    conn.close()

    return redirect(f"/facture_detail/{facture_id}")

@app.route("/facture_detail/<int:facture_id>")
def facture_detail(facture_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    facture = cursor.execute("""
        SELECT * FROM factures WHERE id=? AND user_id=?
    """, (facture_id, session["user_id"])).fetchone()

    items = cursor.execute("""
        SELECT fi.*, p.nom
        FROM facture_items fi
        JOIN produits p ON p.id = fi.produit_id
        WHERE fi.facture_id=?
    """, (facture_id,)).fetchall()

    conn.close()

    return render_template("facture_detail.html", facture=facture, items=items)

@app.route("/facture_pdf/<int:facture_id>")
def facture_pdf(facture_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    facture = cursor.execute("""
        SELECT * FROM factures WHERE id=? AND user_id=?
    """, (facture_id, session["user_id"])).fetchone()

    items = cursor.execute("""
        SELECT fi.*, p.nom
        FROM facture_items fi
        JOIN produits p ON p.id = fi.produit_id
        WHERE fi.facture_id=?
    """, (facture_id,)).fetchall()

    conn.close()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.drawString(50, 800, f"FACTURE #{facture_id}")

    y = 750
    total_global = 0

    for i in items:
        line = f"{i['nom']} | Qté:{i['quantite']} | Total:{i['total']}"
        pdf.drawString(50, y, line)
        y -= 20
        total_global += i["total"]

    pdf.drawString(50, y-20, f"TOTAL: {total_global} FCFA")

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"facture_{facture_id}.pdf")

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=5000)
