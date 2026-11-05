
from datetime import datetime, timedelta
from secrets import token_hex

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app
)
from flask_login import login_required, current_user

from app import db
from app.models import Abonnement, Transaction


abonnement_bp = Blueprint(
    "abonnement",
    __name__,
    url_prefix="/abonnement"
)


FORMULES = {
    "Gratuit": {
        "montant": 0,
        "duree": None
    },
    "Standard": {
        "montant": 5000,
        "duree": 30
    },
    "Premium": {
        "montant": 10000,
        "duree": 30
    },
    "Business": {
        "montant": 20000,
        "duree": 30
    }
}


@abonnement_bp.route("/")
@login_required
def index():

    abonnement_actuel = (
        Abonnement.query
        .filter_by(user_id=current_user.id, actif=True)
        .order_by(Abonnement.date_debut.desc())
        .first()
    )

    transactions = (
        Transaction.query
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.date_transaction.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "abonnement/index.html",
        formules=FORMULES,
        abonnement_actuel=abonnement_actuel,
        transactions=transactions
    )


@abonnement_bp.route("/simulation", methods=["POST"])
@login_required
def simulation():

    # Vérification du mode simulation
    if not current_app.config.get("SIMULATION_MODE", False):
        flash("Le simulateur de paiement est désactivé.", "danger")
        return redirect(url_for("abonnement.index"))

    formule = request.form.get("formule", "").strip()
    resultat = request.form.get("resultat", "").strip().lower()

    if formule not in FORMULES:
        flash("Formule d'abonnement inconnue.", "danger")
        return redirect(url_for("abonnement.index"))

    if resultat not in ["accepte", "refuse"]:
        flash("Résultat de simulation invalide.", "danger")
        return redirect(url_for("abonnement.index"))

    configuration = FORMULES[formule]
    montant = configuration["montant"]

    # Une formule gratuite ne nécessite pas de paiement
    if formule == "Gratuit" and resultat == "refuse":
        flash("La formule gratuite ne nécessite aucun paiement.", "warning")
        return redirect(url_for("abonnement.index"))

    reference = "SIM-" + token_hex(8).upper()

    try:

        # Enregistrement d'une tentative refusée
        if resultat == "refuse":

            transaction = Transaction(
                user_id=current_user.id,
                formule=formule,
                montant=montant,
                mode_paiement="SIMULATION",
                statut="REFUSEE",
                reference=reference,
                message="Paiement fictif refusé pendant le test."
            )

            db.session.add(transaction)
            db.session.commit()

            flash(
                "Simulation terminée : paiement refusé. "
                "Aucun nouvel abonnement n'a été activé.",
                "warning"
            )

            return redirect(url_for("abonnement.index"))

        maintenant = datetime.utcnow()

        # Désactivation des anciens abonnements actifs
        anciens_abonnements = Abonnement.query.filter_by(
            user_id=current_user.id,
            actif=True
        ).all()

        for ancien in anciens_abonnements:
            ancien.actif = False

        # Durée de la formule
        if formule == "Gratuit":
            date_fin = datetime(2099, 12, 31)
        else:
            date_fin = maintenant + timedelta(
                days=configuration["duree"]
            )

        nouvel_abonnement = Abonnement(
            type=formule,
            date_debut=maintenant,
            date_fin=date_fin,
            actif=True,
            montant=montant,
            user_id=current_user.id,
            mode_paiement="SIMULATION",
            reference_paiement=reference,
            date_paiement=maintenant
        )

        db.session.add(nouvel_abonnement)
        db.session.flush()

        transaction = Transaction(
            user_id=current_user.id,
            abonnement_id=nouvel_abonnement.id,
            formule=formule,
            montant=montant,
            mode_paiement="SIMULATION",
            statut="ACCEPTEE",
            reference=reference,
            message="Paiement fictif accepté pendant le test."
        )

        db.session.add(transaction)
        db.session.commit()

        flash(
            f"Simulation réussie ! Votre formule {formule} "
            "est maintenant activée.",
            "success"
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception(
            "Erreur pendant la simulation d'abonnement"
        )
        flash(
            "Une erreur est survenue pendant la simulation.",
            "danger"
        )

    return redirect(url_for("abonnement.index"))
