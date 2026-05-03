import traceback
import os
print("=== APP START ===")
print("DATABASE_URL =", os.getenv("DATABASE_URL"))

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

DATABASE_URL = os.environ.get("DATABASE_URL")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None


# =========================
# DB
# =========================
def db():
    return psycopg2.connect(DATABASE_URL, sslmode="require", cursor_factory=RealDictCursor)


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
        prix_vente NUMERIC(12,2),
        user_id INT
    )""")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS factures(
        id SERIAL PRIMARY KEY,
        total NUMERIC(12,2),
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
        total NUMERIC(12,2)
    )""")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS depenses(
        id SERIAL PRIMARY KEY,
        categorie TEXT,
        montant NUMERIC(12,2),
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INT
    )""")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS entreprises(
        id SERIAL PRIMARY KEY,
        nom TEXT,
        owner_id INT,
        abonnement TEXT DEFAULT 'free',
        date_expiration DATE
    )
    """)

    cur.execute("""
        ALTER TABLE users ADD COLUMN IF NOT EXISTS entreprise_id INT
    """)

    cur.execute("""
        ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'admin'
    """)

    conn.commit()
    cur.close()
    conn.close()

@app.before_request
def initialize_once():
    global db_initialized

    if not globals().get("db_initialized"):
        try:
            init()
            db_initialized = True
            print("Database initialized")
        except Exception as e:
            print("Init DB error:", e)


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
        cur.execute("SELECT * FROM users WHERE username=%s AND entreprise_id=%s",(request.form["username, entreprise_id"],))
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
def check_abonnement(entreprise_id):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT abonnement, date_expiration
        FROM entreprises
        WHERE id=%s
    """, (entreprise_id,))

    data = cur.fetchone()
    conn.close()

    if not data:
        return False

    if data["abonnement"] == "free":
        return True

    if data["date_expiration"] and data["date_expiration"] >= datetime.now().date():
        return True

    return False

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

    cur.execute("SELECT entreprise_id FROM users WHERE id=%s", (uid,))
    ent = cur.fetchone()["entreprise_id"]

    if not check_abonnement(ent):
        return redirect("/abonnement")

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


# =========================#

# route abonnement

@app.route("/abonnement")
def abonnement():
    return render_template("abonnement.html")
#==========================================
@app.route("/activer_abonnement", methods=["POST"])
def activer_abonnement():
    uid = session.get("user_id")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT entreprise_id FROM users WHERE id=%s", (uid,))
    ent = cur.fetchone()["entreprise_id"]

    expiration = datetime.now() + timedelta(days=30)

    cur.execute("""
        UPDATE entreprises
        SET abonnement='pro', date_expiration=%s
        WHERE id=%s
    """, (expiration.date(), ent))

    conn.commit()
    conn.close()

    return redirect("/dashboard")
#====================================
@app.route("/create_entreprise", methods=["POST"])
def create_entreprise():
    uid = session.get("user_id")

    conn = db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO entreprises(nom, owner_id)
        VALUES(%s,%s) RETURNING id
    """, (request.form["nom"], uid))

    entreprise_id = cur.fetchone()["id"]

    cur.execute("""
        UPDATE users SET entreprise_id=%s, role='admin'
        WHERE id=%s
    """, (entreprise_id, uid))

    conn.commit()
    conn.close()

    return redirect("/dashboard")
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
@app.route("/invite_user", methods=["POST"])
def invite_user():
    uid = session.get("user_id")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT entreprise_id FROM users WHERE id=%s", (uid,))
    ent = cur.fetchone()["entreprise_id"]

    cur.execute("""
        INSERT INTO users(username,password,entreprise_id,role)
        VALUES(%s,%s,%s,%s)
    """, (
        request.form["username"],
        generate_password_hash("123456"),
        ent,
        "vendeur"
    ))

    conn.commit()
    conn.close()

    return redirect("/dashboard")
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
@app.route("/saas_ia", methods=["POST"])
def saas_ia():
    uid = session.get("user_id")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT entreprise_id FROM users WHERE id=%s", (uid,))
    ent = cur.fetchone()["entreprise_id"]

    cur.execute("""
        SELECT COALESCE(SUM(total),0) FROM factures
        WHERE user_id IN (
            SELECT id FROM users WHERE entreprise_id=%s
        )
    """, (ent,))
    ventes = cur.fetchone()["coalesce"]

    cur.execute("""
        SELECT COALESCE(SUM(montant),0) FROM depenses
        WHERE user_id IN (
            SELECT id FROM users WHERE entreprise_id=%s
        )
    """, (ent,))
    dep = cur.fetchone()["coalesce"]

    prompt = f"""
Entreprise SaaS:
Ventes: {ventes}
Dépenses: {dep}
Bénéfice: {ventes - dep}

Analyse comme un CEO SaaS.
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return jsonify({"response": res.choices[0].message.content})

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
#========================

@app.route("/ia_pro", methods=["POST"])
def ia_pro():
    uid = session.get("user_id")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(total),0) FROM factures WHERE user_id=%s", (uid,))
    ventes = cur.fetchone()["coalesce"]

    cur.execute("SELECT COALESCE(SUM(montant),0) FROM depenses WHERE user_id=%s", (uid,))
    dep = cur.fetchone()["coalesce"]

    conn.close()

    prompt = f"""
