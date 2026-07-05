from datetime import datetime

from . import db


class Fournisseur(db.Model):

    __tablename__ = "fournisseurs"

    # ==========================
    # CLÉ PRIMAIRE
    # ==========================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # IDENTITÉ
    # ==========================

    nom = db.Column(
        db.String(150),
        nullable=False
    )

    entreprise = db.Column(
        db.String(150)
    )

    contact = db.Column(
        db.String(150)
    )

    telephone = db.Column(
        db.String(30)
    )

    email = db.Column(
        db.String(120)
    )

    adresse = db.Column(
        db.Text
    )

    ville = db.Column(
        db.String(100)
    )

    pays = db.Column(
        db.String(100),
        default="Burkina Faso"
    )

    site_web = db.Column(
        db.String(255)
    )
    note = db.Column(
        db.Text
    )

    # ==========================
    # INFORMATIONS
    # ==========================

    description = db.Column(
        db.Text
    )

    actif = db.Column(
        db.Boolean,
        default=True
    )

    # ==========================
    # DATES
    # ==========================

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    date_modification = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ==========================
    # RELATION PRODUITS
    # ==========================

    produits = db.relationship(
        "Produit",
        back_populates="fournisseur",
        lazy=True
    )

    # ==========================
    # PROPRIÉTÉS
    # ==========================

    @property
    def nombre_produits(self):
        return len(self.produits)

    @property
    def produits_actifs(self):
        return len(
            [p for p in self.produits if p.actif]
        )

    # ==========================
    # REPRÉSENTATION
    # ==========================

    def __repr__(self):
        return f"<Fournisseur {self.nom}>"
