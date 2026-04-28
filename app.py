from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os
import json

# =========================
# CONFIG
# =========================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")

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

    # FACTURES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS factures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produit_id INTEGER,
        quantite INTEGER,
        total REAL,
        statut TEXT,
        user_id INTEGER,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


# =========================
# FONCTIONS UTILES
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
    jours = (date_fin - datetime.now()).days

    return max(jours, 0)


# =========================
# HOME
# =========================
@app.route("/")
def home():
    return redirect("/login")


# =========================
# AUTH
# =========================
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

            try:
                cursor.execute("""
                    INSERT INTO users (username, password)
                    VALUES (?, ?)
                """, (
                    username,
                    generate_password_hash(password)
                ))

                conn.commit()
                conn.close()

                return redirect("/login")

            except:
                conn.close()
                error = "Utilisateur déjà existant"

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        cursor = conn.cursor()

        user = cursor.execute("""
            SELECT * FROM users
            WHERE username=?
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


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# ABONNEMENT
# =========================
@app.route("/abonnement")
def abonnement():
    if "user_id" not in session:
        return redirect("/login")

    actif = verifier_abonnement(session["user_id"])
    jours = jours_restants(session["user_id"])

    return render_template(
        "abonnement.html",
        actif=actif,
        jours=jours
    )


@app.route("/payer_abonnement", methods=["POST"])
def payer_abonnement():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cursor = conn.cursor()

    date_fin = datetime.now() + timedelta(days=30)

    cursor.execute("""
        UPDATE users
        SET abonnement=1,
            date_fin_abonnement=?
        WHERE id=?
    """, (
        date_fin.strftime("%Y-%m-%d"),
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    if not verifier_abonnement(session["user_id"]):
        return redirect("/abonnement")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    produits = cursor.execute("""
        SELECT * FROM produits
        WHERE user_id=?
    """, (user_id,)).fetchall()

    factures = cursor.execute("""
        SELECT * FROM factures
        WHERE user_id=?
        ORDER BY id DESC
    """, (user_id,)).fetchall()

    ventes = cursor.execute("""
        SELECT SUM(total) total
        FROM factures
        WHERE user_id=? AND statut='payé'
    """, (user_id,)).fetchone()["total"] or 0

    depenses = cursor.execute("""
        SELECT SUM(p.prix_achat * f.quantite) total
        FROM factures f
        JOIN produits p ON p.id=f.produit_id
        WHERE f.user_id=? AND f.statut='payé'
    """, (user_id,)).fetchone()["total"] or 0

    benefice = ventes - depenses

    stock_faible = cursor.execute("""
        SELECT *
        FROM produits
        WHERE user_id=? AND quantite <=5
        ORDER BY quantite ASC
    """, (user_id,)).fetchall()

    top_produits = cursor.execute("""
        SELECT p.nom, SUM(f.quantite) total_vendu
        FROM factures f
        JOIN produits p ON p.id=f.produit_id
        WHERE f.user_id=?
        GROUP BY p.nom
        ORDER BY total_vendu DESC
        LIMIT 5
    """, (user_id,)).fetchall()

    conn.close()

    total_produits = sum([p["quantite"] for p in produits])
    total_factures = len(factures)

    labels = []
    ventes_data = []

    for f in factures[:5]:
        labels.append(f"Facture {f['id']}")
        ventes_data.append(f["total"])

    abonnement_actif = verifier_abonnement(user_id)
    jours = jours_restants(user_id)

    notification = None
    if jours <= 7:
        notification = f"⚠️ Abonnement expire dans {jours} jours"

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
        benefice_data=json.dumps([ventes, depenses]),
        top_produits=top_produits,
        total_produits=total_produits,
        total_factures=total_factures,
        abonnement_actif=abonnement_actif,
        jours_restants=jours,
        notification=notification
    )


# =========================
# PRODUITS
# =========================
@app.route("/produits")
def produits():
    if "user_id" not in session:
        return redirect("/login")

    if not verifier_abonnement(session["user_id"]):
        return redirect("/abonnement")

    conn = get_db()

    produits = conn.execute("""
        SELECT * FROM produits
        WHERE user_id=?
    """, (session["user_id"],)).fetchall()

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
        nom = request.form["nom"]
        quantite = int(request.form["quantite"])
        prix_achat = float(request.form["prix_achat"])
        prix_vente = float(request.form["prix_vente"])
        user_id = session["user_id"]

        produit = cursor.execute("""
            SELECT * FROM produits
            WHERE nom=? AND user_id=?
        """, (nom, user_id)).fetchone()

        if produit:
            cursor.execute("""
                UPDATE produits
                SET quantite = quantite + ?
                WHERE id=?
            """, (quantite, produit["id"]))

        else:
            cursor.execute("""
                INSERT INTO produits
                (nom, quantite, prix_achat, prix_vente, user_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                nom,
                quantite,
                prix_achat,
                prix_vente,
                user_id
            ))

        conn.commit()
        conn.close()

        return redirect("/produits")

    conn.close()
    return render_template("ajouter_produit.html")


