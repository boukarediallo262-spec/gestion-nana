from flask import Blueprint, render_template, request, redirect, url_for, session

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

            session["user_id"] = user.id
            session["user_role"] = user.role

            return redirect(url_for("dashboard.home"))

        return render_template("auth/login.html", error="Identifiants incorrects")

    return render_template("auth/login.html")


# ==========================
# LOGOUT
# ==========================

@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("auth.login"))


# ==========================
# REGISTER (option admin)
# ==========================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        user = User(
            nom=request.form["nom"],
            email=request.form["email"],
            role="Utilisateur"
        )

        user.set_password(request.form["password"])

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")
