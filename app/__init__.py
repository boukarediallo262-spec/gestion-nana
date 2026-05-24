from flask import Flask
from app.models.models import db

def create_app():

    app = Flask(__name__)

    app.config["SECRET_KEY"] = "super-secret-key"

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    # IMPORT ROUTES
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp

    # REGISTER BLUEPRINTS
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)

    return app
