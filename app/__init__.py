from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


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

    # --------------------------------------------------------
    # CONFIGURATION
    # --------------------------------------------------------

    app.config["SECRET_KEY"] = "secret-key-faso-gestion"

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    print("Configuration OK")

    # --------------------------------------------------------
    # INITIALISATION DATABASE
    # --------------------------------------------------------

    db.init_app(app)

    print("DB OK")

    # --------------------------------------------------------
    # INITIALISATION FLASK-LOGIN
    # --------------------------------------------------------

    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    print("Flask-Login OK")

    # --------------------------------------------------------
    # IMPORT DES MODÈLES
    # --------------------------------------------------------

    from app.models.user import User

    # Import du package models afin de charger
    # les autres modèles et leurs relations SQLAlchemy.
    from app import models

    print("Modèles OK")

    # --------------------------------------------------------
    # USER LOADER
    # --------------------------------------------------------

    @login_manager.user_loader
    def load_user(user_id):

        try:
            return User.query.get(int(user_id))

        except (TypeError, ValueError):
            return None

    print("User loader OK")

    # --------------------------------------------------------
    # INITIALISATION DES ROUTES
    # --------------------------------------------------------

    from app.routes import init_app

    init_app(app)

    print("Routes OK")

    # --------------------------------------------------------
    # CRÉATION DES TABLES
    # --------------------------------------------------------

    with app.app_context():

        db.create_all()

        print("Base de données OK")

    print("======================================")
    print("FASO GESTION IA PRÊT")
    print("======================================")

    return app
