from flask import Flask, render_template, request, redirect, session, send_file, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os, json, io
import psycopg2
from psycopg2.extras import RealDictCursor
from reportlab.pdfgen import canvas
from openai import OpenAI

# =========================
# APP CONFIG
# =========================
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret")

DATABASE_URL = os.getenv("DATABASE_URL")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None


# =========================
# DB
# =========================
def db():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


# =========================
# INIT DB
# =========================
def init():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS produits(
        id SERIAL PRIMARY KEY,
        nom TEXT,
        quantite INT,
        prix_vente FLOAT,
        user_id INT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS factures(
        id SERIAL PRIMARY KEY,
        total FLOAT DEFAULT 0,
        statut TEXT DEFAULT 'impayé',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS facture_items(
        id SERIAL PRIMARY KEY,
        facture_id INT,
        produit_id INT,
        quantite INT,
        total FLOAT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS depenses(
        id SERIAL PRIMARY KEY,
        categorie TEXT,
        montant FLOAT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INT
    )""")

    conn.commit()
    conn.close()

init()


# =========================
# AUTH
# =========================
@app.route("/")
def home():
    return redirect("/login")


@app.route("/register", methods=["POST","GET"])
def register():
    if request.method == "POST":
        conn = db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users(username,password) VALUES(%s,%s)",
            (request.form["username"], generate_password_hash(request.form["password"]))
        )
        conn.commit()
        conn.close()
        return redirect("/login")
    return render_template("register.html")


@app.route("/login", methods=["POST","GET"])
def login():
    if request.method == "POST":
        conn = db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s",(request.form["username"],))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], request.form["password"]):
            session["user_id"] = user["id"]
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# DASHBOARD + FILTRE
# =========================
@app.route("/dashboard")
def dashboard():
    uid = session.get("user_id")
    if not uid:
        return redirect("/login")

    filtre = request.args.get("filtre","mois")

    conn = db()
    cur = conn.cursor()

    # PRODUITS
    cur.execute("SELECT * FROM produits WHERE user_id=%s",(uid,))
    produits = cur.fetchall()

    # FACTURES
    cur.execute("SELECT * FROM factures WHERE user_id=%s ORDER BY id DESC",(uid,))
    factures = cur.fetchall()

    # VENTES
    cur.execute("SELECT COALESCE(SUM(total),0) FROM factures WHERE user_id=%s AND statut='payé'",(uid,))
    ventes = cur.fetchone()["coalesce"]

    # DEPENSES
    cur.execute("SELECT COALESCE(SUM(montant),0) FROM depenses WHERE user_id=%s",(uid,))
    depenses = cur.fetchone()["coalesce"]

    conn.close()

    benefice = ventes - depenses

    return render_template("dashboard.html",
        produits=produits,
        factures=factures,
        ventes=ventes,
        depenses=depenses,
        benefice=benefice,
        filtre=filtre
    )


# =========================
# PRODUITS CRUD
# =========================
@app.route("/ajouter_produit", methods=["POST"])
def ajouter_produit():
    uid = session["user_id"]
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO produits(nom,quantite,prix_vente,user_id)
        VALUES(%s,%s,%s,%s)
    """,(request.form["nom"],request.form["quantite"],request.form["prix"],uid))
    conn.commit()
    conn.close()
    return redirect("/dashboard")


@app.route("/supprimer_produit/<int:id>")
def supprimer_produit(id):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM produits WHERE id=%s",(id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")


# =========================
# DEPENSES CRUD
# =========================
@app.route("/ajouter_depense", methods=["POST"])
def ajouter_depense():
    uid = session["user_id"]
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO depenses(categorie,montant,description,user_id)
        VALUES(%s,%s,%s,%s)
    """,(request.form["categorie"],request.form["montant"],request.form["description"],uid))
    conn.commit()
    conn.close()
    return redirect("/dashboard")


@app.route("/supprimer_depense/<int:id>")
def supprimer_depense(id):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM depenses WHERE id=%s",(id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")


# =========================
# FACTURE PDF
# =========================
@app.route("/facture_pdf/<int:id>")
def pdf(id):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM facture_items WHERE facture_id=%s",(id,))
    items = cur.fetchall()

    y = 800
    total = 0

    p.drawString(50,820,f"FACTURE #{id}")

    for i in items:
        p.drawString(50,y,f"{i['quantite']} x {i['total']}")
        total += i["total"]
        y -= 20

    p.drawString(50,y-20,f"TOTAL: {total}")
    p.save()

    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="facture.pdf")


# =========================
# IA COMPTABLE + FRAUDE
# =========================
@app.route("/ia", methods=["POST"])
def ia():
    if not client:
        return jsonify({"response":"IA non configurée"})

    uid = session["user_id"]

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(total),0) FROM factures WHERE user_id=%s",(uid,))
    ventes = cur.fetchone()["coalesce"]

    cur.execute("SELECT COALESCE(SUM(montant),0) FROM depenses WHERE user_id=%s",(uid,))
    depenses = cur.fetchone()["coalesce"]

    conn.close()

    prompt = f"""
Tu es comptable et analyste financier.

Ventes: {ventes}
Dépenses: {depenses}
Bénéfice: {ventes - depenses}

Donne:
- analyse
- conseils
- risques de fraude
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return jsonify({"response":res.choices[0].message.content})


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
