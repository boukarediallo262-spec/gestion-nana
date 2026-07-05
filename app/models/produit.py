from datetime import datetime

from . import db


class Produit(db.Model):

    __tablename__ = "produits"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ========= INFORMATIONS =========

    nom = db.Column(
        db.String(150),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    reference = db.Column(
        db.String(50),
        unique=True
    )

    code_barre = db.Column(
        db.String(100),
        unique=True
    )

    image = db.Column(
        db.String(255)
    )

    # ========= CATEGORIE =========

    categorie_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id"),
        nullable=False
    )

    categorie = db.relationship(
        "Categorie",
        back_populates="produits"
    )

    # ========= FOURNISSEUR =========

    fournisseur_id = db.Column(
        db.Integer,
        db.ForeignKey("fournisseurs.id")
    )

    fournisseur = db.relationship(
        "Fournisseur",
        back_populates="produits"
    )

    # ========= PRIX =========

    prix_achat = db.Column(
        db.Float,
        default=0
    )

    prix = db.Column(
        db.Float,
        nullable=False
    )

    tva = db.Column(
        db.Float,
        default=0
    )

    # ========= STOCK =========

    quantite = db.Column(
        db.Integer,
        default=0
    )

    stock_minimum = db.Column(
        db.Integer,
        default=5
    )

    unite = db.Column(
        db.String(20),
        default="Pièce"
    )

    # ========= ETAT =========

    actif = db.Column(
        db.Boolean,
        default=True
    )

    # ========= DATES =========

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    date_modification = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ========= RELATIONS =========

    lignes_facture = db.relationship(
        "LigneFacture",
        back_populates="produit",
        lazy=True
    )

    # ========= PROPRIÉTÉS =========

    @property
    def stock_faible(self):
        return self.quantite <= self.stock_minimum

    @property
    def valeur_stock(self):
        return self.quantite * self.prix

    @property
    def valeur_achat_stock(self):
        return self.quantite * self.prix_achat

    @property
    def marge_unitaire(self):
        return self.prix - self.prix_achat

    @property
    def marge_totale_stock(self):
        return self.quantite * self.marge_unitaire

    def __repr__(self):
        return f"<Produit {self.nom}>"
