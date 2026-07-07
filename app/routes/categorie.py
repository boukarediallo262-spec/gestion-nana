from flask import Blueprint, render_template, request, redirect, url_for

from app import db
from app.models import Categorie

categorie_bp = Blueprint("categorie", __name__)


# ==========================================
# LISTE DES CATEGORIES
# ==========================================

@categorie_bp.route("/categories")
def liste_categories():

    categories = Categorie.query.order_by(
        Categorie.id.desc()
    ).all()

    return render_template(
        "categories/liste.html",
        categories=categories
    )


# ==========================================
# AJOUTER UNE CATEGORIE
# ==========================================

@categorie_bp.route("/categories/ajouter", methods=["GET", "POST"])
def ajouter_categorie():

    if request.method == "POST":

        categorie = Categorie(

            nom=request.form["nom"],

            description=request.form.get("description")

        )

        db.session.add(categorie)
        db.session.commit()

        return redirect(
            url_for("categorie.liste_categories")
        )

    return render_template(
        "categories/ajouter.html"
    )


# ==========================================
# MODIFIER
# ==========================================

@categorie_bp.route(
    "/categories/modifier/<int:id>",
    methods=["GET", "POST"]
)
def modifier_categorie(id):

    categorie = Categorie.query.get_or_404(id)

    if request.method == "POST":

        categorie.nom = request.form["nom"]

        categorie.description = request.form.get(
            "description"
        )

        db.session.commit()

        return redirect(
            url_for("categorie.liste_categories")
        )

    return render_template(
        "categories/modifier.html",
        categorie=categorie
    )


# ==========================================
# DETAIL
# ==========================================

@categorie_bp.route("/categories/<int:id>")
def voir_categorie(id):

    categorie = Categorie.query.get_or_404(id)

    return render_template(
        "categories/voir.html",
        categorie=categorie
    )


# ==========================================
# SUPPRIMER
# ==========================================

@categorie_bp.route("/categories/supprimer/<int:id>")
def supprimer_categorie(id):

    categorie = Categorie.query.get_or_404(id)

    db.session.delete(categorie)
    db.session.commit()

    return redirect(
        url_for("categorie.liste_categories")
    )
