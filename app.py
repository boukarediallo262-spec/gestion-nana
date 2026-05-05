from flask import Flask, render_template, request, redirect, session, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import io
import pandas as pd
from reportlab.pdfgen import canvas

# =========================
# APP CONFIG
# =========================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

DATABASE_URL = os.getenv("DATABASE_URL")


# =========================
# DB CONNECTION
# =========================
def db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# =========================
# LOGIN REQUIRED DECORATOR
# =========================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper


# =========================
# INIT DB
# =========================
def init_db():
    conn = db()
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
        prix FLOAT,
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
def setup():
    if not hasattr(app, "ready"):
        init_db()
        app.ready = True


# =========================
# AUTH
# =========================
@app.route("/")
def home():
    return redirect("/dashboard")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO users(username,password)
            VALUES(%s,%s)
        """, (
            request.form["username"],
            generate_password_hash(request.form["password"])
        ))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        conn = db()
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
@login_required
def dashboard():
    conn = db()
    cur = conn.cursor()
    uid = session["user_id"]

    cur.execute("SELECT COALESCE(SUM(total),0) as total FROM factures WHERE user_id=%s", (uid,))
    ventes = cur.fetchone()["total"]

    cur.execute("SELECT COALESCE(SUM(montant),0) as total FROM depenses WHERE user_id=%s", (uid,))
    depenses = cur.fetchone()["total"]

    benefice = ventes - depenses

    cur.execute("SELECT * FROM produits WHERE user_id=%s", (uid,))
    produits = cur.fetchall()

    conn.close()

    return render_template("dashboard.html",
        ventes=ventes,
        depenses=depenses,
        benefice=benefice,
        produits=produits
    )


# =========================
# PRODUITS
# =========================
@app.route("/produits")
@login_required
def produits():
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM produits WHERE user_id=%s", (session["user_id"],))
    data = cur.fetchall()

    conn.close()
    return render_template("produits.html", produits=data)


@app.route("/ajouter_produit", methods=["POST"])
@login_required
def ajouter_produit():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO produits(nom,quantite,prix,user_id)
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


@app.route("/supprimer_produit/<int:id>")
@login_required
def supprimer_produit(id):
    conn = db()
    cur = conn.cursor()

    cur.execute("DELETE FROM produits WHERE id=%s", (id,))

    conn.commit()
    conn.close()
    return redirect("/produits")


# =========================
# DEPENSES
# =========================
@app.route("/depenses")
@login_required
def depenses():
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM depenses WHERE user_id=%s", (session["user_id"],))
    data = cur.fetchall()

    conn.close()
    return render_template("depenses.html", depenses=data)


@app.route("/ajouter_depense", methods=["POST"])
@login_required
def ajouter_depense():
    conn = db()
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
# FACTURES PDF
# =========================
@app.route("/facture_pdf/<int:id>")
@login_required
def facture_pdf(id):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    p.drawString(100, 800, f"FACTURE #{id}")
    p.drawString(100, 780, "Faso Gestion IA")

    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="facture.pdf")


# =========================
# EXPORT EXCEL
# =========================
@app.route("/export_excel")
@login_required
def export_excel():
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM factures WHERE user_id=%s", (session["user_id"],))
    data = cur.fetchall()

    df = pd.DataFrame(data)
    path = "/tmp/data.xlsx"
    df.to_excel(path, index=False)

    return send_file(path, as_attachment=True)


# =========================
# ABONNEMENT
# =========================
@app.route("/abonnement")
@login_required
def abonnement():
    return render_template("abonnement.html")


@app.route("/payer_abonnement", methods=["POST"])
@login_required
def payer_abonnement():
    conn = db()
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
# IA SIMPLIFIÉE (SAFE)
# =========================
@app.route("/ia")
@login_required
def ia():
    return render_template("ia.html")


@app.route("/chat_ia", methods=["POST"])
@login_required
def chat_ia():
    data = request.get_json()
    msg = data.get("message")

    return jsonify({
        "response": f"Analyse IA simulée: {msg}"
    })


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
