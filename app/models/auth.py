from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for

from app.models import db
from app.models import User

auth_bp = Blueprint(
    "auth",
    __name__
)


# ==========================
# CONNEXION
# ==========================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        # Le système de connexion complet sera ajouté plus tard
        return redirect(url_for("dashboard.home"))

    return render_template(
        "auth/login.html"
    )


# ==========================
# INSCRIPTION
# ==========================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        user = User(
            nom=request.form["nom"],
            email=request.form["email"]
        )

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("auth.login"))

    return render_template(
        "auth/register.html" 
    )


# ==========================
# DECONNEXION
# ==========================

@auth_bp.route("/logout")
def logout():

    return redirect(
        url_for("auth.login")
    )
