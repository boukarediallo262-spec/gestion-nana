from datetime import datetime

from app import db


# ==========================================================
# CATEGORIE
# ==========================================================

class Categorie(db.Model):
    __tablename__ = "categories"

    # ==========================
    # IDENTIFIANT
    # ==========================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # INFORMATIONS
    # ==========================

    nom = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    description = db.Column(
        db.Text
    )

    couleur = db.Column(
        db.String(20),
        default="#198754",
        nullable=False
    )

    icone = db.Column(
        db.String(50),
        default="📦",
        nullable=False
    )

    active = db.Column(
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

    produits = db.relationship(
        "Produit",
        back_populates="categorie",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # ==========================
    # PROPRIÉTÉS
    # ==========================

    @property
    def nombre_produits(self):
        return len(self.produits)

    @property
    def produits_actifs(self):
        return sum(
            1
            for produit in self.produits
            if produit.actif
        )

    @property
    def valeur_stock(self):
        return sum(
            produit.valeur_stock
            for produit in self.produits
        )

    @property
    def stock_total(self):
        return sum(
            produit.quantite
            for produit in self.produits
        )

    # ==========================
    # REPRÉSENTATION
    # ==========================

    def __repr__(self):
        return f"<Categorie {self.nom}>"
