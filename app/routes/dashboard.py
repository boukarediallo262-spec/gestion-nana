from flask import Blueprint, render_template
from sqlalchemy import func
from datetime import datetime, timedelta

from app.models import db, Produit, Client, Facture, Depense

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def home():

    # ==========================
    # KPI PRINCIPAUX
    # ==========================

    total_produits = Produit.query.count()
    total_clients = Client.query.count()
    total_factures = Facture.query.count()

    total_ventes = db.session.query(func.sum(Facture.total)).scalar() or 0
    total_depenses = db.session.query(func.sum(Depense.montant)).scalar() or 0

    benefices = total_ventes - total_depenses

    # ==========================
    # STOCK CRITIQUE
    # ==========================

    stock_critique = Produit.query.filter(
        Produit.quantite <= Produit.stock_minimum
    ).count()

    produits_rupture = Produit.query.filter(
        Produit.quantite <= Produit.stock_minimum
    ).limit(5).all()

    # ==========================
    # VENTES 7 JOURS
    # ==========================

    jours = []
    ventes = []

    for i in range(6, -1, -1):

        jour = datetime.now().date() - timedelta(days=i)

        total = db.session.query(
            func.sum(Facture.total)
        ).filter(
            func.date(Facture.date_facture) == jour
        ).scalar() or 0

        jours.append(jour.strftime("%d/%m"))
        ventes.append(total)

    # ==========================
    # CONSEIL IA SIMPLE
    # ==========================

    if benefices < 0:
        conseil = "⚠ Attention : vos dépenses dépassent vos ventes"
    elif stock_critique > 0:
        conseil = "📦 Stock faible détecté, pensez à réapprovisionner"
    else:
        conseil = "✅ Votre activité est stable"

    # ==========================
    # RENDER
    # ==========================

    return render_template(
        "dashboard/index.html",

        total_produits=total_produits,
        total_clients=total_clients,
        total_factures=total_factures,

        total_ventes=total_ventes,
        total_depenses=total_depenses,
        benefices=benefices,

        stock_critique=stock_critique,
        produits_rupture=produits_rupture,

        jours=jours,
        ventes=ventes,

        conseil=conseil
    )
