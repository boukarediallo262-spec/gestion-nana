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

from sqlalchemy import or_

from app import db

from app.models import (
    Produit,
    Categorie,
    Fournisseur,
)

from app.utils.abonnement import abonnement_requis


# ==========================================================
# BLUEPRINT
# ==========================================================

produit_bp = Blueprint(
    "produit",
    __name__,
    url_prefix="/produits",
)


# ==========================================================
# LISTE DES PRODUITS
# ==========================================================

@produit_bp.route("/")
@login_required
@abonnement_requis
def index():

    recherche = request.args.get(
        "q",
        ""
    ).strip()

    categorie = request.args.get(
        "categorie",
        type=int
    )

    fournisseur = request.args.get(
        "fournisseur",
        type=int
    )

    produits = Produit.query

    # ----------------------------------
    # Recherche
    # ----------------------------------

    if recherche:

        produits = produits.filter(

            or_(

                Produit.nom.ilike(
                    f"%{recherche}%"
                ),

                Produit.reference.ilike(
                    f"%{recherche}%"
                ),

                Produit.code_barre.ilike(
                    f"%{recherche}%"
                )

            )

        )

    # ----------------------------------
    # Catégorie
    # ----------------------------------

    if categorie:

        produits = produits.filter(
            Produit.categorie_id == categorie
        )

    # ----------------------------------
    # Fournisseur
    # ----------------------------------

    if fournisseur:

        produits = produits.filter(
            Produit.fournisseur_id == fournisseur
        )

    produits = produits.order_by(
        Produit.nom.asc()
    ).all()

    return render_template(

        "produits/index.html",

        produits=produits,

        categories=Categorie.query.order_by(
            Categorie.nom.asc()
        ).all(),

        fournisseurs=Fournisseur.query.order_by(
            Fournisseur.nom.asc()
        ).all(),

        recherche=recherche,

        categorie_selectionnee=categorie,

        fournisseur_selectionne=fournisseur,

    )


# ==========================================================
# DETAIL D'UN PRODUIT
# ==========================================================

@produit_bp.route("/detail/<int:id>")
@login_required
@abonnement_requis
def detail(id):

    produit = db.session.get(
        Produit,
        id
    )

    if produit is None:

        flash(
            "Produit introuvable.",
            "danger"
        )

        return redirect(
            url_for(
                "produit.index"
            )
        )

    return render_template(

        "produits/detail.html",

        produit=produit,

    )
    # ==========================================================
# AJOUTER UN PRODUIT
# ==========================================================

@produit_bp.route("/ajouter", methods=["GET", "POST"])
@login_required
@abonnement_requis
def ajouter():

    categories = (
        Categorie.query
        .order_by(Categorie.nom.asc())
        .all()
    )

    fournisseurs = (
        Fournisseur.query
        .order_by(Fournisseur.nom.asc())
        .all()
    )

    if request.method == "POST":

        produit = Produit(

            nom=request.form.get("nom"),

            description=request.form.get("description"),

            reference=request.form.get("reference"),

            code_barre=request.form.get("code_barre"),

            image=request.form.get("image"),

            categorie_id=request.form.get(
                "categorie_id",
                type=int
            ),

            fournisseur_id=request.form.get(
                "fournisseur_id",
                type=int
            ),

            prix_achat=request.form.get(
                "prix_achat",
                type=float
            ) or 0,

            prix=request.form.get(
                "prix",
                type=float
            ) or 0,

            tva=request.form.get(
                "tva",
                type=float
            ) or 0,

            quantite=request.form.get(
                "quantite",
                type=int
            ) or 0,

            stock_minimum=request.form.get(
                "stock_minimum",
                type=int
            ) or 5,

            unite=request.form.get(
                "unite"
            ) or "Pièce",

            actif=True

        )

        db.session.add(produit)
        db.session.commit()

        flash(
            "Produit ajouté avec succès.",
            "success"
        )

        return redirect(
            url_for("produit.index")
        )

    return render_template(

        "produits/ajouter.html",

        categories=categories,

        fournisseurs=fournisseurs,

    )


# ==========================================================
# MODIFIER UN PRODUIT
# ==========================================================

@produit_bp.route("/modifier/<int:id>", methods=["GET", "POST"])
@login_required
@abonnement_requis
def modifier(id):

    produit = db.session.get(
        Produit,
        id
    )

    if produit is None:

        flash(
            "Produit introuvable.",
            "danger"
        )

        return redirect(
            url_for("produit.index")
        )

    categories = (
        Categorie.query
        .order_by(Categorie.nom.asc())
        .all()
    )

    fournisseurs = (
        Fournisseur.query
        .order_by(Fournisseur.nom.asc())
        .all()
    )

    if request.method == "POST":

        produit.nom = request.form.get("nom")

        produit.description = request.form.get(
            "description"
        )

        produit.reference = request.form.get(
            "reference"
        )

        produit.code_barre = request.form.get(
            "code_barre"
        )

        produit.image = request.form.get(
            "image"
        )

        produit.categorie_id = request.form.get(
            "categorie_id",
            type=int
        )

        produit.fournisseur_id = request.form.get(
            "fournisseur_id",
            type=int
        )

        produit.prix_achat = request.form.get(
            "prix_achat",
            type=float
        ) or 0

        produit.prix = request.form.get(
            "prix",
            type=float
        ) or 0

        produit.tva = request.form.get(
            "tva",
            type=float
        ) or 0

        produit.quantite = request.form.get(
            "quantite",
            type=int
        ) or 0

        produit.stock_minimum = request.form.get(
            "stock_minimum",
            type=int
        ) or 5

        produit.unite = request.form.get(
            "unite"
        ) or "Pièce"

        produit.actif = (
            request.form.get("actif") == "on"
        )

        db.session.commit()

        flash(
            "Produit modifié avec succès.",
            "success"
        )

        return redirect(
            url_for("produit.index")
        )

    return render_template(

        "produits/modifier.html",

        produit=produit,

        categories=categories,

        fournisseurs=fournisseurs,

    )
   # ==========================================================
# SUPPRIMER UN PRODUIT
# ==========================================================

@produit_bp.route("/supprimer/<int:id>", methods=["POST"])
@login_required
@abonnement_requis
def supprimer(id):

    produit = db.session.get(
        Produit,
        id
    )

    if produit is None:

        flash(
            "Produit introuvable.",
            "danger"
        )

        return redirect(
            url_for("produit.index")
        )

    try:

        db.session.delete(produit)

        db.session.commit()

        flash(
            "Produit supprimé avec succès.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "Impossible de supprimer ce produit.",
            "danger"
        )

    return redirect(
        url_for("produit.index")
    )


# ==========================================================
# ACTIVER / DÉSACTIVER
# ==========================================================

@produit_bp.route("/actif/<int:id>")
@login_required
@abonnement_requis
def actif(id):

    produit = db.session.get(
        Produit,
        id
    )

    if produit is None:

        flash(
            "Produit introuvable.",
            "danger"
        )

        return redirect(
            url_for("produit.index")
        )

    produit.actif = not produit.actif

    db.session.commit()

    if produit.actif:

        flash(
            "Produit activé.",
            "success"
        )

    else:

        flash(
            "Produit désactivé.",
            "warning"
        )

    return redirect(
        url_for("produit.index")
    ) 
