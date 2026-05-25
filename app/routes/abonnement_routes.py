from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import db, User

abonnement_bp = Blueprint('abonnement', __name__)


# PAGE ABONNEMENT
@abonnement_bp.route('/abonnement')
def abonnement():
    users = User.query.all()
    return render_template(
        'abonnement.html',
        users=users
    )


# ACTIVER ABONNEMENT
@abonnement_bp.route('/activer_abonnement/<int:user_id>')
def activer_abonnement(user_id):
    user = User.query.get_or_404(user_id)

    user.abonnement = 1

    db.session.commit()

    flash("Abonnement activé avec succès", "success")

    return redirect(url_for('abonnement.abonnement'))


# DESACTIVER ABONNEMENT
@abonnement_bp.route('/desactiver_abonnement/<int:user_id>')
def desactiver_abonnement(user_id):
    user = User.query.get_or_404(user_id)

    user.abonnement = 0

    db.session.commit()

    flash("Abonnement désactivé", "warning")

    return redirect(url_for('abonnement.abonnement'))
