from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
 
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(300))

    abonnement = db.Column(db.Integer, default=0)

    date_fin_abonnement = db.Column(db.Date)

class Produit(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    nom = db.Column(db.String(200), nullable=False)

    prix = db.Column(db.Integer, nullable=False)

    quantite = db.Column(db.Integer, nullable=False)

    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
class Facture(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    client = db.Column(db.String(200))

    produit = db.Column(db.String(200))

    quantite = db.Column(db.Integer)

    montant = db.Column(db.Integer)

    total = db.Column(db.Float)

    paiement = db.Column(db.String(100))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(db.Integer)
    date_facture = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    lignes = db.relationship(
        'LigneFacture',
        backref='facture',
        lazy=True
    )

class LigneFacture(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    facture_id = db.Column(
        db.Integer,
        db.ForeignKey('facture.id')
    )

    produit_id = db.Column(
        db.Integer,
        db.ForeignKey('produit.id')
    )

    quantite = db.Column(db.Integer)

    prix = db.Column(db.Float)

    total = db.Column(db.Float)

    produit = db.relationship(
        "Produit",
        backref="lignes_facture"
    )


class Depense(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    categorie = db.Column(db.String(100))
    montant = db.Column(db.Float)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(db.Integer)

class Client(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    nom = db.Column(db.String(200))

    telephone = db.Column(db.String(50))

    adresse = db.Column(db.String(200))

class Abonnement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100))
    prix = db.Column(db.Float)
