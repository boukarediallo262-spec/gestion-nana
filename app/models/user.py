from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from . import db


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    nom = db.Column(db.String(120), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    telephone = db.Column(db.String(30))

    role = db.Column(
        db.String(30),
        default="Utilisateur"
    )

    actif = db.Column(
        db.Boolean,
        default=True
    )

    date_creation = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    abonnement = db.Column(
        db.String(50),
        default="Free"
    )

    # --------------------------

    def set_password(self, mot_de_passe):

        self.password = generate_password_hash(
            mot_de_passe
        )

    def check_password(self, mot_de_passe):

        return check_password_hash(
            self.password,
            mot_de_passe
        )

    def __repr__(self):

        return f"<User {self.nom}>"
