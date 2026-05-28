from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(300))

    abonnement = db.Column(db.Integer, default=0)

    date_fin_abonnement = db.Column(db.Date)

class Produit(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    nom = db.Column(db.String(200))

    prix = db.Column(db.Integer)

    stock = db.Column(db.Integer, default=0)

    stock_min = db.Column(db.Integer, default=5)

    categorie = db.Column(db.String(100))

    description = db.Column(db.Text)

    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
class Facture(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    client = db.Column(db.String(200))

    produit = db.Column(db.String(200))

    quantite = db.Column(db.Integer)
    montant = db.Column(db.Integer)

    total = db.Column(db.Float)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_id = db.Column(db.Integer)

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
