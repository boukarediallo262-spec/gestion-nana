from datetime import datetime, timedelta

from app import db


class Abonnement(db.Model):
    __tablename__ = "abonnements"

    id = db.Column(db.Integer, primary_key=True)

    type = db.Column(
        db.String(50),
        nullable=False,
        default="Gratuit"
    )

    date_debut = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    date_fin = db.Column(
        db.DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=30)
    )

    actif = db.Column(
        db.Boolean,
        default=True
    )

    montant = db.Column(
        db.Float,
        default=0
    )

    # Relation avec User
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    utilisateur = db.relationship(
        "User",
        back_populates="abonnements"
    )

    def __repr__(self):
        return f"<Abonnement {self.type}>"
