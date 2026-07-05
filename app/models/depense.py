from datetime import datetime

from . import db


class Depense(db.Model):

    __tablename__ = "depenses"

    # ==========================
    # IDENTIFIANT
    # ==========================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # INFOS DEPENSE
    # ==========================

    titre = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    montant = db.Column(
        db.Float,
        nullable=False
    )

    categorie = db.Column(
        db.String(100),
        default="Générale"
    )
    # Ex: Salaires, Transport, Achat, Électricité...

    mode_paiement = db.Column(
        db.String(50),
        default="Cash"
    )

    fournisseur = db.Column(
        db.String(150)
    )

    reference = db.Column(
        db.String(100),
        unique=True
    )

    # ==========================
    # DATE
    # ==========================

    date_depense = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # ==========================
    # ETAT
    # ==========================

    validee = db.Column(
        db.Boolean,
        default=True
    )

    # ==========================
    # PROPRIÉTÉS UTILES
    # ==========================

    @property
    def est_importante(self):
        return self.montant >= 50000

    def __repr__(self):
        return f"<Depense {self.titre} - {self.montant}>"
