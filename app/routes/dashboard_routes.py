from flask import Blueprint, render_template
from app.models.models import Produit, Facture, Depense

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def home():

    total_produits = Produit.query.count()
    total_factures = Facture.query.count()

    depenses = Depense.query.all()

    total_depenses = sum([d.montant for d in depenses])

    produits = Produit.query.limit(5).all()

    abonnement = "Actif"

    return render_template(
        "dashboard/index.html",
        total_produits=total_produits,
        total_factures=total_factures,
        total_depenses=total_depenses,
        abonnement=abonnement,
        produits=produits
    )

@dashboard_bp.route("/produits", methods=["GET", "POST"])
def produits():

    if request.method == "POST":

        nom = request.form.get("nom")
        prix = request.form.get("prix")
        quantite = request.form.get("quantite")

        nouveau_produit = Produit(
            nom=nom,
            prix=prix,
            quantite=quantite
        )

        db.session.add(nouveau_produit)
        db.session.commit()

        return redirect("/produits")

    produits = Produit.query.all()

    return render_template(
        "produits.html",
        produits=produits
    )
