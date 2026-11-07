
from flask import Blueprint, render_template
from flask_login import login_required

from app import db
from app.models import Produit
from app.utils.abonnement import abonnement_requis


# ==========================================
# BLUEPRINT STOCK
# ==========================================

stock_bp = Blueprint("stock", __name__)


# ==========================================
# PAGE PRINCIPALE DU STOCK
# ==========================================

@stock_bp.route("/stock", methods=["GET"])
@login_required
@abonnement_requis
def stock():

    produits = (
        Produit.query
        .filter_by(actif=True)
        .order_by(Produit.nom.asc())
        .all()
    )

    total_produits = len(produits)

    total_stock = sum(
        produit.quantite for produit in produits
    )

    produits_disponibles = sum(
        1 for produit in produits
        if produit.quantite > 0
    )

    produits_en_alerte = sum(
        1 for produit in produits
        if produit.stock_faible
    )

    valeur_stock = sum(
        produit.valeur_achat_stock for produit in produits
    )

    return render_template(
        "stock.html",
        produits=produits,
        total_produits=total_produits,
        total_stock=total_stock,
        produits_disponibles=produits_disponibles,
        produits_en_alerte=produits_en_alerte,
        valeur_stock=valeur_stock
    )
