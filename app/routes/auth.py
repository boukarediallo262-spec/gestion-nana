from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from app import db
from app.models import User


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


# =====================================================
# CONNEXION
# =====================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.mot_de_passe,
            password
        ):

            login_user(user)

            flash(
                "Connexion réussie.",
                "success"
            )

            return redirect(
                url_for("dashboard.home")
            )

        flash(
            "Email ou mot de passe incorrect.",
            "danger"
        )

    return render_template(
        "auth/login.html"
    )


# =====================================================
# DECONNEXION
# =====================================================

@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "Vous êtes déconnecté.",
        "info"
    )

    return redirect(
        url_for("auth.login")
    )


# =====================================================
# INSCRIPTION
# =====================================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        email = request.form.get("email")

        existe = User.query.filter_by(
            email=email
        ).first()

        if existe:

            flash(
                "Cet email existe déjà.",
                "warning"
            )

            return redirect(
                url_for("auth.register")
            )

        utilisateur = User(

            nom=request.form.get("nom"),

            prenom=request.form.get("prenom"),

            email=email,

            telephone=request.form.get("telephone"),

            role="utilisateur",

            mot_de_passe=generate_password_hash(
                request.form.get("password")
            )

        )

        db.session.add(utilisateur)
        db.session.commit()

        flash(
            "Compte créé avec succès.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/register.html"
    )
