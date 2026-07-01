from flask import render_template
from app.models.models import Facture, Depense

@dashboard_bp.route("/statistiques")
def statistiques():

    # Total ventes
    ventes = Facture.query.all()
    total_ventes = sum([f.total for f in ventes if f.total])

    # Dépenses
    depenses = Depense.query.all()
    total_depenses = sum([d.montant for d in depenses if d.montant])

    # Factures
    total_factures = Facture.query.count()

    # Bénéfices
    benefices = total_ventes - total_depenses

    return render_template(
        "statistiques.html",
        total_ventes=total_ventes,
        total_depenses=total_depenses,
        total_factures=total_factures,
        benefices=benefices
    )
