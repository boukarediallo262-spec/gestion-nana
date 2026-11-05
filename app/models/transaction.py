
from datetime import datetime

from app import db


class Transaction(db.Model):
    __tablename__ = "transactions"

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
        nullable=False,
        default="SIMULATION"
    )

    statut = db.Column(
        db.String(30),
        nullable=False
    )

    reference = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    date_transaction = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

    message = db.Column(db.String(255))

    utilisateur = db.relationship(
        "User",
        backref=db.backref("transactions", lazy=True)
    )

    abonnement = db.relationship(
        "Abonnement",
        backref=db.backref("transactions", lazy=True)
    )

    def __repr__(self):
        return f"<Transaction {self.reference} - {self.statut}>"