# =========================
# FACTURES
# =========================
@app.route("/factures")
def factures():
    if "user_id" not in session:
        return redirect("/login")

    if not verifier_abonnement(session["user_id"]):
        return redirect("/abonnement")

    conn = get_db()

    factures = conn.execute("""
        SELECT f.*, p.nom nom_produit
        FROM factures f
        LEFT JOIN produits p ON p.id=f.produit_id
        WHERE f.user_id=?
        ORDER BY f.id DESC
    """, (session["user_id"],)).fetchall()

    conn.close()

    return render_template("factures.html", factures=factures)


@app.route("/ajouter_facture", methods=["GET", "POST"])
def ajouter_facture():
    if "user_id" not in session:
        return redirect("/login")

    if not verifier_abonnement(session["user_id"]):
        return redirect("/abonnement")

    conn = get_db()
    cursor = conn.cursor()

    user_id = session["user_id"]

    produits = cursor.execute("""
        SELECT * FROM produits
        WHERE user_id=?
    """, (user_id,)).fetchall()

    if request.method == "POST":
        produit_id = int(request.form["produit_id"])
        quantite = int(request.form["quantite"])
        statut = request.form["statut"]

        produit = cursor.execute("""
            SELECT * FROM produits
            WHERE id=? AND user_id=?
        """, (produit_id, user_id)).fetchone()

        if not produit:
            conn.close()
            return "Produit introuvable"

        if quantite > produit["quantite"]:
            conn.close()
            return "Stock insuffisant"

        total = produit["prix_vente"] * quantite
        nouvelle_qte = produit["quantite"] - quantite

        cursor.execute("""
            UPDATE produits
            SET quantite=?
            WHERE id=?
        """, (nouvelle_qte, produit_id))

        cursor.execute("""
            INSERT INTO factures
            (produit_id, quantite, total, statut, user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            produit_id,
            quantite,
            total,
            statut,
            user_id,
            datetime.now().strftime("%Y-%m-%d")
        ))

        conn.commit()
        conn.close()

        return redirect("/factures")

    conn.close()
    return render_template("ajouter_facture.html", produits=produits)


# =========================
# IA
# =========================
@app.route("/ia")
def ia():
    if "user_id" not in session:
        return redirect("/login")

    if not verifier_abonnement(session["user_id"]):
        return redirect("/abonnement")

    user_id = session["user_id"]

    conn = get_db()
    cursor = conn.cursor()

    ventes = cursor.execute("""
        SELECT SUM(total) total
        FROM factures
        WHERE user_id=? AND statut='payé'
    """, (user_id,)).fetchone()["total"] or 0

    depenses = cursor.execute("""
        SELECT SUM(p.prix_achat * f.quantite) total
        FROM factures f
        JOIN produits p ON p.id=f.produit_id
        WHERE f.user_id=? AND f.statut='payé'
    """, (user_id,)).fetchone()["total"] or 0

    nb_produits = cursor.execute("""
        SELECT COUNT(*) total
        FROM produits
        WHERE user_id=?
    """, (user_id,)).fetchone()["total"]

    conn.close()

    prompt = f"""
Analyse ce business :

Ventes: {ventes} FCFA
Dépenses: {depenses} FCFA
Produits: {nb_produits}

Donne:
- état du business
- conseils
- stratégies pour augmenter les profits
"""

    if client is None:
        analyse = "IA non configurée"

    else:
        try:
            response = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}]
            )

            analyse = response.choices[0].message.content

        except Exception as e:
            analyse = f"Erreur IA : {e}"

    return render_template("ia.html", analyse=analyse)


# =========================
# RUN
# =========================
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
