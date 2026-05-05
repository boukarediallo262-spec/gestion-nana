from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

# =====================
# APP CONFIG
# =====================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# =====================
# INIT DB SAFE
# =====================
def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
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
def startup():
    if not hasattr(app, "db_init"):
        init_db()
        app.db_init = True
        print("DB READY")

# =====================
# AUTH
# =====================
@app.route("/")
def home():
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO users(username, password)
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
        username = request.form["username"]
        password = request.form["password"]

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

# =====================
# DASHBOARD
# =====================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    uid = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM produits WHERE user_id=%s", (uid,))
    produits = cur.fetchone()["count"]

    cur.execute("SELECT COALESCE(SUM(total),0) FROM factures WHERE user_id=%s", (uid,))
    ventes = cur.fetchone()["coalesce"]

    cur.execute("SELECT COALESCE(SUM(montant),0) FROM depenses WHERE user_id=%s", (uid,))
    depenses = cur.fetchone()["coalesce"]

    conn.close()

    return render_template(
        "dashboard.html",
        produits=produits,
        ventes=ventes,
        depenses=depenses,
        benefice=ventes - depenses
    )

# =====================
# PRODUITS
# =====================
@app.route("/produits")
def produits():
    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM produits WHERE user_id=%s", (session["user_id"],))
    data = cur.fetchall()

    conn.close()
    return render_template("produits.html", produits=data)

# =====================
# IA SIMPLE (SAFE)
# =====================
@app.route("/ia", methods=["POST"])
def ia():
    data = request.get_json()
    question = data.get("message")

    response = f"Analyse simple: {question}. (IA à connecter ensuite)"
    return jsonify({"response": response})

# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
