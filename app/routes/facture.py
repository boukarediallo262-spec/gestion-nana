
import secrets
from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_required
from sqlalchemy import or_

from app import db
from app.models import Facture, Produit, Client, LigneFacture
from app.utils.abonnement import abonnement_requis


facture_bp = Blueprint(
    "facture",
    __name__,
    url_prefix="/factures",
)


# ==========================================================
# OUTILS
# ==========================================================

def generer_reference():
    """Génère une référence de facture unique."""
    return (
        f"FAC-{datetime.utcnow().strftime('%Y%m%d')}-"
        f"{secrets.token_hex(4).upper()}"
    )


def recalculer_total(facture):
    """Recalcule le montant total de la facture."""
    facture.total = sum(
        ligne.total for ligne in facture.lignes
    )
    return facture.total


def charger_formulaire():
    clients = Client.query.order_by(Client.nom.asc()).all()

    produits = (
        Produit.query
        .filter_by(actif=True)
        .order_by(Produit.nom.asc())
        .all()
    )

    return clients, produits


# ==========================================================
# LISTE DES FACTURES
# ==========================================================

@facture_bp.route("/")
@login_required
@abonnement_requis
def index():

    recherche = request.args.get("q", "").strip()

    factures = Facture.query

    if recherche:
        factures = (
            factures
            .join(Client)
            .filter(
                or_(
                    Client.nom.ilike(f"%{recherche}%"),
                    Client.prenom.ilike(f"%{recherche}%"),
                    Client.telephone.ilike(f"%{recherche}%"),
                    Facture.reference.ilike(f"%{recherche}%"),
                )
            )
        )

    factures = (
        factures
        .order_by(Facture.date_facture.desc())
        .all()
    )

    return render_template(
        "factures/index.html",
        factures=factures,
        recherche=recherche,
    )


# ==========================================================
# DÉTAIL D'UNE FACTURE
# ==========================================================

@facture_bp.route("/detail/<int:id>")
@login_required
@abonnement_requis
def detail(id):

    facture = db.session.get(Facture, id)

    if facture is None:
        flash("Facture introuvable.", "danger")
        return redirect(url_for("facture.index"))

    lignes = facture.lignes

    return render_template(
        "factures/detail.html",
        facture=facture,
        lignes=lignes,
    )


# ==========================================================
# CRÉER UNE FACTURE AVEC SES PRODUITS
# ==========================================================

