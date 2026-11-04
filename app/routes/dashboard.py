from datetime import datetime, date, timedelta

from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from sqlalchemy import func

from app import db
from app.models import Produit, Client, Facture, Depense


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def home():

    # =====================================
    # FILTRE TEMPOREL
    # =====================================

    periode = request.args.get("periode", "7jours")
    date_debut_input = request.args.get("date_debut", "")
    date_fin_input = request.args.get("date_fin", "")

    aujourd_hui = datetime.utcnow().date()

    debut = aujourd_hui
    fin = aujourd_hui

    if periode == "aujourd_hui":
        debut = aujourd_hui
        fin = aujourd_hui

    elif periode == "hier":
        debut = aujourd_hui - timedelta(days=1)
        fin = debut

    elif periode == "7jours":
        debut = aujourd_hui - timedelta(days=6)
        fin = aujourd_hui

    elif periode == "30jours":
        debut = aujourd_hui - timedelta(days=29)
        fin = aujourd_hui

    elif periode == "mois":
        debut = aujourd_hui.replace(day=1)
        fin = aujourd_hui

    elif periode == "mois_precedent":
        premier_jour_mois = aujourd_hui.replace(day=1)
        fin = premier_jour_mois - timedelta(days=1)
        debut = fin.replace(day=1)

    elif periode == "annee":
        debut = aujourd_hui.replace(month=1, day=1)
        fin = aujourd_hui

    elif periode == "personnalisee":

        try:
            debut = datetime.strptime(
                date_debut_input, "%Y-%m-%d"
            ).date()

            fin = datetime.strptime(
                date_fin_input, "%Y-%m-%d"
            ).date()

            if debut > fin:
                raise ValueError

            if fin > aujourd_hui:
                raise ValueError

        except (ValueError, TypeError):
            periode = "7jours"
            debut = aujourd_hui - timedelta(days=6)
            fin = aujourd_hui

    else:
        periode = "7jours"
        debut = aujourd_hui - timedelta(days=6)
        fin = aujourd_hui

    # Bornes horaires : date de fin incluse.
    debut_datetime = datetime.combine(
        debut, datetime.min.time()
    )

    fin_datetime = datetime.combine(
        fin + timedelta(days=1),
        datetime.min.time()
    )

    # =====================================
    # KPI GLOBAUX
    # =====================================

    total_produits = Produit.query.count()
    total_clients = Client.query.count()

    # =====================================
    # KPI DE LA PERIODE
    # =====================================

    factures_periode = Facture.query.filter(
        Facture.date_facture >= debut_datetime,
        Facture.date_facture < fin_datetime
    )

    total_factures = factures_periode.count()

    total_ventes = (
        db.session.query(func.sum(Facture.total))
        .filter(
            Facture.date_facture >= debut_datetime,
            Facture.date_facture < fin_datetime
        )
        .scalar()
        or 0
    )

    total_depenses = (
        db.session.query(func.sum(Depense.montant))
        .filter(
            Depense.date_depense >= debut_datetime,
            Depense.date_depense < fin_datetime
        )
        .scalar()
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
    # EVOLUTION DES VENTES
    # =====================================

    ventes_par_jour = (
        db.session.query(
            func.date(Facture.date_facture),
            func.sum(Facture.total)
        )
        .filter(
            Facture.date_facture >= debut_datetime,
            Facture.date_facture < fin_datetime
        )
        .group_by(func.date(Facture.date_facture))
        .all()
    )

    ventes_dict = {}

    for jour, montant in ventes_par_jour:
        jour_date = date.fromisoformat(str(jour)[:10])
        ventes_dict[jour_date] = float(montant or 0)

    jours = []
    ventes = []

    nombre_jours = (fin - debut).days + 1

    if nombre_jours <= 62:

        jour_actuel = debut

        while jour_actuel <= fin:

            jours.append(jour_actuel.strftime("%d/%m"))
            ventes.append(ventes_dict.get(jour_actuel, 0))

            jour_actuel += timedelta(days=1)

    else:

        ventes_mensuelles = {}

        for jour, montant in ventes_dict.items():

            cle = jour.strftime("%Y-%m")

            ventes_mensuelles[cle] = (
                ventes_mensuelles.get(cle, 0) + montant
            )

        mois_actuel = debut.replace(day=1)

        while mois_actuel <= fin:

            cle = mois_actuel.strftime("%Y-%m")

            jours.append(mois_actuel.strftime("%b %Y"))
            ventes.append(ventes_mensuelles.get(cle, 0))

            if mois_actuel.month == 12:
                mois_actuel = mois_actuel.replace(
                    year=mois_actuel.year + 1,
                    month=1
                )
            else:
                mois_actuel = mois_actuel.replace(
                    month=mois_actuel.month + 1
                )

    # =====================================
    # DERNIERES FACTURES DE LA PERIODE
    # =====================================

    dernieres_factures = (
        factures_periode
        .order_by(Facture.date_facture.desc())
        .limit(5)
        .all()
    )

    # =====================================
    # CONSEIL BOUBA AI
    # =====================================

    if total_factures == 0:

        conseil = (
            "Aucune facture enregistrée pendant cette période. "
            "Commencez à enregistrer vos ventes pour suivre votre activité."
        )

    elif benefices < 0:

        conseil = (
            "Attention : vos dépenses dépassent vos ventes "
            "sur cette période. Examinez vos charges."
        )

    elif stock_critique > 0:

        conseil = (
            f"Vous avez {stock_critique} produit(s) en stock critique. "
            "Pensez à organiser leur réapprovisionnement."
        )

    else:

        conseil = (
            "Votre solde estimé est positif sur cette période. "
            "Continuez à suivre vos ventes et vos dépenses."
        )

    # =====================================
    # AFFICHAGE
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

        periode=periode,
        date_debut=debut.strftime("%Y-%m-%d"),
        date_fin=fin.strftime("%Y-%m-%d"),
        date_aujourd_hui=aujourd_hui.strftime("%Y-%m-%d")
    )
