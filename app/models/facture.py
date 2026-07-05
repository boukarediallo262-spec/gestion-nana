from datetime import datetime

from . import db


# ==========================
# FACTURE PRINCIPALE
# ==========================

class Facture(db.Model):

    __tablename__ = "factures"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # CLIENT
    # ==========================

    client_id = db.Column(
        db.Integer,
        db.ForeignKey("clients.id"),
        nullable=False
    )

    client = db.relationship(
        "Client",
        back_populates="factures"
    )

    # ==========================
    # INFOS FACTURE
    # ==========================

    date_facture = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    statut = db.Column(
        db.String(50),
        default="Non payée"
    )  
    # Non payée / Payée / Partielle

    paiement = db.Column(
        db.String(50),
        default="Cash"
    )

    reference = db.Column(
        db.String(100),
        unique=True
    )

    total = db.Column(
        db.Float,
        default=0
    )

    # ==========================
    # RELATION LIGNES
    # ==========================

    lignes = db.relationship(
        "LigneFacture",
        back_populates="facture",
        cascade="all, delete",
        lazy=True
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
    # MÉTHODES INTELLIGENTES
    # ==========================

    def calculer_total(self):
        """Recalcule automatiquement le total de la facture"""
        self.total = sum(
            ligne.total for ligne in self.lignes
        )
        return self.total

    @property
    def est_payee(self):
        return self.statut == "Payée"

    @property
    def nombre_articles(self):
        return len(self.lignes)

    def __repr__(self):
        return f"<Facture {self.id} - {self.client_id}>"


# ==========================
# LIGNES DE FACTURE
# ==========================

class LigneFacture(db.Model):

    __tablename__ = "lignes_facture"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    facture_id = db.Column(
        db.Integer,
        db.ForeignKey("factures.id"),
        nullable=False
    )

    facture = db.relationship(
        "Facture",
        back_populates="lignes"
    )

    produit_id = db.Column(
        db.Integer,
        db.ForeignKey("produits.id"),
        nullable=False
    )

    produit = db.relationship(
        "Produit",
        back_populates="lignes_facture"
    )

    quantite = db.Column(
        db.Integer,
        nullable=False
    )

    prix = db.Column(
        db.Float,
        nullable=False
    )

    total = db.Column(
        db.Float,
        nullable=False
    )

    def calculer_total(self):
        self.total = self.quantite * self.prix
        return self.total

    def __repr__(self):
        return f"<LigneFacture {self.id}>"
