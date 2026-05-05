from flask import Flask, render_template, request, redirect, session, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os, json, io
import psycopg2
from psycopg2.extras import RealDictCursor
from reportlab.pdfgen import canvas
import pandas as pd

# =========================
# CONFIG
# =========================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback-secret")

DATABASE_URL = os.getenv("DATABASE_URL")


# =========================
# DB CONNECTION
# =========================
def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# =========================
# INIT DATABASE
# =========================
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        abonnement INT DEFAULT 0,
        date_fin_abonnement DATE
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS produits (
        id SERIAL PRIMARY KEY,
        nom TEXT,
        quantite INT,
        prix_vente FLOAT,
        user_id INT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS factures (
        id SERIAL PRIMARY KEY,
        total FLOAT DEFAULT 0,
        statut TEXT DEFAULT 'impayé',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS facture_items (
        id SERIAL PRIMARY KEY,
        facture_id INT,
        produit_id INT,
        quantite INT,
        total FLOAT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS depenses (
        id SERIAL PRIMARY KEY,
        categorie TEXT,
        montant FLOAT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INT
    )
    """)

    conn.commit()
    conn.close()


@app.before_request
def initialize():
    if not hasattr(app, "db_initialized"):
        init_db()
        app.db_initialized = True
        print("Database initialized")


# =========================
# AUTH
# =========================
@app.route("/")
def home():
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            conn = get_db()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO users(username,password) VALUES(%s,%s)",
                (
                    request.form["username"],
                    generate_password_hash(request.form["password"])
                )
            )

            conn.commit()
            conn.close()

            return redirect("/login")

        except Exception as e:
            return f"Erreur inscription: {e}"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        conn.close()

        if not user:
            error = "Utilisateur introuvable"
        elif not check_password_hash(user["password"], password):
            error = "Mot de passe incorrect"
        else:
            session["user_id"] = user["id"]
            return redirect("/dashboard")

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cur = conn.cursor()

    # ventes
    cur.execute("""
        SELECT COALESCE(SUM(total),0) as total
        FROM factures
        WHERE user_id=%s AND statut='payé'
    """, (user_id,))
    ventes = cur.fetchone()["total"]

    # dépenses
    cur.execute("""
        SELECT COALESCE(SUM(montant),0) as total
        FROM depenses
        WHERE user_id=%s
    """, (user_id,))
    depenses = cur.fetchone()["total"]

    benefice = ventes - depenses

    # produits
    cur.execute("SELECT * FROM produits WHERE user_id=%s", (user_id,))
    produits = cur.fetchall()

    total_produits = sum([p["quantite"] for p in produits]) if produits else 0

    # factures
    cur.execute("""
        SELECT * FROM factures
        WHERE user_id=%s
        ORDER BY id DESC LIMIT 10
    """, (user_id,))
    factures = cur.fetchall()

    cur.execute("SELECT COUNT(*) as count FROM factures WHERE user_id=%s", (user_id,))
    total_factures = cur.fetchone()["count"]

    conn.close()

    return render_template(
        "dashboard.html",
        ventes=ventes,
        depenses=depenses,
        benefice=benefice,
        total_produits=total_produits,
        total_factures=total_factures
    )


# =========================
# PRODUITS
# =========================
@app.route("/ajouter_produit", methods=["POST"])
def ajouter_produit():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO produits(nom,quantite,prix_vente,user_id)
        VALUES(%s,%s,%s,%s)
    """, (
        request.form["nom"],
        request.form["quantite"],
        request.form["prix"],
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


@app.route("/supprimer_produit/<int:id>")
def supprimer_produit(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM produits WHERE id=%s", (id,))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# =========================
# DEPENSES
# =========================
@app.route("/ajouter_depense", methods=["POST"])
def ajouter_depense():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO depenses(categorie,montant,description,user_id)
        VALUES(%s,%s,%s,%s)
    """, (
        request.form["categorie"],
        request.form["montant"],
        request.form["description"],
        session["user_id"]
    ))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# =========================
# EXPORT EXCEL
# =========================
@app.route("/export_excel")
def export_excel():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM factures WHERE user_id=%s", (session["user_id"],))
    data = cur.fetchall()

    df = pd.DataFrame(data)
    path = "/tmp/export.xlsx"
    df.to_excel(path, index=False)

    return send_file(path, as_attachment=True)


# =========================
# PDF FACTURE
# =========================
@app.route("/facture_pdf/<int:id>")
def facture_pdf(id):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM facture_items WHERE facture_id=%s", (id,))
    items = cur.fetchall()

    y = 800
    total = 0

    for i in items:
        p.drawString(50, y, f"{i['quantite']} x {i['total']}")
        total += i["total"]
        y -= 20

    p.drawString(50, y-20, f"TOTAL: {total}")
    p.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="facture.pdf")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
