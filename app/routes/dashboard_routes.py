from flask import Blueprint, render_template
from app.models.models import Produit, Facture, Depense

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def home():

    total_produits = Produit.query.count()
    total_factures = Facture.query.count()

    depenses = Depense.query.all()

    total_depenses = 0

    for d in depenses:
        total_depenses += d.montant

    abonnement = "Actif"

    return render_template(
        "dashboard/index.html",
        total_produits=total_produits,
        total_factures=total_factures,
        total_depenses=total_depenses,
        abonnement=abonnement
    )
