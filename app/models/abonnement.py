from datetime import datetime, timedelta

from app import db


class Abonnement(db.Model):
    __tablename__ = "abonnements"

    id = db.Column(db.Integer, primary_key=True)

    type = db.Column(
        db.String(50),
        nullable=False,
        default="Standard"
    )

    date_debut = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    date_fin = db.Column(
        db.DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=30),
        nullable=False
    )

    actif = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    montant = db.Column(
        db.Float,
        default=20000,
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    mode_paiement = db.Column(
        db.String(50),
        default="Orange Money"
    )

    reference_paiement = db.Column(
        db.String(100),
        unique=True
    )

    date_paiement = db.Column(db.DateTime)

    utilisateur = db.relationship(
        "User",
        back_populates="abonnements"
    )

    @property
    def jours_restants(self):
        aujourd_hui = datetime.utcnow()

        if self.date_fin <= aujourd_hui:
            return 0

        return (self.date_fin - aujourd_hui).days

    @property
    def est_expire(self):
        return datetime.utcnow() >= self.date_fin

    @property
    def statut(self):

        if not self.actif:
            return "Inactif"

        if self.est_expire:
            return "Expiré"

        if self.jours_restants <= 7:
            return "Expire bientôt"

        return "Actif"

    def __repr__(self):
        return f"<Abonnement {self.type}>"
