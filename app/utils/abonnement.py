from functools import wraps
from datetime import datetime

from flask import redirect, url_for, flash
from flask_login import current_user

from app.models import Abonnement


def abonnement_requis(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        abonnement = (
            Abonnement.query
            .filter_by(user_id=current_user.id)
            .order_by(Abonnement.date_fin.desc())
            .first()
        )

        if abonnement is None:
            flash("Vous n'avez aucun abonnement.", "warning")
            return redirect(url_for("abonnement.index"))

        if abonnement.date_fin < datetime.utcnow():
            flash("Votre abonnement a expiré.", "danger")
            return redirect(url_for("abonnement.index"))

        return f(*args, **kwargs)

    return decorated_function
