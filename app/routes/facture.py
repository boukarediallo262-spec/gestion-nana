from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime

from app.models import db, Facture, Produit, Client, LigneFacture

facture_bp = Blueprint("facture", __name__)


# ==========================
# LISTE FACTURES
# ==========================

@facture_bp.route("/factures")
def liste_factures():

    factures = Facture.query.order_by(Facture.id.desc()).all()

    return render_template(
        "factures/liste.html",
        factures=factures
    )


# ==========================
# CREER FACTURE (PAGE)
# ==========================

@facture_bp.route("/factures/ajouter", methods=["GET", "POST"])
def ajouter_facture():

    clients = Client.query.all()
    produits = Produit.query.all()

    if request.method == "POST":

        client_id = request.form["client_id"]
        paiement = request.form["paiement"]

        facture = Facture(
            client_id=client_id,
            paiement=paiement,
            date_facture=datetime.utcnow(),
            total=0
        )

        db.session.add(facture)
        db.session.commit()

        return redirect(url_for("facture.voir_facture", id=facture.id))

    return render_template(
        "factures/ajouter.html",
        clients=clients,
        produits=produits
    )


# ==========================
# AJOUTER PRODUIT FACTURE
# ==========================

@facture_bp.route("/factures/<int:id>/ajouter_produit", methods=["POST"])
def ajouter_produit_facture(id):

    facture = Facture.query.get_or_404(id)

    produit_id = request.form["produit_id"]
    quantite = int(request.form["quantite"])

    produit = Produit.query.get(produit_id)

    ligne = LigneFacture(
        facture_id=facture.id,
        produit_id=produit.id,
        quantite=quantite,
        prix=produit.prix,
        total=produit.prix * quantite
    )

    db.session.add(ligne)

    # recalcul total facture
    facture.calculer_total()

    db.session.commit()

    return redirect(url_for("facture.voir_facture", id=facture.id))


# ==========================
# VOIR FACTURE
# ==========================

@facture_bp.route("/factures/<int:id>")
def voir_facture(id):

    facture = Facture.query.get_or_404(id)

    lignes = LigneFacture.query.filter_by(
        facture_id=facture.id
    ).all()

    return render_template(
        "voir_facture.html",
        facture=facture,
        lignes=lignes
    )


# ==========================
# SUPPRIMER FACTURE
# ==========================

@facture_bp.route("/factures/supprimer/<int:id>")
def supprimer_facture(id):

    facture = Facture.query.get_or_404(id)

    db.session.delete(facture)
    db.session.commit()

    return redirect(url_for("facture.liste_factures"))
