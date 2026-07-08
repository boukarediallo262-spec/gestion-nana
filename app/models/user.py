from datetime import datetime

from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # Informations
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    telephone = db.Column(db.String(30))

    # Connexion
    mot_de_passe = db.Column(db.String(255), nullable=False)

    # Rôle
    role = db.Column(
        db.String(20),
        default="utilisateur"
    )

    # Compte
    actif = db.Column(
        db.Boolean,
        default=True
    )

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Relation avec les abonnements
    abonnements = db.relationship(
        "Abonnement",
        back_populates="utilisateur",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.nom}>"
