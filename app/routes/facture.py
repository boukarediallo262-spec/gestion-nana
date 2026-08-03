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
    Facture,
    Produit,
    Client,
    LigneFacture,
)

from app.utils.abonnement import (
    abonnement_requis,
)


# ==========================================================
# BLUEPRINT
# ==========================================================

facture_bp = Blueprint(
    "facture",
    __name__,
    url_prefix="/factures",
)


# ==========================================================
# LISTE DES FACTURES
# ==========================================================

@facture_bp.route("/")
@login_required
@abonnement_requis
def index():

    recherche = request.args.get(
        "q",
        ""
    ).strip()

    factures = Facture.query

    if recherche:

        factures = (
            factures
            .join(Client)
            .filter(

                or_(

                    Client.nom.ilike(
                        f"%{recherche}%"
                    ),

                    Client.prenom.ilike(
                        f"%{recherche}%"
                    ),

                    Client.telephone.ilike(
                        f"%{recherche}%"
                    )

                )

            )
        )

    factures = (
        factures
        .order_by(
            Facture.date_facture.desc()
        )
        .all()
    )

    return render_template(

        "factures/index.html",

        factures=factures,

        recherche=recherche,

    )


# ==========================================================
# DETAIL D'UNE FACTURE
# ==========================================================

@facture_bp.route("/detail/<int:id>")
@login_required
@abonnement_requis
def detail(id):

    facture = db.session.get(
        Facture,
        id
    )

    if facture is None:

        flash(
            "Facture introuvable.",
            "danger"
        )

        return redirect(
            url_for(
                "facture.index"
            )
        )

    lignes = (
        LigneFacture.query
        .filter_by(
            facture_id=id
        )
        .all()
    )

    return render_template(

        "factures/detail.html",

        facture=facture,

        lignes=lignes,

    )

# ==========================================================
# AJOUTER UNE FACTURE
# ==========================================================

@facture_bp.route("/ajouter", methods=["GET", "POST"])
@login_required
@abonnement_requis
def ajouter():

    clients = (
        Client.query
        .order_by(Client.nom.asc())
        .all()
    )

    produits = (
        Produit.query
        .filter_by(actif=True)
        .order_by(Produit.nom.asc())
        .all()
    )

    if request.method == "POST":

        client_id = request.form.get("client_id")

        paiement = request.form.get(
            "paiement",
            "Espèces"
        )

        facture = Facture(

            client_id=client_id,

            paiement=paiement,

            total=0,

        )

        db.session.add(facture)
        db.session.commit()

        flash(
            "Facture créée avec succès.",
            "success"
        )

        return redirect(
            url_for(
                "facture.modifier",
                id=facture.id
            )
        )

    return render_template(

        "factures/ajouter.html",

        clients=clients,

        produits=produits,

    )


# ==========================================================
# AJOUTER UNE LIGNE DE FACTURE
# ==========================================================

@facture_bp.route(
    "/<int:id>/ajouter-produit",
    methods=["POST"]
)
@login_required
@abonnement_requis
def ajouter_produit(id):

    facture = db.session.get(
        Facture,
        id
    )

    if facture is None:

        flash(
            "Facture introuvable.",
            "danger"
        )

        return redirect(
            url_for("facture.index")
        )

    produit = db.session.get(

        Produit,

        request.form.get("produit_id")

    )

    if produit is None:

        flash(
            "Produit introuvable.",
            "danger"
        )

        return redirect(
            url_for(
                "facture.modifier",
                id=id
            )
        )

    quantite = int(
        request.form.get(
            "quantite",
            1
        )
    )

    # =====================================
    # Vérification du stock
    # =====================================

    if quantite <= 0:

        flash(
            "Quantité invalide.",
            "warning"
        )

        return redirect(
            url_for(
                "facture.modifier",
                id=id
            )
        )

    if produit.quantite < quantite:

        flash(
            f"Stock insuffisant pour {produit.nom}.",
            "danger"
        )

        return redirect(
            url_for(
                "facture.modifier",
                id=id
            )
        )

    # =====================================
    # Création ligne facture
    # =====================================

    ligne = LigneFacture(

        facture_id=facture.id,

        produit_id=produit.id,

        quantite=quantite,

        prix=produit.prix,

        total=produit.prix * quantite,

    )

    db.session.add(ligne)

    # =====================================
    # Déduction du stock
    # =====================================

    produit.quantite -= quantite

    # =====================================
    # Recalcul facture
    # =====================================

    facture.total = sum(

        l.total

        for l in facture.lignes_facture

    ) + ligne.total

    db.session.commit()

    flash(
        "Produit ajouté à la facture.",
        "success"
    )

    return redirect(
        url_for(
            "facture.modifier",
            id=id
        )
    )

