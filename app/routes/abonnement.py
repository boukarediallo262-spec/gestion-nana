from flask import Blueprint, render_template

abonnement_bp = Blueprint(
    "abonnement",
    __name__,
    url_prefix="/abonnement"
)


@abonnement_bp.route("/")
def index():

    mode_paiement = db.Column(
        db.String(50),
        default="Orange Money"
    )

    reference_paiement = db.Column(
        db.String(100)
    )

    date_paiement = db.Column(
        db.DateTime
    )
    

    return render_template("abonnement/index.html")
