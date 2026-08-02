from datetime import datetime, timedelta

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from app.models import (
    Produit,
    Client,
    Facture,
    Depense,
)

dashboard_bp = Blueprint(
    "dashboard",
    __name__,
)


@dashboard_bp.route("/")
@login_required
def home():
    """
    Tableau de bord principal.
    """

    # =====================================
    # KPI
    # =====================================

    total_produits = Produit.query.count()

    total_clients = Client.query.count()

    total_factures = Facture.query.count()

    total_ventes = (
        db.session.query(
            func.sum(Facture.total)
        ).scalar()
        or 0
    )

    total_depenses = (
        db.session.query(
            func.sum(Depense.montant)
        ).scalar()
        or 0
    )

    benefices = total_ventes - total_depenses

    # =====================================
    # STOCK CRITIQUE
    # =====================================

    produits_rupture = Produit.query.filter(
        Produit.quantite <= Produit.stock_minimum
    ).all()

    stock_critique = len(produits_rupture)

    # =====================================
    # VENTES DES 7 DERNIERS JOURS
    # =====================================

    jours = []
    ventes = []

    aujourd_hui = datetime.utcnow().date()

    for i in range(6, -1, -1):

        jour = aujourd_hui - timedelta(days=i)

        total = (
            db.session.query(
                func.sum(Facture.total)
            )
            .filter(
                func.date(Facture.date_facture) == jour
            )
            .scalar()
            or 0
        )

        jours.append(
            jour.strftime("%d/%m")
        )

        ventes.append(float(total))

    # =====================================
    # DERNIERES FACTURES
    # =====================================

    dernieres_factures = (
        Facture.query
        .order_by(Facture.date_facture.desc())
        .limit(5)
        .all()
    )

    # =====================================
    # CONSEIL IA
    # =====================================

    if benefices < 0:

        conseil = (
            "⚠️ Vos dépenses dépassent vos ventes. "
            "Réduisez les charges ou augmentez les ventes."
        )

    elif stock_critique > 0:

        conseil = (
            f"📦 {stock_critique} produit(s) sont en stock critique."
        )

    elif total_factures == 0:

        conseil = (
            "📄 Aucune facture enregistrée."
        )

    else:

        conseil = (
            "✅ Activité stable. Continuez ainsi."
        )

    # =====================================
    # RENDU
    # =====================================

    return render_template(
        "dashboard/index.html",

        utilisateur=current_user,

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

        dernieres_factures=dernieres_factures,

        conseil=conseil,
    )
