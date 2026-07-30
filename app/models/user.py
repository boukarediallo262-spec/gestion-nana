from datetime import datetime

from flask_login import UserMixin
from app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # ==========================
    # Informations personnelles
    # ==========================

    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100))
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )
    telephone = db.Column(
        db.String(30),
        unique=True
    )

    # ==========================
    # Authentification
    # ==========================

    mot_de_passe = db.Column(
        db.String(255),
        nullable=False
    )

    # ==========================
    # Gestion des droits
    # ==========================

    role = db.Column(
        db.String(20),
        default="utilisateur",
        nullable=False
    )

    actif = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    # ==========================
    # Dates
    # ==========================

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ==========================
    # Relations
    # ==========================

    abonnements = db.relationship(
        "Abonnement",
        back_populates="utilisateur",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.nom}>"
