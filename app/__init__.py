from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():

    app = Flask(__name__)

    app.config["SECRET_KEY"] = "secret-key-faso-gestion"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # Import des modèles APRÈS l'initialisation
    from app.models.user import User
    from app import models

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes import init_app
    init_app(app)

    with app.app_context():
        db.create_all()

    return app
