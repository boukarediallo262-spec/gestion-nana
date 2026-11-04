
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from datetime import datetime
from math import ceil

# ============================================================
# EXTENSIONS
# ============================================================

db = SQLAlchemy()
login_manager = LoginManager()


# ============================================================
# FACTORY APPLICATION
# ============================================================

def create_app():

    print("======================================")
    print("FASO GESTION IA - DÉMARRAGE")
    print("======================================")

    app = Flask(__name__)

    print("Application Flask créée")

    # CONFIGURATION
    app.config["SECRET_KEY"] = "secret-key-faso-gestion"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    print("Configuration OK")

    # INITIALISATION DATABASE
    db.init_app(app)
    print("DB OK")

    # INITIALISATION FLASK-LOGIN
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    print("Flask-Login OK")

    # IMPORT DES MODÈLES
    from app.models.user import User
    from app import models

    print("Modèles OK")

    # USER LOADER
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except (TypeError, ValueError):
            return None

    print("User loader OK")

    # ========================================================
    # NOTIFICATION AUTOMATIQUE D'ABONNEMENT
    # ========================================================

    @app.context_processor
    def injecter_abonnement():

        if not current_user.is_authenticated:
            return {
                "abonnement_notification": None
            }

        from app.models import Abonnement

        maintenant = datetime.utcnow()

        abonnement = (
            Abonnement.query
            .filter_by(user_id=current_user.id)
            .order_by(Abonnement.date_fin.desc())
            .first()
        )

        if abonnement is None:
            return {
                "abonnement_notification": {
                    "statut": "aucun",
                    "message": "Vous n'avez aucun abonnement actif.",
                    "jours": 0,
                    "date_fin": None
                }
            }

        if not abonnement.actif:
            return {
                "abonnement_notification": {
                    "statut": "inactif",
                    "message": "Votre abonnement est inactif.",
                    "jours": 0,
                    "date_fin": abonnement.date_fin.strftime("%d/%m/%Y")
                }
            }

        if abonnement.date_fin <= maintenant:
            return {
                "abonnement_notification": {
                    "statut": "expire",
                    "message": "Votre abonnement a expiré.",
                    "jours": 0,
                    "date_fin": abonnement.date_fin.strftime("%d/%m/%Y")
                }
            }

        jours_restants = max(
            1,
            ceil((abonnement.date_fin - maintenant).total_seconds() / 86400)
        )

        if jours_restants <= 7:
            statut = "attention"
            message = f"Attention ! Votre abonnement expire dans {jours_restants} jour(s)."

        else:
            statut = "actif"
            message = f"Votre abonnement est actif : {jours_restants} jour(s) restant(s)."

        return {
            "abonnement_notification": {
                "statut": statut,
                "message": message,
                "jours": jours_restants,
                "date_fin": abonnement.date_fin.strftime("%d/%m/%Y")
            }
        }

    print("Notification abonnement OK")

    # INITIALISATION DES ROUTES
    from app.routes import init_app
    init_app(app)

    print("Routes OK")

    # CRÉATION DES TABLES
    with app.app_context():
        db.create_all()
        print("Base de données OK")

    print("======================================")
    print("FASO GESTION IA PRÊT")
    print("======================================")

    return app
