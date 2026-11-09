
from datetime import datetime

from app import db


class TransactionAbonnement(db.Model):
    __tablename__ = "transactions_abonnement"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    abonnement_id = db.Column(
        db.Integer,
        db.ForeignKey("abonnements.id"),
        nullable=True
    )

    formule = db.Column(db.String(50), nullable=False)
    montant = db.Column(db.Float, nullable=False, default=0)

    mode_paiement = db.Column(
        db.String(50),
        default="Simulation"
    )

    reference = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    statut = db.Column(
        db.String(30),
        nullable=False,
        default="en_attente"
    )

    simulation = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    message = db.Column(db.String(255))

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    utilisateur = db.relationship(
        "User",
        backref=db.backref(
            "transactions_abonnement",
            lazy=True
        )
    )

    # Pas de backref "transactions" :
    # ce nom existe déjà dans le modèle Abonnement.
    abonnement = db.relationship("Abonnement")

    def __repr__(self):
        return (
            f"<TransactionAbonnement "
            f"{self.reference} - {self.statut}>"
        )