@facture_bp.route("/ajouter", methods=["GET", "POST"])
@login_required
@abonnement_requis
def ajouter():

    clients, produits = charger_formulaire()

    if request.method == "POST":

        # Vérifier le client
        try:
            client_id = int(request.form.get("client_id", ""))
        except (TypeError, ValueError):
            flash("Veuillez sélectionner un client valide.", "warning")
            return render_template(
                "factures/ajouter.html",
                clients=clients,
                produits=produits,
            )

        client = db.session.get(Client, client_id)

        if client is None:
            flash("Le client sélectionné n'existe pas.", "danger")
            return render_template(
                "factures/ajouter.html",
                clients=clients,
                produits=produits,
            )

        # Vérifier le mode de paiement
        paiement = request.form.get("paiement", "").strip()

        modes_autorises = [
            "Espèces",
            "Mobile Money",
            "Bancaire",
            "En attente",
        ]

        if paiement not in modes_autorises:
            flash("Veuillez choisir un mode de paiement valide.", "warning")
            return render_template(
                "factures/ajouter.html",
                clients=clients,
                produits=produits,
            )

        # Récupérer les produits et quantités
        produits_ids = request.form.getlist("produit_id[]")
        quantites = request.form.getlist("quantite[]")

        if not produits_ids or len(produits_ids) != len(quantites):
            flash("Ajoutez au moins un produit à la facture.", "warning")
            return render_template(
                "factures/ajouter.html",
                clients=clients,
                produits=produits,
            )

        lignes_a_creer = []
        demandes_stock = {}

        # Vérifier toutes les lignes avant de modifier le stock
        for produit_id_brut, quantite_brute in zip(produits_ids, quantites):

            if not produit_id_brut or not quantite_brute:
                flash("Chaque ligne doit contenir un produit et une quantité.", "warning")
                return render_template(
                    "factures/ajouter.html",
                    clients=clients,
                    produits=produits,
                )

            try:
                produit_id = int(produit_id_brut)
                quantite = int(quantite_brute)
            except (TypeError, ValueError):
                flash("Un produit ou une quantité est invalide.", "warning")
                return render_template(
                    "factures/ajouter.html",
                    clients=clients,
                    produits=produits,
                )

            if quantite <= 0:
                flash("Les quantités doivent être supérieures à zéro.", "warning")
                return render_template(
                    "factures/ajouter.html",
                    clients=clients,
                    produits=produits,
                )

            produit = db.session.get(Produit, produit_id)

            if produit is None or not produit.actif:
                flash("Un des produits sélectionnés est introuvable ou inactif.", "danger")
                return render_template(
                    "factures/ajouter.html",
                    clients=clients,
                    produits=produits,
                )

            lignes_a_creer.append((produit, quantite))

            demandes_stock[produit.id] = (
                demandes_stock.get(produit.id, 0) + quantite
            )

        # Vérifier le stock total demandé, même si un produit
        # apparaît plusieurs fois dans le formulaire.
        for produit_id, quantite_demandee in demandes_stock.items():

            produit = db.session.get(Produit, produit_id)

            if produit.quantite < quantite_demandee:
                flash(
                    f"Stock insuffisant pour {produit.nom}. "
                    f"Stock disponible : {produit.quantite}. "
                    f"Quantité demandée : {quantite_demandee}.",
                    "danger",
                )
                return render_template(
                    "factures/ajouter.html",
                    clients=clients,
                    produits=produits,
                )

        # Création et enregistrement dans une transaction unique
        try:

            facture = Facture(
                client_id=client.id,
                reference=generer_reference(),
                paiement=paiement,
                statut="Non payée",
                total=0,
            )

            db.session.add(facture)
            db.session.flush()

            for produit, quantite in lignes_a_creer:

                prix = float(produit.prix)
                total_ligne = prix * quantite

                ligne = LigneFacture(
                    facture_id=facture.id,
                    produit_id=produit.id,
                    quantite=quantite,
                    prix=prix,
                    total=total_ligne,
                )

                db.session.add(ligne)

                # Déduction du stock une seule fois
                produit.quantite -= quantite

            db.session.flush()

            # Recalcul du total à partir des lignes enregistrées
            facture.calculer_total()

            db.session.commit()

            flash(
                f"Facture {facture.reference} créée avec succès.",
                "success",
            )

            return redirect(
                url_for("facture.detail", id=facture.id)
            )

        except Exception:
            db.session.rollback()

            current_app.logger.exception(
                "Erreur pendant la création de la facture."
            )

            flash(
                "Impossible d'enregistrer la facture. "
                "Aucune modification du stock n'a été conservée.",
                "danger",
            )

            return redirect(url_for("facture.ajouter"))

    return render_template(
        "factures/ajouter.html",
        clients=clients,
        produits=produits,
    )


# ==========================================================
# AJOUTER UN PRODUIT À UNE FACTURE EXISTANTE
# ==========================================================

@facture_bp.route("/<int:id>/ajouter-produit", methods=["POST"])
@login_required
@abonnement_requis
def ajouter_produit(id):

    facture = db.session.get(Facture, id)

    if facture is None:
        flash("Facture introuvable.", "danger")
        return redirect(url_for("facture.index"))

    try:
        produit_id = int(request.form.get("produit_id", ""))
        quantite = int(request.form.get("quantite", ""))
    except (TypeError, ValueError):
        flash("Produit ou quantité invalide.", "warning")
        return redirect(url_for("facture.modifier", id=id))

    produit = db.session.get(Produit, produit_id)

    if produit is None or not produit.actif:
        flash("Produit introuvable ou inactif.", "danger")
        return redirect(url_for("facture.modifier", id=id))

    if quantite <= 0:
        flash("La quantité doit être supérieure à zéro.", "warning")
        return redirect(url_for("facture.modifier", id=id))

    if produit.quantite < quantite:
        flash(f"Stock insuffisant pour {produit.nom}.", "danger")
        return redirect(url_for("facture.modifier", id=id))

    try:
        prix = float(produit.prix)

        ligne = LigneFacture(
            facture=facture,
            produit=produit,
            quantite=quantite,
            prix=prix,
            total=prix * quantite,
        )

        db.session.add(ligne)
        produit.quantite -= quantite

        db.session.flush()
        recalculer_total(facture)

        db.session.commit()

        flash("Produit ajouté à la facture.", "success")

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erreur lors de l'ajout d'un produit.")
        flash("Impossible d'ajouter ce produit.", "danger")

    return redirect(url_for("facture.modifier", id=id))


