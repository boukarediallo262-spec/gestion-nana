from flask import Flask
from app.models.models import db

def create_app():

    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'faso_secret'

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gestion.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


    db.init_app(app)


    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.produit_routes import produit_bp
    from app.routes.abonnement_routes import abonnement_bp


    app.register_blueprint(dashboard_bp)
    app.register_blueprint(produit_bp)
    app.register_blueprint(abonnement_bp)


    with app.app_context():
        db.create_all()

    return app
