from flask import Flask
from flask_login import LoginManager
from app.models import db, User

login_manager = LoginManager()

def create_app():

    app = Flask(__name__)

    app.config["SECRET_KEY"] = "secret-key-faso-gestion"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app import models

    from app.routes import init_app
    init_app(app)

    with app.app_context():
        db.create_all()

    return app
