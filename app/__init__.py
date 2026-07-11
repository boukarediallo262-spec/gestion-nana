from flask import Flask
from flask_login import LoginManager

from app.models import db, User

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Veuillez vous connecter."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app():

    app = Flask(__name__)

    # ==========================
    # CONFIGURATION
    # ==========================

    app.config["SECRET_KEY"] = "secret-key-faso-gestion"

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ==========================
    # INITIALISATION
    # ==========================

    db.init_app(app)
    login_manager.init_app(app)

    # ==========================
    # IMPORT DES MODÈLES
    # ==========================

    import app.models

    # ==========================
    # ENREGISTREMENT DES ROUTES
    # ==========================

    from app.routes import init_app
    init_app(app)

    # ==========================
    # CRÉATION DES TABLES
    # ==========================

    with app.app_context():
        db.create_all()

    return app
