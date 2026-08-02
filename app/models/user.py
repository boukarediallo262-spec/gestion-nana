from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from app import db


# ==========================================================
# UTILISATEUR
# ==========================================================

class User(UserMixin, db.Model):
    __tablename__ = "users"

    # ==========================
    # IDENTIFIANT
    # ==========================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # INFORMATIONS PERSONNELLES
    # ==========================

    nom = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    prenom = db.Column(
        db.String(100)
    )

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
    # AUTHENTIFICATION
    # ==========================

    mot_de_passe = db.Column(
        db.String(255),
        nullable=False
    )

    # ==========================
    # ROLE
    # ==========================

    role = db.Column(
        db.String(20),
        default="utilisateur",
        nullable=False
    )

    # ==========================
    # ETAT DU COMPTE
    # ==========================

    actif = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    # ==========================
    # DATES
    # ==========================

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    date_modification = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # ==========================
    # RELATIONS
    # ==========================

    abonnements = db.relationship(
        "Abonnement",
        back_populates="utilisateur",
        cascade="all, delete-orphan",
        lazy=True
    )

    # ==========================
    # SECURITE
    # ==========================

    def set_password(self, password):
        """
        Hash le mot de passe avant enregistrement.
        """
        self.mot_de_passe = generate_password_hash(password)

    def check_password(self, password):
        """
        Vérifie le mot de passe.
        """
        return check_password_hash(
            self.mot_de_passe,
            password
        )

    # ==========================
    # PROPRIETES
    # ==========================

    @property
    def abonnement_actif(self):
        """
        Retourne le premier abonnement actif.
        """
        for abonnement in self.abonnements:
            if abonnement.actif and not abonnement.est_expire:
                return abonnement
        return None

    @property
    def est_admin(self):
        return self.role.lower() == "admin"

    @property
    def nom_complet(self):
        if self.prenom:
            return f"{self.prenom} {self.nom}"
        return self.nom

    # ==========================
    # REPRESENTATION
    # ==========================

    def __repr__(self):
        return (
            f"<User {self.nom_complet}>"
        )
