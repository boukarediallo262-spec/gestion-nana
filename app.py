from services.ai_service import ask_ai
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
    cur.execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS abonnement INT DEFAULT 0
    """)

    cur.execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS date_fin_abonnement DATE
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
from datetime import datetime, timedelta
import json

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    uid = session["user_id"]
    conn = get_db()
    cur = conn.cursor()

    # 📊 KPI
    cur.execute("SELECT COUNT(*) FROM produits WHERE user_id=%s", (uid,))
    produits = cur.fetchone()["count"]

    cur.execute("SELECT COALESCE(SUM(total),0) FROM factures WHERE user_id=%s", (uid,))
    ventes = cur.fetchone()["coalesce"]

    cur.execute("SELECT COALESCE(SUM(montant),0) FROM depenses WHERE user_id=%s", (uid,))
    depenses = cur.fetchone()["coalesce"]

    benefice = ventes - depenses

    # 📈 DONNÉES GRAPHIQUES (7 jours)
    cur.execute("""
        SELECT DATE(created_at) as date, SUM(total) as total
        FROM factures
        WHERE user_id=%s
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 7
    """, (uid,))
    ventes_data = cur.fetchall()

    cur.execute("""
        SELECT DATE(created_at) as date, SUM(montant) as total
        FROM depenses
        WHERE user_id=%s
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 7
    """, (uid,))
    dep_data = cur.fetchall()

    conn.close()

    # Format graphique
    labels = [str(d["date"]) for d in ventes_data][::-1]
    ventes_chart = [float(d["total"] or 0) for d in ventes_data][::-1]

    dep_map = {str(d["date"]): float(d["total"]) for d in dep_data}
    dep_chart = [dep_map.get(l, 0) for l in labels]

    benef_chart = [ventes_chart[i] - dep_chart[i] for i in range(len(labels))]

    # ⚠️ ALERTES
    alerts = []
    if benefice < 0:
        alerts.append("⚠️ Ton business est en perte")

    if depenses > ventes:
        alerts.append("⚠️ Dépenses supérieures aux ventes")

    if produits == 0:
        alerts.append("⚠️ Aucun produit enregistré")

    # 🧠 INSIGHT SIMPLE
    insight = "Ton business est stable"
    if benefice > 100000:
        insight = "🔥 Forte rentabilité"
    elif benefice < 0:
        insight = "⚠️ Situation critique"

    return render_template(
        "dashboard.html",
        produits=produits,
        ventes=ventes,
        depenses=depenses,
        benefice=benefice,

        labels=json.dumps(labels),
        ventes_chart=json.dumps(ventes_chart),
        dep_chart=json.dumps(dep_chart),
        benef_chart=json.dumps(benef_chart),

        alerts=alerts,
        insight=insight
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
@app.route("/ia_pro", methods=["POST"])
def ia_pro():
    if not client:
        return jsonify({"response": "IA non configurée"})

    uid = session.get("user_id")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COALESCE(SUM(total),0) FROM factures WHERE user_id=%s", (uid,))
    ventes = cur.fetchone()["coalesce"]

    cur.execute("SELECT COALESCE(SUM(montant),0) FROM depenses WHERE user_id=%s", (uid,))
    dep = cur.fetchone()["coalesce"]

    conn.close()

    prompt = f"""
Entreprise:
Ventes: {ventes}
Dépenses: {dep}
Bénéfice: {ventes - dep}

Analyse comme un expert africain.
"""

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}]
    )

    return jsonify({"response": res.choices[0].message.content})
# =====================
@app.route("/chat_ia", methods=["POST"])
def chat_ia():
    if not client:
        return jsonify({"response": "IA non configurée"})

    data = request.get_json()
    question = data.get("message", "")

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":question}]
    )

    return jsonify({"response": res.choices[0].message.content})

#=========================
from functools import wraps

def abonnement_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")

        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT abonnement, date_fin_abonnement
            FROM users WHERE id=%s
        """, (session["user_id"],))

        user = cur.fetchone()
        conn.close()

        if not user:
            return redirect("/login")

        if user["abonnement"] == 0:
            return redirect("/abonnement")

        if user["date_fin_abonnement"] and user["date_fin_abonnement"] < datetime.now().date():
            return redirect("/abonnement")

        return f(*args, **kwargs)

    return decorated

#=====================
@app.route("/payer", methods=["POST"])
def payer():
    user_id = session["user_id"]

    # ici tu peux vérifier paiement manuel

    conn = get_db()
    cur = conn.cursor()

    date_fin = datetime.now() + timedelta(days=30)

    cur.execute("""
        UPDATE users
        SET abonnement=1, date_fin_abonnement=%s
        WHERE id=%s
    """, (date_fin, user_id))

    conn.commit()
    conn.close()

    return redirect("/dashboard")



#====================
@app.route("/create_facture", methods=["POST"])
def create_facture():
    uid = session["user_id"]
    items = request.json["items"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO factures(user_id,total)
        VALUES(%s,0) RETURNING id
    """, (uid,))

    facture_id = cur.fetchone()["id"]

    total = 0

    for item in items:
        total += item["prix"] * item["quantite"]

        cur.execute("""
            INSERT INTO facture_items(facture_id,produit_id,quantite,total)
            VALUES(%s,%s,%s,%s)
        """, (
            facture_id,
            item["id"],
            item["quantite"],
            item["prix"] * item["quantite"]
        ))

    cur.execute("UPDATE factures SET total=%s WHERE id=%s", (total, facture_id))

    conn.commit()
    conn.close()

    return jsonify({"success": True})

#======================
@app.route("/facture_pdf/<int:id>")
def pdf(id):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)

    conn = get_db()
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
# RUN
# =====================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
