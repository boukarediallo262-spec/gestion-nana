from flask import Blueprint, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash

from app.models.models import db, User

auth_bp = Blueprint("auth", __name__)


# =========================
# REGISTER
# =========================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    error = None

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        existing = User.query.filter_by(username=username).first()

        if existing:
            error = "Utilisateur existe déjà"

        else:
            user = User(
                username=username,
                password=generate_password_hash(password)
            )

            db.session.add(user)
            db.session.commit()

            return redirect("/login")

    return render_template("register.html", error=error)


# =========================
# LOGIN
# =========================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if not user:
            error = "Utilisateur introuvable"

        elif not check_password_hash(user.password, password):
            error = "Mot de passe incorrect"

        else:
            session["user_id"] = user.id

            return redirect("/dashboard")

    return render_template("login.html", error=error)


# =========================
# LOGOUT
# =========================
@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/login")
