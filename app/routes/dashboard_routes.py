from sqlalchemy import func
from datetime import datetime, date, timedelta
from app.models.models import (
    db,
    Facture,
    Produit,
    Depense,
    Client,
    LigneFacture
)
#============================
@dashboard_bp.route("/")
def home():

    total_produits = Produit.query.count()

    total_clients = Client.query.count()

    total_factures = Facture.query.count()

    total_ventes = db.session.query(
        func.sum(Facture.total)
    ).scalar() or 0

    total_depenses = db.session.query(
        func.sum(Depense.montant)
    ).scalar() or 0

    benefices = total_ventes - total_depenses

    stock_faible = Produit.query.filter(
        Produit.quantite <= 5
    ).count()

    abonnement = "Premium"

    return render_template(

        "dashboard/index.html",

        total_produits=total_produits,

        total_clients=total_clients,

        total_factures=total_factures,

        total_ventes=total_ventes,

        total_depenses=total_depenses,

        benefices=benefices,

        stock_faible=stock_faible,

        abonnement=abonnement

    )
#===========================


@dashboard_bp.route("/statistiques")
def statistiques():

    # ==========================
    # Statistiques générales
    # ==========================

    total_produits = Produit.query.count()
    total_clients = Client.query.count()
    total_factures = Facture.query.count()

    total_ventes = db.session.query(
        func.sum(Facture.total)
    ).scalar() or 0

    total_depenses = db.session.query(
        func.sum(Depense.montant)
    ).scalar() or 0

    benefices = total_ventes - total_depenses

    # ==========================
    # Ventes aujourd'hui
    # ==========================

    aujourd_hui = date.today()

    ventes_jour = db.session.query(
        func.sum(Facture.total)
    ).filter(
        func.date(Facture.date_facture) == aujourd_hui
    ).scalar() or 0

    # ==========================
    # Ventes semaine
    # ==========================

    debut_semaine = aujourd_hui - timedelta(days=7)

    ventes_semaine = db.session.query(
        func.sum(Facture.total)
    ).filter(
        Facture.date_facture >= debut_semaine
    ).scalar() or 0

    # ==========================
    # Ventes mois
    # ==========================

    mois = datetime.now().month
    annee = datetime.now().year

    ventes_mois = db.session.query(
        func.sum(Facture.total)
    ).filter(
        func.extract("month", Facture.date_facture) == mois,
        func.extract("year", Facture.date_facture) == annee
    ).scalar() or 0

    # ==========================
    # Top produits
    # ==========================

    top_produits = (
        db.session.query(
            Produit.nom,
            func.sum(LigneFacture.quantite).label("quantite")
        )
        .join(LigneFacture)
        .group_by(Produit.id)
        .order_by(func.sum(LigneFacture.quantite).desc())
        .limit(5)
        .all()
    )

    # ==========================
    # Alertes stock
    # ==========================

    stock_faible = Produit.query.filter(
        Produit.quantite <= 5
    ).all()

    return render_template(
        "statistiques.html",

        total_produits=total_produits,
        total_clients=total_clients,
        total_factures=total_factures,

        total_ventes=total_ventes,
        total_depenses=total_depenses,
        benefices=benefices,

        ventes_jour=ventes_jour,
        ventes_semaine=ventes_semaine,
        ventes_mois=ventes_mois,

        top_produits=top_produits,
        stock_faible=stock_faible
    )
