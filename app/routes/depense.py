from flask import Blueprint, render_template, request, redirect, url_for

from app import db
from app.models import Depense

from flask_login import login_required
from app.utils.abonnement import abonnement_requis

@depense_bp.route("/")
@login_required
@abonnement_requis
def depenses():
    ...

depense_bp = Blueprint("depense", __name__)


# ==========================================
# LISTE DES DEPENSES
# ==========================================

@depense_bp.route("/depenses")
def liste_depenses():

    depenses = Depense.query.order_by(
        Depense.date_depense.desc()
    ).all()

    total_depenses = sum(
        d.montant for d in depenses
    )

    return render_template(
        "depenses/liste.html",
        depenses=depenses,
        total_depenses=total_depenses
    )


# ==========================================
# AJOUTER UNE DEPENSE
# ==========================================

@depense_bp.route("/depenses/ajouter", methods=["GET", "POST"])
def ajouter_depense():

    if request.method == "POST":

        depense = Depense(

            titre=request.form["titre"],

            description=request.form.get(
                "description"
            ),

            montant=float(
                request.form["montant"]
            ),

            categorie=request.form.get(
                "categorie"
            ),

            mode_paiement=request.form.get(
                "mode_paiement"
            ),

            fournisseur=request.form.get(
                "fournisseur"
            )

        )

        db.session.add(depense)
        db.session.commit()

        return redirect(
            url_for("depense.liste_depenses")
        )

    return render_template(
        "depenses/ajouter.html"
    )


# ==========================================
# MODIFIER
# ==========================================

@depense_bp.route(
    "/depenses/modifier/<int:id>",
    methods=["GET", "POST"]
)
def modifier_depense(id):

    depense = Depense.query.get_or_404(id)

    if request.method == "POST":

        depense.titre = request.form["titre"]

        depense.description = request.form.get(
            "description"
        )

        depense.montant = float(
            request.form["montant"]
        )

        depense.categorie = request.form.get(
            "categorie"
        )

        depense.mode_paiement = request.form.get(
            "mode_paiement"
        )

        depense.fournisseur = request.form.get(
            "fournisseur"
        )

        db.session.commit()

        return redirect(
            url_for("depense.liste_depenses")
        )

    return render_template(
        "depenses/modifier.html",
        depense=depense
    )


# ==========================================
# DETAIL DEPENSE
# ==========================================

@depense_bp.route("/depenses/<int:id>")
def voir_depense(id):

    depense = Depense.query.get_or_404(id)

    return render_template(
        "depenses/voir.html",
        depense=depense
    )


# ==========================================
# SUPPRIMER
# ==========================================

@depense_bp.route("/depenses/supprimer/<int:id>")
def supprimer_depense(id):

    depense = Depense.query.get_or_404(id)

    db.session.delete(depense)

    db.session.commit()

    return redirect(
        url_for("depense.liste_depenses")
    )
