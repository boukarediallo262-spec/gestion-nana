from datetime import datetime

from app import db


# ==========================================================
# FOURNISSEUR
# ==========================================================

class Fournisseur(db.Model):
    __tablename__ = "fournisseurs"

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
        db.String(150),
        nullable=False,
        index=True
    )

    entreprise = db.Column(
        db.String(150)
    )

    contact = db.Column(
        db.String(150)
    )

    telephone = db.Column(
        db.String(30),
        index=True
    )

    email = db.Column(
        db.String(120),
        index=True
    )

    adresse = db.Column(
        db.Text
    )

    ville = db.Column(
        db.String(100)
    )

    pays = db.Column(
        db.String(100),
        default="Burkina Faso",
        nullable=False
    )

    site_web = db.Column(
        db.String(255)
    )

    note = db.Column(
        db.Text
    )

    # ==========================
    # DESCRIPTION
    # ==========================

    description = db.Column(
        db.Text
    )

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
    def nom_affichage(self):
        if self.entreprise:
            return f"{self.entreprise} ({self.nom})"
        return self.nom

    # ==========================
    # REPRÉSENTATION
    # ==========================

    def __repr__(self):
        return f"<Fournisseur {self.nom}>"
