from flask import Flask, render_template, request, redirect, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import os
import json
import io
from reportlab.pdfgen import canvas

# =========================
# APP CONFIG
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        abonnement INTEGER DEFAULT 0,
        date_fin_abonnement TEXT
    )
    """)

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS factures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total REAL DEFAULT 0,
        statut TEXT,
        user_id INTEGER,
        created_at TEXT
    )
    """)

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
    user = conn.execute("""
        SELECT abonnement, date_fin_abonnement
        FROM users WHERE id=?
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
    user = conn.execute("""
        SELECT date_fin_abonnement FROM users WHERE id=?
    """, (user_id,)).fetchone()
    conn.close()

    if not user or not user["date_fin_abonnement"]:
        return 0

    date_fin = datetime.strptime(user["date_fin_abonnement"], "%Y-%m-%d")
    return max((date_fin - datetime.now()).days, 0)


# =========================
# INIT DB
# =========================
init_db()


# =========================
# ROUTES AUTH
# =========================
@app.route("/")
def home():
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return redirect("/login")
        except:
            error = "Utilisateur déjà existant"
        finally:
            conn.close()

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()

        if not user:
            error = "Utilisateur introuvable"
        elif not check_password_hash(user["password"], password):
            error = "Mot de passe incorrect"
        else:
            session["user_id"] = user["id"]
            return redirect("/dashboard" if verifier_abonnement(user["id"]) else "/abonnement")

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

    user_id = session["user_id"]
    actif = verifier_abonnement(user_id)
    jours = jours_restants(user_id)

    return render_template(
        "abonnement.html",
        actif=actif,
        jours=jours,
        statut="Actif" if actif else "Expiré",
        couleur="green" if actif else "red"
    )


@app.route("/payer_abonnement", methods=["POST"])
def payer_abonnement():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    date_fin = datetime.now() + timedelta(days=30)

    conn = get_db()
    conn.execute("""
        UPDATE users
        SET abonnement=1, date_fin_abonnement=?
        WHERE id=?
    """, (date_fin.strftime("%Y-%m-%d"), user_id))
    conn.commit()
    conn.close()

    return redirect("/dashboard")


# =========================
# DASHBOARD PROPRE
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    if not verifier_abonnement(user_id):
        return redirect("/abonnement")

    conn = get_db()

    produits = conn.execute("SELECT * FROM produits WHERE user_id=?", (user_id,)).fetchall()
    factures = conn.execute("SELECT * FROM factures WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()

    total_produits = conn.execute(
        "SELECT COALESCE(SUM(quantite),0) as total FROM produits WHERE user_id=?",
        (user_id,)
    ).fetchone()["total"]

    total_factures = conn.execute(
        "SELECT COUNT(*) as total FROM factures WHERE user_id=?",
        (user_id,)
    ).fetchone()["total"]

    ventes = conn.execute(
        "SELECT COALESCE(SUM(total),0) as total FROM factures WHERE user_id=? AND statut='payé'",
        (user_id,)
    ).fetchone()["total"]

    depenses = conn.execute("""
        SELECT COALESCE(SUM(fi.total),0) as total
        FROM facture_items fi
        JOIN factures f ON f.id = fi.facture_id
        WHERE f.user_id=? AND f.statut='payé'
    """, (user_id,)).fetchone()["total"]

    stock_faible = conn.execute(
        "SELECT * FROM produits WHERE user_id=? AND quantite<=5",
        (user_id,)
    ).fetchall()

    top_produits = conn.execute("""
        SELECT p.nom, COALESCE(SUM(fi.quantite),0) as total
        FROM facture_items fi
        JOIN produits p ON p.id = fi.produit_id
        JOIN factures f ON f.id = fi.facture_id
        WHERE f.user_id=?
        GROUP BY p.nom
        ORDER BY total DESC
        LIMIT 5
    """, (user_id,)).fetchall()

    conn.close()

    benefice = ventes - depenses

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
        top_produits=top_produits,
        jours_restants=jours_restants(user_id),
        abonnement_actif=verifier_abonnement(user_id)
    )


# =========================
# FACTURE DETAIL + PDF
# =========================
@app.route("/facture_detail/<int:id>")
def facture_detail(id):
    conn = get_db()
    facture = conn.execute("SELECT * FROM factures WHERE id=?", (id,)).fetchone()

    items = conn.execute("""
        SELECT fi.*, p.nom
        FROM facture_items fi
        JOIN produits p ON p.id=fi.produit_id
        WHERE fi.facture_id=?
    """, (id,)).fetchall()

    conn.close()

    return render_template("facture_detail.html", facture=facture, items=items)


@app.route("/facture_pdf/<int:id>")
def facture_pdf(id):
    conn = get_db()
    items = conn.execute("""
        SELECT fi.*, p.nom
        FROM facture_items fi
        JOIN produits p ON p.id=fi.produit_id
        WHERE fi.facture_id=?
    """, (id,)).fetchall()
    conn.close()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.drawString(50, 800, f"FACTURE #{id}")

    y = 760
    total = 0

    for i in items:
        pdf.drawString(50, y, f"{i['nom']} | {i['quantite']} | {i['total']}")
        y -= 20
        total += i["total"]

    pdf.drawString(50, y-20, f"TOTAL: {total} FCFA")

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"facture_{id}.pdf")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
