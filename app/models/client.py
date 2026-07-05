from datetime import datetime

from . import db


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
    # INFOS CLIENT
    # ==========================

    nom = db.Column(
        db.String(150),
        nullable=False
    )

    prenom = db.Column(
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

    entreprise = db.Column(
        db.String(150)
    )

    # ==========================
    # STATUT CLIENT
    # ==========================

    type_client = db.Column(
        db.String(50),
        default="Particulier"
    )  # Particulier / Entreprise / VIP

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
    # RELATION FACTURES
    # ==========================

    factures = db.relationship(
        "Facture",
        back_populates="client",
        lazy=True
    )

    # ==========================
    # PROPRIÉTÉS IMPORTANTES
    # ==========================

    @property
    def nombre_factures(self):
        return len(self.factures)

    @property
    def total_depense(self):
        return sum(
            facture.total for facture in self.factures
        )

    @property
    def dernier_achat(self):
        if not self.factures:
            return None
        return max(
            self.factures,
            key=lambda f: f.date_facture
        )

    def __repr__(self):
        return f"<Client {self.nom}>"
