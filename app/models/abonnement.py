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
        default=20000
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    utilisateur = db.relationship(
        "User",
        back_populates="abonnements"
    )

    # ==========================
    # PROPRIÉTÉS
    # ==========================

    @property
    def jours_restants(self):
        """Retourne le nombre de jours restants."""
        aujourd_hui = datetime.utcnow()

        if self.date_fin <= aujourd_hui:
            return 0

        return (self.date_fin - aujourd_hui).days

    @property
    def est_expire(self):
        return datetime.utcnow() > self.date_fin

    @property
    def statut(self):

        if self.est_expire:
            return "Expiré"

        if self.jours_restants <= 7:
            return "Expire bientôt"

        return "Actif"

    def __repr__(self):
        return f"<Abonnement {self.type}>"
