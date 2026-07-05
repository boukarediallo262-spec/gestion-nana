from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():

    app = Flask(__name__)

    # ==========================
    # CONFIG
    # ==========================
    app.config["SECRET_KEY"] = "secret-key-faso-gestion"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ==========================
    # INIT EXTENSIONS
    # ==========================
    db.init_app(app)
    login_manager.init_app(app)

    # ==========================
    # IMPORT MODELS
    # ==========================
    from app.models import (
        User,
        Produit,
        Client,
        Facture,
        Depense,
        Categorie,
        Fournisseur
    )

    # ==========================
    # IMPORT BLUEPRINTS
    # ==========================
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.facture_routes import facture_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(facture_bp)

    return app
