from flask import Blueprint, render_template, session, redirect
from app.models.models import db, Produit, Facture, Depense, User
from sqlalchemy import func
from datetime import date

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def home():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    user = User.query.get(user_id)

    ventes = db.session.query(
        func.coalesce(func.sum(Facture.total), 0)
    ).filter_by(user_id=user_id).scalar()

    depenses = db.session.query(
        func.coalesce(func.sum(Depense.montant), 0)
    ).filter_by(user_id=user_id).scalar()

    produits = Produit.query.filter_by(user_id=user_id).count()

    factures = Facture.query.filter_by(user_id=user_id).count()

    benefice = ventes - depenses

    abonnement_actif = False
    jours_restants = 0

    if user.date_fin_abonnement:

        jours_restants = (
            user.date_fin_abonnement - date.today()
        ).days

        if jours_restants > 0:
            abonnement_actif = True

    return render_template(
        "dashboard/index.html",

        ventes=ventes,
        depenses=depenses,
        benefice=benefice,
        produits=produits,
        factures=factures,

        abonnement_actif=abonnement_actif,
        jours_restants=jours_restants
    )
