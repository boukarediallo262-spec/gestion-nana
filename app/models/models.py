from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


# =========================
# USER
# =========================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    abonnement = db.Column(db.Integer, default=0)

    date_fin_abonnement = db.Column(db.Date)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# =========================
# PRODUITS
# =========================
class Produit(db.Model):
    __tablename__ = "produits"

    id = db.Column(db.Integer, primary_key=True)

    nom = db.Column(db.String(255))

    quantite = db.Column(db.Integer, default=0)

    prix_vente = db.Column(db.Float, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))


# =========================
# FACTURES
# =========================
class Facture(db.Model):
    __tablename__ = "factures"

    id = db.Column(db.Integer, primary_key=True)

    total = db.Column(db.Float, default=0)

    statut = db.Column(db.String(50), default="payé")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))


# =========================
# DEPENSES
# =========================
class Depense(db.Model):
    __tablename__ = "depenses"

    id = db.Column(db.Integer, primary_key=True)

    categorie = db.Column(db.String(255))

    montant = db.Column(db.Float)

    description = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
