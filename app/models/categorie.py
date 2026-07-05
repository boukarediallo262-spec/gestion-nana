from datetime import datetime

from . import db


class Categorie(db.Model):

    __tablename__ = "categories"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nom = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    couleur = db.Column(
        db.String(20),
        default="#198754"
    )

    icone = db.Column(
        db.String(50),
        default="📦"
    )

    active = db.Column(
        db.Boolean,
        default=True
    )

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Relation avec les produits
    produits = db.relationship(
        "Produit",
        back_populates="categorie",
        lazy=True,
        cascade="all, delete"
    )

    @property
    def nombre_produits(self):
        return len(self.produits)

    def __repr__(self):
        return f"<Categorie {self.nom}>"
