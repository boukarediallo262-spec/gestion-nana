from flask import Blueprint, render_template

abonnement_bp = Blueprint(
    "abonnement",
    __name__,
    url_prefix="/abonnement"
)


@abonnement_bp.route("/")
def index():

    return render_template("abonnement/index.html")
