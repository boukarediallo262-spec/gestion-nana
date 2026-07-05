from datetime import datetime

from . import db


class Abonnement(db.Model):

    __tablename__ = "abonnements"

    id = db.Column(db.Integer, primary_key=True)

    nom = db.Column(db.String(100))  # Free / Premium

    prix = db.Column(db.Float, default=0)

    actif = db.Column(db.Boolean, default=True)

    date_debut = db.Column(db.DateTime, default=datetime.utcnow)

    date_fin = db.Column(db.DateTime)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
