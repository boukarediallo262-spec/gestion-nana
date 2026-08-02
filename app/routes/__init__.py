# ==========================================================
# app/routes/__init__.py
# ==========================================================

"""
Initialisation des Blueprints de FASO GESTION IA.

Toutes les routes de l'application sont enregistrées ici.
"""

# ==========================================================
# IMPORT DES BLUEPRINTS
# ==========================================================

from .auth import auth_bp
from .dashboard import dashboard_bp

from .client import client_bp
from .fournisseur import fournisseur_bp
from .categorie import categorie_bp
from .produit import produit_bp
from .facture import facture_bp
from .depense import depense_bp
from .abonnement import abonnement_bp


# ==========================================================
# ENREGISTREMENT
# ==========================================================

def init_app(app):
    """
    Enregistre tous les Blueprints de l'application.
    """

    blueprints = [

        auth_bp,

        dashboard_bp,

        client_bp,
        fournisseur_bp,
        categorie_bp,
        produit_bp,
        facture_bp,
        depense_bp,

        abonnement_bp

    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint)
