from flask import Blueprint, render_template, request, redirect, url_for

from app.models import db, Produit, Categorie, Fournisseur
from flask_login import login_required
from app.utils.abonnement import abonnement_requis


produit_bp = Blueprint(
    "produit",
    __name__,
    url_prefix="/produits"
)

@produit_bp.route("/")
def produits():
    return "Produits OK"
    
    


# ==========================
# LISTE PRODUITS
# ==========================

@produit_bp.route("/produits")
def liste_produits():

    produits = Produit.query.order_by(Produit.id.desc()).all()

    return render_template(
        "produits/liste.html",
        produits=produits
    )


# ==========================
# AJOUT PRODUIT
# ==========================

@produit_bp.route("/produits/ajouter", methods=["GET", "POST"])
def ajouter_produit():

    categories = Categorie.query.all()
    fournisseurs = Fournisseur.query.all()

    if request.method == "POST":

        nom = request.form["nom"]
        prix = float(request.form["prix"])
        quantite = int(request.form["quantite"])
        categorie_id = request.form["categorie_id"]
        fournisseur_id = request.form["fournisseur_id"]

        produit = Produit(
            nom=nom,
            prix=prix,
            quantite=quantite,
            categorie_id=categorie_id,
            fournisseur_id=fournisseur_id
        )

        db.session.add(produit)
        db.session.commit()

        return redirect(url_for("produit.liste_produits"))

    return render_template(
        "produits/ajouter.html",
        categories=categories,
        fournisseurs=fournisseurs
    )


# ==========================
# MODIFIER PRODUIT
# ==========================

@produit_bp.route("/produits/modifier/<int:id>", methods=["GET", "POST"])
def modifier_produit(id):

    produit = Produit.query.get_or_404(id)

    categories = Categorie.query.all()
    fournisseurs = Fournisseur.query.all()

    if request.method == "POST":

        produit.nom = request.form["nom"]
        produit.prix = float(request.form["prix"])
        produit.quantite = int(request.form["quantite"])
        produit.categorie_id = request.form["categorie_id"]
        produit.fournisseur_id = request.form["fournisseur_id"]

        db.session.commit()

        return redirect(url_for("produit.liste_produits"))

    return render_template(
        "produits/modifier.html",
        produit=produit,
        categories=categories,
        fournisseurs=fournisseurs
    )


# ==========================
# SUPPRIMER PRODUIT
# ==========================

@produit_bp.route("/produits/supprimer/<int:id>")
def supprimer_produit(id):

    produit = Produit.query.get_or_404(id)

    db.session.delete(produit)
    db.session.commit()

    return redirect(url_for("produit.liste_produits"))


# ==========================
# DETAILS PRODUIT
# ==========================

@produit_bp.route("/produits/<int:id>")
def voir_produit(id):

    produit = Produit.query.get_or_404(id)

    return render_template(
        "produits/voir.html",
        produit=produit
    )
