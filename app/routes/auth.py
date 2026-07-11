from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required

from app.models import db, User

auth_bp = Blueprint("auth", __name__)


# ==========================
# LOGIN
# ==========================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):

            login_user(user)

            return redirect(url_for("dashboard.home"))

        flash("Email ou mot de passe incorrect.", "danger")

    return render_template("auth/login.html")


# ==========================
# LOGOUT
# ==========================

@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("auth.login"))


# ==========================
# REGISTER
# ==========================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        # Vérifie si l'utilisateur existe déjà
        existe = User.query.filter_by(
            email=request.form["email"]
        ).first()

        if existe:
            flash("Cet email existe déjà.", "warning")
            return redirect(url_for("auth.register"))

        user = User(
            nom=request.form["nom"],
            email=request.form["email"],
            role="Utilisateur"
        )

        user.set_password(request.form["password"])

        db.session.add(user)
        db.session.commit()

        flash("Compte créé avec succès.", "success")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")
