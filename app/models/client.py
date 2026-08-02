from datetime import datetime

from app import db


# ==========================================================
# CLIENT
# ==========================================================

class Client(db.Model):
    __tablename__ = "clients"

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

    prenom = db.Column(
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

    entreprise = db.Column(
        db.String(150)
    )

    # ==========================
    # TYPE CLIENT
    # ==========================

    type_client = db.Column(
        db.String(50),
        default="Particulier",
        nullable=False,
        index=True
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

    factures = db.relationship(
        "Facture",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy=True
    )

    # ==========================
    # PROPRIÉTÉS
    # ==========================

    @property
    def nombre_factures(self):
        return len(self.factures)

    @property
    def total_depense(self):
        return sum(
            facture.total
            for facture in self.factures
        )

    @property
    def dernier_achat(self):
        if not self.factures:
            return None

        return max(
            self.factures,
            key=lambda facture: facture.date_facture
        )

    @property
    def nom_complet(self):
        if self.prenom:
            return f"{self.prenom} {self.nom}"
        return self.nom

    # ==========================
    # REPRÉSENTATION
    # ==========================

    def __repr__(self):
        return f"<Client {self.nom_complet}>"
