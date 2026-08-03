from sqlalchemy import func

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from flask_login import (
    login_required,
)

from app import db

from app.models import (
    Depense,
)

from app.utils.abonnement import (
    abonnement_requis,
)


# ==========================================================
# BLUEPRINT
# ==========================================================

depense_bp = Blueprint(
    "depense",
    __name__,
    url_prefix="/depenses",
)


# ==========================================================
# LISTE DES DEPENSES
# ==========================================================

@depense_bp.route("/")
@login_required
@abonnement_requis
def index():

    recherche = request.args.get(
        "q",
        ""
    ).strip()

    query = Depense.query

    if recherche:

        query = query.filter(
            Depense.titre.ilike(f"%{recherche}%")
            |
            Depense.categorie.ilike(f"%{recherche}%")
            |
            Depense.fournisseur.ilike(f"%{recherche}%")
        )

    depenses = (
        query
        .order_by(
            Depense.date_depense.desc()
        )
        .all()
    )

    total_depenses = (
        db.session.query(
            func.sum(
                Depense.montant
            )
        ).scalar()
        or 0
    )

    return render_template(
        "depenses/index.html",

        depenses=depenses,

        total_depenses=total_depenses,

        recherche=recherche,
    )


# ==========================================================
# AJOUTER UNE DEPENSE
# ==========================================================

@depense_bp.route(
    "/ajouter",
    methods=["GET", "POST"],
)
@login_required
@abonnement_requis
def ajouter():

    if request.method == "POST":

        depense = Depense(

            titre=request.form.get(
                "titre"
            ),

            description=request.form.get(
                "description"
            ),

            categorie=request.form.get(
                "categorie"
            ),

            fournisseur=request.form.get(
                "fournisseur"
            ),

            montant=float(
                request.form.get(
                    "montant",
                    0
                )
            ),

            mode_paiement=request.form.get(
                "mode_paiement"
            ),
        )

        db.session.add(
            depense
        )

        db.session.commit()

        flash(
            "Dépense ajoutée avec succès.",
            "success",
        )

        return redirect(
            url_for(
                "depense.index"
            )
        )

    return render_template(
        "depenses/ajouter.html"
    )

# ==========================================================
# MODIFIER UNE DEPENSE
# ==========================================================

@depense_bp.route(
    "/modifier/<int:id>",
    methods=["GET", "POST"],
)
@login_required
@abonnement_requis
def modifier(id):

    depense = db.session.get(
        Depense,
        id
    )

    if depense is None:

        flash(
            "Cette dépense est introuvable.",
            "danger",
        )

        return redirect(
            url_for(
                "depense.index"
            )
        )

    if request.method == "POST":

        depense.titre = request.form.get(
            "titre"
        )

        depense.description = request.form.get(
            "description"
        )

        depense.categorie = request.form.get(
            "categorie"
        )

        depense.fournisseur = request.form.get(
            "fournisseur"
        )

        depense.mode_paiement = request.form.get(
            "mode_paiement"
        )

        depense.montant = float(
            request.form.get(
                "montant",
                0
            )
        )

        db.session.commit()

        flash(
            "La dépense a été modifiée avec succès.",
            "success",
        )

        return redirect(
            url_for(
                "depense.index"
            )
        )

    return render_template(
        "depenses/modifier.html",
        depense=depense,
    )


# ==========================================================
# DETAIL D'UNE DEPENSE
# ==========================================================

@depense_bp.route(
    "/detail/<int:id>"
)
@login_required
@abonnement_requis
def detail(id):

    depense = db.session.get(
        Depense,
        id
    )

    if depense is None:

        flash(
            "Cette dépense est introuvable.",
            "danger",
        )

        return redirect(
            url_for(
                "depense.index"
            )
        )

    return render_template(
        "depenses/detail.html",
        depense=depense,
    )

# ==========================================================
# SUPPRIMER UNE DEPENSE
# ==========================================================

@depense_bp.route(
    "/supprimer/<int:id>",
    methods=["POST"]
)
@login_required
@abonnement_requis
def supprimer(id):

    depense = db.session.get(
        Depense,
        id
    )

    if depense is None:

        flash(
            "Cette dépense est introuvable.",
            "danger",
        )

        return redirect(
            url_for(
                "depense.index"
            )
        )

    try:

        db.session.delete(
            depense
        )

        db.session.commit()

        flash(
            "La dépense a été supprimée avec succès.",
            "success",
        )

    except Exception:

        db.session.rollback()

        flash(
            "Impossible de supprimer cette dépense.",
            "danger",
        )

    return redirect(
        url_for(
            "depense.index"
        )
    )