Tu es un expert comptable senior et analyste financier.

Entreprise:
- Ventes: {ventes}
- Dépenses: {dep}
- Résultat: {ventes - dep}

Donne:
1. analyse complète
2. risques financiers
3. fraude possible
4. recommandations stratégiques
5. prédiction du mois prochain
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return jsonify({"response": res.choices[0].message.content})
#=========================
@app.route("/chat_ia", methods=["POST"])
def chat_ia():
    if not client:
        return jsonify({"response": "IA non configurée"})

    uid = session.get("user_id")
    if not uid:
        return jsonify({"response": "Non autorisé"})

    data = request.get_json()
    question = data.get("message", "")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(total),0) FROM factures WHERE user_id=%s", (uid,))
    ventes = cur.fetchone()["coalesce"]

    cur.execute("SELECT COALESCE(SUM(montant),0) FROM depenses WHERE user_id=%s", (uid,))
    depenses = cur.fetchone()["coalesce"]

    conn.close()

    prompt = f"""
Tu es un assistant financier professionnel pour une entreprise.

Données utilisateur :
- Ventes: {ventes}
- Dépenses: {depenses}
- Bénéfice: {ventes - depenses}

Question utilisateur:
{question}

Réponds comme un comptable + conseiller financier + détecteur de fraude.
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return jsonify({"response": res.choices[0].message.content})

#==============================
@app.route("/alertes")
def alertes():
    uid = session.get("user_id")

    conn = db()
    cur = conn.cursor()

    # Stock faible
    cur.execute("SELECT nom FROM produits WHERE user_id=%s AND quantite <= 5", (uid,))
    stock = cur.fetchall()

    # Dépenses élevées
    cur.execute("SELECT COALESCE(SUM(montant),0) FROM depenses WHERE user_id=%s", (uid,))
    dep = cur.fetchone()["coalesce"]

    conn.close()

    alerts = []

    if stock:
        alerts.append(f"⚠ Stock faible: {len(stock)} produit(s)")

    if dep > 500000:
        alerts.append("⚠ Dépenses très élevées détectées")

    return {"alerts": alerts}

#=====================
import pandas as pd

@app.route("/export_excel")
def export_excel():
    uid = session.get("user_id")

    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM factures WHERE user_id=%s", (uid,))
    data = cur.fetchall()

    df = pd.DataFrame(data)
    file_path = "/tmp/factures.xlsx"
    df.to_excel(file_path, index=False)

    return send_file(file_path, as_attachment=True)
#==================================



# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
