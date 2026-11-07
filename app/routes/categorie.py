
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from app import db
from app.models import Categorie, Produit

categorie_bp = Blueprint("categorie", __name__)


@categorie_bp.route("/categories")
@login_required
def liste_categories():
    categories = Categorie.query.order_by(Categorie.id.desc()).all()

    return render_template(
        "categories/liste.html",
        categories=categories
    )


@categorie_bp.route("/categories/ajouter", methods=["GET", "POST"])
@login_required
def ajouter_categorie():
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()

        if not nom:
            flash("Le nom de la catégorie est obligatoire.", "danger")
            return redirect(url_for("categorie.ajouter_categorie"))

        existante = Categorie.query.filter(
            db.func.lower(Categorie.nom) == nom.lower()
        ).first()

        if existante:
            flash("Cette catégorie existe déjà.", "warning")
            return redirect(url_for("categorie.ajouter_categorie"))

        categorie = Categorie(
            nom=nom,
            description=request.form.get("description", "").strip()
        )

        db.session.add(categorie)
        db.session.commit()

        flash("Catégorie ajoutée avec succès.", "success")

        return redirect(
            url_for("produit.index")
        )

    return render_template("categories/ajouter.html")


@categorie_bp.route("/categories/modifier/<int:id>", methods=["GET", "POST"])
@login_required
def modifier_categorie(id):
    categorie = Categorie.query.get_or_404(id)

    if request.method == "POST":
        nom = request.form.get("nom", "").strip()

        if not nom:
            flash("Le nom de la catégorie est obligatoire.", "danger")
            return redirect(url_for("categorie.modifier_categorie", id=id))

        existante = Categorie.query.filter(
            db.func.lower(Categorie.nom) == nom.lower(),
            Categorie.id != id
        ).first()

        if existante:
            flash("Une autre catégorie porte déjà ce nom.", "warning")
            return redirect(url_for("categorie.modifier_categorie", id=id))

        categorie.nom = nom
        categorie.description = request.form.get("description", "").strip()

        db.session.commit()

        flash("Catégorie modifiée avec succès.", "success")
        return redirect(url_for("categorie.liste_categories"))

    return render_template(
        "categories/modifier.html",
        categorie=categorie
    )


@categorie_bp.route("/categories/<int:id>")
@login_required
def voir_categorie(id):
    categorie = Categorie.query.get_or_404(id)

    return render_template(
        "categories/voir.html",
        categorie=categorie
    )


@categorie_bp.route("/categories/supprimer/<int:id>", methods=["POST"])
@login_required
def supprimer_categorie(id):
    categorie = Categorie.query.get_or_404(id)

    if Produit.query.filter_by(categorie_id=id).first():
        flash(
            "Impossible de supprimer cette catégorie : elle est utilisée par des produits.",
            "danger"
        )
        return redirect(url_for("categorie.liste_categories"))

    db.session.delete(categorie)
    db.session.commit()

    flash("Catégorie supprimée avec succès.", "success")
    return redirect(url_for("categorie.liste_categories"))
