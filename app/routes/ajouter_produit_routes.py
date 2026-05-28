from flask import Blueprint, render_template, request, redirect
from app.models.models import db, Produit

produit_bp = Blueprint("produit_bp", __name__)

# =========================
# AFFICHER + AJOUTER PRODUITS
# =========================

@produit_bp.route("/produits", methods=["GET", "POST"])
def produits():

    if request.method == "POST":

        nom = request.form.get("nom")
        prix = request.form.get("prix")
        quantite = request.form.get("quantite")

        # Vérification simple

        if nom and prix and quantite:

            nouveau_produit = Produit(

                nom=nom,
                prix=float(prix),
                quantite=int(quantite)

            )

            db.session.add(nouveau_produit)

            db.session.commit()

        return redirect("/produits")

    # AFFICHER PRODUITS

    produits = Produit.query.all()

    return render_template(

        "produits.html",
        produits=produits

    )


# =========================
# SUPPRIMER PRODUIT
# =========================

@produit_bp.route("/supprimer_produit/<int:id>")
def supprimer_produit(id):

    produit = Produit.query.get_or_404(id)

    db.session.delete(produit)

    db.session.commit()

    return redirect("/produits")


# =========================
# MODIFIER PRODUIT
# =========================

@produit_bp.route("/modifier_produit/<int:id>", methods=["GET", "POST"])
def modifier_produit(id):

    produit = Produit.query.get_or_404(id)

    if request.method == "POST":

        produit.nom = request.form.get("nom")

        produit.prix = float(request.form.get("prix"))

        produit.quantite = int(request.form.get("quantite"))

        db.session.commit()

        return redirect("/produits")

    return render_template(

        "modifier_produit.html",
        produit=produit

    )
