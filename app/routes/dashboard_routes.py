from sqlalchemy import func
from datetime import datetime, date
from app.models.models import Facture, Depense, Produit, LigneFacture

@dashboard_bp.route("/statistiques")
def statistiques():

    # =========================
    # VENTES / FINANCES
    # =========================

    factures = Facture.query.all()
    depenses = Depense.query.all()

    total_ventes = sum(f.total or 0 for f in factures)
    total_depenses = sum(d.montant or 0 for d in depenses)
    total_factures = Facture.query.count()
    benefices = total_ventes - total_depenses

    # =========================
    # PRODUITS
    # =========================

    top_produits = (
        db.session.query(
            Produit.nom,
            func.sum(LigneFacture.quantite).label("total_vendu")
        )
        .join(LigneFacture, LigneFacture.produit_id == Produit.id)
        .group_by(Produit.id)
        .order_by(func.sum(LigneFacture.quantite).desc())
        .limit(5)
        .all()
    )

    produits_rupture = Produit.query.filter(Produit.quantite <= 0).all()

    produits_alerte = Produit.query.filter(
        Produit.quantite > 0,
        Produit.quantite <= 5
    ).all()

    # =========================
    # TEMPS
    # =========================

    today = date.today()

    ventes_jour = Facture.query.filter(
        Facture.date_facture >= today
    ).all()

    total_jour = sum(f.total or 0 for f in ventes_jour)

    mois_actuel = datetime.now().month

    ventes_mois = Facture.query.filter(
        func.strftime('%m', Facture.date_facture) == f"{mois_actuel:02d}"
    ).all()

    total_mois = sum(f.total or 0 for f in ventes_mois)

    # =========================
    # RETURN
    # =========================

    return render_template(
        "statistiques.html",

        # finances
        total_ventes=total_ventes,
        total_depenses=total_depenses,
        total_factures=total_factures,
        benefices=benefices,

        # produits
        top_produits=top_produits,
        produits_rupture=produits_rupture,
        produits_alerte=produits_alerte,

        # temps
        total_jour=total_jour,
        total_mois=total_mois
    )
