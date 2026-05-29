from flask import Blueprint, render_template, request, redirect
from app.models.models import (
    db,
    Produit,
    Facture,
    Depense,
    LigneFacture
)

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def home():

    total_produits = Produit.query.count()
    total_factures = Facture.query.count()

    depenses = Depense.query.all()

    total_depenses = sum([d.montant for d in depenses])

    produits = Produit.query.limit(5).all()

    abonnement = "Actif"

    ventes_data = Facture.query.all()

    total_ventes = sum([f.total for f in ventes_data])

    depenses_data = Depense.query.all()

    total_depenses_graph = sum([d.montant for d in depenses_data])

    benefices = total_ventes - total_depenses_graph

    return render_template(
        "dashboard/index.html",
        total_produits=total_produits,
        total_factures=total_factures,
        total_depenses=total_depenses,
        abonnement=abonnement,
        produits=produits,
        total_ventes=total_ventes,
        benefices=benefices
    )

@dashboard_bp.route("/produits", methods=["GET", "POST"])
def produits():

    if request.method == "POST":

        nom = request.form.get("nom")
        prix = request.form.get("prix")
        quantite = request.form.get("quantite")

        produit_existant = Produit.query.filter_by(nom=nom).first()

        if produit_existant:

            produit_existant.quantite += int(quantite)

        else:

            nouveau_produit = Produit(
                nom=nom,
                prix=prix,
                quantite=quantite
            )

            db.session.add(nouveau_produit)

        db.session.commit()
        return redirect("/produits")

    produits = Produit.query.all()

    return render_template(
        "produits.html",
        produits=produits
    )

# =========================
# FACTURES
# =========================

@dashboard_bp.route("/factures")
def factures():

    toutes_factures = Facture.query.all()

    return render_template(
        "factures.html",
        factures=toutes_factures
    )


@dashboard_bp.route("/ajouter_facture", methods=["GET", "POST"])
def ajouter_facture():

    produits = Produit.query.all()

    if request.method == "POST":

        client = request.form.get("client")

        mode_paiement = request.form.get("mode_paiement")

        total = 0

        nouvelle_facture = Facture(
            client=client,
            total=0,
            mode_paiement=mode_paiement
        )

        db.session.add(nouvelle_facture)
        db.session.commit()

        for produit in produits:

            quantite = request.form.get(f"quantite_{produit.id}")

            if quantite and int(quantite) > 0:

                quantite = int(quantite)

                # DIMINUTION STOCK
                produit.quantite -= quantite

                montant = produit.prix * quantite

                total += montant

                ligne = LigneFacture(
                    facture_id=nouvelle_facture.id,
                    produit_id=produit.id,
                    quantite=quantite,
                    prix=produit.prix
                )

                db.session.add(ligne)

        nouvelle_facture.total = total

        db.session.commit()

        return redirect("/factures")

    return render_template(
        "ajouter_facture.html",
        produits=produits
    )

@dashboard_bp.route("/supprimer_facture/<int:id>")
def supprimer_facture(id):

    facture = Facture.query.get(id)

    if facture:

        db.session.delete(facture)
        db.session.commit()

    return redirect("/factures")
