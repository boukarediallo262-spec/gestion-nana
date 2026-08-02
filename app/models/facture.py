from datetime import datetime

from app import db


# ==========================================================
# FACTURE
# ==========================================================

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
        nullable=False,
        index=True
    )

    client = db.relationship(
        "Client",
        back_populates="factures"
    )

    # ==========================
    # INFORMATIONS
    # ==========================

    reference = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    date_facture = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    statut = db.Column(
        db.String(50),
        default="Non payée",
        nullable=False,
        index=True
    )

    paiement = db.Column(
        db.String(50),
        default="Cash",
        nullable=False
    )

    total = db.Column(
        db.Float,
        default=0,
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

    lignes = db.relationship(
        "LigneFacture",
        back_populates="facture",
        cascade="all, delete-orphan",
        lazy=True
    )

    # ==========================
    # PROPRIÉTÉS
    # ==========================

    @property
    def est_payee(self):
        return self.statut.lower() == "payée"

    @property
    def nombre_articles(self):
        return sum(
            ligne.quantite
            for ligne in self.lignes
        )

    # ==========================
    # MÉTHODES
    # ==========================

    def calculer_total(self):
        self.total = sum(
            ligne.total
            for ligne in self.lignes
        )
        return self.total

    def __repr__(self):
        return f"<Facture {self.reference}>"



# ==========================================================
# LIGNE DE FACTURE
# ==========================================================

class LigneFacture(db.Model):
    __tablename__ = "lignes_facture"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================
    # FACTURE
    # ==========================

    facture_id = db.Column(
        db.Integer,
        db.ForeignKey("factures.id"),
        nullable=False,
        index=True
    )

    facture = db.relationship(
        "Facture",
        back_populates="lignes"
    )

    # ==========================
    # PRODUIT
    # ==========================

    produit_id = db.Column(
        db.Integer,
        db.ForeignKey("produits.id"),
        nullable=False,
        index=True
    )

    produit = db.relationship(
        "Produit",
        back_populates="lignes_facture"
    )

    # ==========================
    # INFORMATIONS
    # ==========================

    quantite = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )

    prix = db.Column(
        db.Float,
        nullable=False
    )

    total = db.Column(
        db.Float,
        default=0,
        nullable=False
    )

    # ==========================
    # MÉTHODES
    # ==========================

    def calculer_total(self):
        self.total = self.quantite * self.prix
        return self.total

    def __repr__(self):
        return f"<LigneFacture {self.id}>"
