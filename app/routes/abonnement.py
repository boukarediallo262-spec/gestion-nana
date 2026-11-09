
from datetime import datetime, timedelta
from secrets import token_hex

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)

from flask_login import login_required, current_user

from app import db
from app.models import Abonnement, TransactionAbonnement


abonnement_bp = Blueprint(
    "abonnement",
    __name__,
    url_prefix="/abonnement"
)


# ==========================================================
# FORMULES ET TARIFS
# ==========================================================

FORMULES = {
    "GRATUIT": {
        "montant": 0,
        "duree": None,
    },
    "STANDARD": {
        "montant": 5000,
        "duree": 30,
    },
    "PREMIUM": {
        "montant": 10000,
        "duree": 30,
    },
    "BUSINESS": {
        "montant": 20000,
        "duree": 30,
    },
}


# ==========================================================
# PAGE DES ABONNEMENTS
# ==========================================================

@abonnement_bp.route("/")
@login_required
def index():

    abonnement_actuel = current_user.abonnement_actif

    historique = (
        TransactionAbonnement.query
        .filter_by(user_id=current_user.id)
        .order_by(TransactionAbonnement.date_creation.desc())
        .limit(20)
        .all()
    )

    return render_template(
        "abonnement/index.html",
        abonnement_actuel=abonnement_actuel,
        historique=historique,
        simulation_mode=current_app.config.get(
            "SIMULATION_MODE", False
        ),
    )


# ==========================================================
# SIMULATION D'UNE SOUSCRIPTION
# ==========================================================

@abonnement_bp.route(
    "/simuler/<formule>",
    methods=["POST"]
)
@login_required
def simuler(formule):

    # Vérification du mode simulation
    if not current_app.config.get("SIMULATION_MODE", False):
        flash(
            "Le mode simulation est désactivé.",
            "danger"
        )
        return redirect(url_for("abonnement.index"))

    formule = formule.upper()

    # Vérification de la formule
    if formule not in FORMULES:
        flash(
            "Cette formule d'abonnement n'existe pas.",
            "danger"
        )
        return redirect(url_for("abonnement.index"))

    informations = FORMULES[formule]

    montant = informations["montant"]

    maintenant = datetime.utcnow()

    reference = "SIM-" + token_hex(8).upper()

    # ======================================================
    # RESULTAT DU PAIEMENT SIMULE
    # ======================================================

    if formule == "GRATUIT":
        resultat = "acceptee"
    else:
        resultat = request.form.get("resultat", "").lower()

        if resultat not in ["acceptee", "refusee"]:
            flash(
                "Choisissez un résultat de simulation valide.",
                "warning"
            )
            return redirect(url_for("abonnement.index"))

    try:

        # ==================================================
        # PAIEMENT REFUSE
        # ==================================================

        if resultat == "refusee":

            transaction = TransactionAbonnement(
                user_id=current_user.id,
                formule=formule,
                montant=montant,
                mode_paiement="Simulation",
                reference=reference,
                statut="refusee",
                simulation=True,
                message="Paiement simulé refusé. Aucun abonnement activé."
            )

            db.session.add(transaction)
            db.session.commit()

            flash(
                "Simulation terminée : paiement refusé. "
                "Votre abonnement actuel reste inchangé.",
                "warning"
            )

            return redirect(url_for("abonnement.index"))

        # ==================================================
        # CREATION DU NOUVEL ABONNEMENT
        # ==================================================

        if formule == "GRATUIT":

            date_fin = datetime(
                9999, 12, 31, 23, 59, 59
            )

        else:

            date_fin = maintenant + timedelta(days=30)

        nouvel_abonnement = Abonnement(
            type=formule,
            date_debut=maintenant,
            date_fin=date_fin,
            actif=True,
            montant=montant,
            user_id=current_user.id,
            mode_paiement="Gratuit" if montant == 0 else "Simulation",
            reference_paiement=reference,
            date_paiement=maintenant,
        )

        db.session.add(nouvel_abonnement)

        # Génération de l'identifiant
        db.session.flush()

        # ==================================================
        # DESACTIVATION DES ANCIENS ABONNEMENTS
        # ==================================================

        anciens_abonnements = (
            Abonnement.query
            .filter_by(
                user_id=current_user.id,
                actif=True
            )
            .filter(
                Abonnement.id != nouvel_abonnement.id
            )
            .all()
        )

        for ancien in anciens_abonnements:
            ancien.actif = False

        # ==================================================
        # ENREGISTREMENT DE LA TRANSACTION
        # ==================================================

        transaction = TransactionAbonnement(
            user_id=current_user.id,
            abonnement_id=nouvel_abonnement.id,
            formule=formule,
            montant=montant,
            mode_paiement="Simulation",
            reference=reference,
            statut="acceptee",
            simulation=True,
            message=(
                "Activation gratuite permanente."
                if formule == "GRATUIT"
                else "Paiement simulé accepté. "
                     "Abonnement activé pour 30 jours."
            )
        )

        db.session.add(transaction)

        # Enregistrement atomique
        db.session.commit()

        if formule == "GRATUIT":

            flash(
                "Votre formule GRATUIT a été activée "
                "sans expiration.",
                "success"
            )

        else:

            flash(
                f"Simulation réussie ! "
                f"La formule {formule} est activée "
                f"pour 30 jours.",
                "success"
            )

    except Exception as erreur:

        db.session.rollback()

        current_app.logger.exception(
            "Erreur pendant la simulation d'abonnement : %s",
            erreur
        )

        flash(
            "Une erreur est survenue. "
            "Aucun changement d'abonnement n'a été confirmé.",
            "danger"
        )

    return redirect(url_for("abonnement.index"))
