from app.routes.abonnement_routes import abonnement_bp
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.register_blueprint(abonnement_bp)


    db.init_app(app)

    # IMPORT BLUEPRINTS
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    # CREATE TABLES
    with app.app_context():
        db.create_all()

    return app
