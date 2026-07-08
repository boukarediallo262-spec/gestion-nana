from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import des modèles
from .user import User
from .categorie import Categorie
from .produit import Produit
from .client import Client
from .fournisseur import Fournisseur
from .depense import Depense
from .facture import Facture, LigneFacture
from .abonnement import Abonnement
