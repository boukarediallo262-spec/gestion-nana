# app/routes/__init__.py

"""
Package des routes de FASO GESTION IA
Ce fichier permet d'organiser toutes les routes de l'application.
"""

# Import des blueprints (on les ajoutera progressivement)

from .dashboard import dashboard_bp
from .facture import facture_bp
from .client import client_bp
from .produit import produit_bp
from .depense import depense_bp
from .categorie import categorie_bp
from .fournisseur import fournisseur_bp
from .abonnement import abonnement_bp
from .auth import auth_bp


def init_app(app):
    """
    Enregistre tous les blueprints dans l'application Flask
    """

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(facture_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(produit_bp)
    app.register_blueprint(depense_bp)
    app.register_blueprint(categorie_bp)
    app.register_blueprint(fournisseur_bp)
    app.register_blueprint(abonnement_bp)
    app.register_blueprint(auth_bp)