# ==========================================================
# MODIFIER UNE FACTURE
# ==========================================================

@facture_bp.route("/modifier/<int:id>", methods=["GET", "POST"])
@login_required
@abonnement_requis
def modifier(id):

    facture = db.session.get(Facture, id)

    if facture is None:
        flash("Facture introuvable.", "danger")
        return redirect(url_for("facture.index"))

    clients, produits = charger_formulaire()

    if request.method == "POST":

        try:
            client_id = int(request.form.get("client_id", ""))
        except (TypeError, ValueError):
            flash("Veuillez sélectionner un client valide.", "warning")
            return redirect(url_for("facture.modifier", id=id))

        client = db.session.get(Client, client_id)

        if client is None:
            flash("Client introuvable.", "danger")
            return redirect(url_for("facture.modifier", id=id))

        paiement = request.form.get("paiement", "").strip()

        modes_autorises = [
            "Espèces",
            "Mobile Money",
            "Bancaire",
            "En attente",
        ]

        if paiement not in modes_autorises:
            flash("Mode de paiement invalide.", "warning")
            return redirect(url_for("facture.modifier", id=id))

        facture.client_id = client.id
        facture.paiement = paiement

        try:
            db.session.commit()
            flash("Facture modifiée avec succès.", "success")
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Erreur lors de la modification.")
            flash("Impossible de modifier la facture.", "danger")

        return redirect(url_for("facture.modifier", id=id))

    return render_template(
        "factures/modifier.html",
        facture=facture,
        clients=clients,
        produits=produits,
        lignes=facture.lignes,
    )


# ==========================================================
# SUPPRIMER UNE LIGNE DE FACTURE
# ==========================================================

@facture_bp.route("/ligne/<int:id>/supprimer", methods=["POST", "GET"])
@login_required
@abonnement_requis
def supprimer_ligne(id):

    ligne = db.session.get(LigneFacture, id)

    if ligne is None:
        flash("Ligne introuvable.", "danger")
        return redirect(url_for("facture.index"))

    facture = ligne.facture
    produit = ligne.produit

    try:
        # Remettre la quantité dans le stock
        produit.quantite += ligne.quantite

        db.session.delete(ligne)
        db.session.flush()

        recalculer_total(facture)

        facture_id = facture.id
        db.session.commit()

        flash("Produit supprimé de la facture et remis en stock.", "success")

        return redirect(
            url_for("facture.modifier", id=facture_id)
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erreur lors de la suppression de la ligne.")
        flash("Impossible de supprimer cette ligne.", "danger")
        return redirect(url_for("facture.index"))


# ==========================================================
# SUPPRIMER UNE FACTURE
# ==========================================================

@facture_bp.route("/supprimer/<int:id>", methods=["POST", "GET"])
@login_required
@abonnement_requis
def supprimer(id):

    facture = db.session.get(Facture, id)

    if facture is None:
        flash("Facture introuvable.", "danger")
        return redirect(url_for("facture.index"))

    try:
        # Restaurer le stock de chaque ligne
        for ligne in facture.lignes:
            ligne.produit.quantite += ligne.quantite

        facture_id = facture.id

        db.session.delete(facture)
        db.session.commit()

        flash("Facture supprimée et stock restauré.", "success")

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Erreur lors de la suppression de la facture.")
        flash("Impossible de supprimer cette facture.", "danger")

    return redirect(url_for("facture.index"))
