from flask import Flask, render_template, request, redirect, session, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os, json, io
import psycopg2
from psycopg2.extras import RealDictCursor
from reportlab.pdfgen import canvas
import pandas as pd

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret")

DATABASE_URL = os.getenv("DATABASE_URL")

# =========================
# DB
# =========================
def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# =========================
# INIT DB
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
def init_once():
    if not hasattr(app, "init_done"):
        init_db()
        app.init_done = True


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
            return f"Erreur: {e}"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s", (request.form["username"],))
        user = cur.fetchone()
        conn.close()

        if not user:
            error = "Utilisateur introuvable"
        elif not check_password_hash(user["password"], request.form["password"]):
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

    uid = session["user_id"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(total),0) as total FROM factures WHERE user_id=%s", (uid,))
    ventes = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(montant),0) as total FROM depenses WHERE user_id=%s", (uid,))
    depenses = cur.fetchone()["total"]

    benefice = ventes - depenses

    cur.execute("SELECT * FROM produits WHERE user_id=%s", (uid,))
    produits = cur.fetchall()

    cur.execute("SELECT * FROM factures WHERE user_id=%s ORDER BY id DESC LIMIT 10", (uid,))
    factures = cur.fetchall()

    conn.close()

    return render_template("dashboard.html",
        ventes=ventes,
        depenses=depenses,
        benefice=benefice,
        produits=produits,
        factures=factures
    )


# =========================
# PRODUITS
# =========================
@app.route("/produits")
def produits_page():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM produits WHERE user_id=%s", (session["user_id"],))
    produits = cur.fetchall()
    conn.close()

    return render_template("produits.html", produits=produits)


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
    return redirect("/produits")


# =========================
# FACTURES
# =========================
@app.route("/factures")
def factures_page():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM factures WHERE user_id=%s", (session["user_id"],))
    factures = cur.fetchall()

    conn.close()
    return render_template("factures.html", factures=factures)


# =========================
# DEPENSES
# =========================
@app.route("/depenses")
def depenses_page():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM depenses WHERE user_id=%s", (session["user_id"],))
    depenses = cur.fetchall()

    conn.close()
    return render_template("depenses.html", depenses=depenses)


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

    return redirect("/depenses")


# =========================
# ABONNEMENT
# =========================
@app.route("/abonnement")
def abonnement():
    return render_template("abonnement.html")


@app.route("/payer_abonnement", methods=["POST"])
def payer_abonnement():
    conn = get_db()
    cur = conn.cursor()

    date_fin = datetime.now() + timedelta(days=30)

    cur.execute("""
        UPDATE users
        SET abonnement=1, date_fin_abonnement=%s
        WHERE id=%s
    """, (date_fin, session["user_id"]))

    conn.commit()
    conn.close()

    return redirect("/dashboard")


# =========================
# IA (safe version)
# =========================
@app.route("/ia")
def ia_page():
    return render_template("ia.html")


@app.route("/chat_ia", methods=["POST"])
def chat_ia():
    data = request.get_json()
    question = data.get("message")

    return jsonify({
        "response": f"Analyse IA simulée: {question}"
    })


# =========================
# EXPORT
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
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
