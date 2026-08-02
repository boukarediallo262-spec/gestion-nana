from datetime import datetime

from app import db


# ==========================================================
# DEPENSE
# ==========================================================

class Depense(db.Model):
    __tablename__ = "depenses"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # INFORMATIONS
    # ==========================

    titre = db.Column(
        db.String(150),
        nullable=False,
        index=True
    )

    description = db.Column(
        db.Text
    )

    categorie = db.Column(
        db.String(100),
        nullable=False,
        default="Autres",
        index=True
    )

    fournisseur = db.Column(
        db.String(150)
    )

    # ==========================
    # MONTANT
    # ==========================

    montant = db.Column(
        db.Float,
        nullable=False,
        default=0
    )

    mode_paiement = db.Column(
        db.String(50),
        nullable=False,
        default="Espèces"
    )

    # ==========================
    # DATE
    # ==========================

    date_depense = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )

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
    # ETAT
    # ==========================

    actif = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    # ==========================
    # PROPRIÉTÉS
    # ==========================

    @property
    def montant_formate(self):
        return f"{self.montant:,.0f} FCFA".replace(",", " ")

    # ==========================
    # REPRÉSENTATION
    # ==========================

    def __repr__(self):
        return f"<Depense {self.titre}>"