# ==========================================================
# MODIFIER UNE FACTURE
# ==========================================================

@facture_bp.route("/modifier/<int:id>", methods=["GET", "POST"])
@login_required
@abonnement_requis
def modifier(id):

    facture = db.session.get(
        Facture,
        id
    )

    if facture is None:

        flash(
            "Facture introuvable.",
            "danger"
        )

        return redirect(
            url_for("facture.index")
        )

    clients = (
        Client.query
        .order_by(Client.nom.asc())
        .all()
    )

    produits = (
        Produit.query
        .filter_by(actif=True)
        .order_by(Produit.nom.asc())
        .all()
    )

    lignes = (
        LigneFacture.query
        .filter_by(
            facture_id=id
        )
        .all()
    )

    if request.method == "POST":

        facture.client_id = request.form.get(
            "client_id"
        )

        facture.paiement = request.form.get(
            "paiement"
        )

        db.session.commit()

        flash(
            "Facture modifiée avec succès.",
            "success"
        )

        return redirect(
            url_for(
                "facture.modifier",
                id=id
            )
        )

    return render_template(

        "factures/modifier.html",

        facture=facture,

        clients=clients,

        produits=produits,

        lignes=lignes,

    )


# ==========================================================
# SUPPRIMER UNE LIGNE DE FACTURE
# ==========================================================

@facture_bp.route(
    "/ligne/<int:id>/supprimer"
)
@login_required
@abonnement_requis
def supprimer_ligne(id):

    ligne = db.session.get(
        LigneFacture,
        id
    )

    if ligne is None:

        flash(
            "Ligne introuvable.",
            "danger"
        )

        return redirect(
            url_for("facture.index")
        )

    facture = ligne.facture

    produit = ligne.produit

    # ==========================
    # REMISE EN STOCK
    # ==========================

    produit.quantite += ligne.quantite

    db.session.delete(ligne)

    db.session.flush()

    facture.total = sum(

        l.total

        for l in facture.lignes_facture

    )

    db.session.commit()

    flash(
        "Produit supprimé de la facture.",
        "success"
    )

    return redirect(
        url_for(
            "facture.modifier",
            id=facture.id
        )
    )


# ==========================================================
# SUPPRIMER UNE FACTURE
# ==========================================================

@facture_bp.route(
    "/supprimer/<int:id>"
)
@login_required
@abonnement_requis
def supprimer(id):

    facture = db.session.get(
        Facture,
        id
    )

    if facture is None:

        flash(
            "Facture introuvable.",
            "danger"
        )

        return redirect(
            url_for("facture.index")
        )

    # ==========================
    # REMISE EN STOCK
    # ==========================

    for ligne in facture.lignes_facture:

        ligne.produit.quantite += ligne.quantite

    db.session.delete(facture)

    db.session.commit()

    flash(
        "Facture supprimée.",
        "success"
    )

    return redirect(
        url_for("facture.index")
    )


# ==========================================================
# RECALCUL DU TOTAL
# ==========================================================

def recalculer_total(facture):

    facture.total = sum(

        ligne.total

        for ligne in facture.lignes_facture

    )

    db.session.commit()
