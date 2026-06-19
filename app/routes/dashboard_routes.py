from flask import Blueprint, render_template, request, redirect
from app.models.models import (
    db,
    Produit,
    Facture,
    LigneFacture,
    Depense
)

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/")
def home():

    total_produits = Produit.query.count()
    total_factures = Facture.query.count()

    depenses = Depense.query.all()

    total_depenses = sum([d.montant for d in depenses])

    produits = Produit.query.limit(5).all()

    abonnement = "Actif"

    ventes_data = Facture.query.all()

    total_ventes = sum([f.total for f in ventes_data])

    depenses_data = Depense.query.all()

    total_depenses_graph = sum([d.montant for d in depenses_data])

    benefices = total_ventes - total_depenses_graph

    return render_template(
        "dashboard/index.html",
        total_produits=total_produits,
        total_factures=total_factures,
        total_depenses=total_depenses,
        abonnement=abonnement,
        produits=produits,
        total_ventes=total_ventes,
        benefices=benefices
    )

@dashboard_bp.route("/produits", methods=["GET", "POST"])
def produits():

    if request.method == "POST":

        nom = request.form.get("nom")
        prix = request.form.get("prix")
        quantite = request.form.get("quantite")

        produit_existant = Produit.query.filter_by(nom=nom).first()

        if produit_existant:

            produit_existant.quantite += int(quantite)

        else:

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

# =========================
# FACTURES
# =========================

@dashboard_bp.route("/factures")
def factures():

    toutes_factures = Facture.query.all()

    return render_template(
        "factures.html",
        factures=toutes_factures
    )

@dashboard_bp.route("/ajouter_facture", methods=["GET", "POST"])
def ajouter_facture():

    produits = Produit.query.all()

    if request.method == "POST":

        client = request.form.get("client")

        produit_id = request.form.get("produit_id")

        quantite_str = request.form.get("quantite")

        if not quantite_str:
            return "Quantité manquante"

        quantite = int(quantite_str)

        paiement = request.form.get("paiement")

        produit = Produit.query.get(int(produit_id))

        if not produit:
            return "Produit introuvable"

        # Vérification stock
        if produit.quantite < quantite:

            return "Stock insuffisant"

        # Calcul total
        total = produit.prix * quantite

        # DIMINUER LE STOCK
        produit.quantite -= quantite

        # Créer facture
        facture = Facture(
            client=client,
            paiement=paiement,
            total=total
        )
        db.session.add(facture)

        db.session.commit()

        
        ligne = LigneFacture(
            facture_id=facture.id,
            produit_id=produit.id,
            quantite=quantite,
            prix=produit.prix,
            total=total
        )

        db.session.add(ligne)

        db.session.commit()

        return redirect("/factures")

    return render_template(
        "ajouter_facture.html",
        produits=produits
    )

@dashboard_bp.route("/supprimer_facture/<int:id>")
def supprimer_facture(id):

    facture = Facture.query.get(id)

    if facture:

        db.session.delete(facture)
        db.session.commit()

    return redirect("/factures")


#======================================
@dashboard_bp.route("/voir_facture/<int:id>")
def voir_facture(id):

    facture = Facture.query.get_or_404(id)

    lignes = LigneFacture.query.filter_by(
        facture_id=id
    ).all()

    return render_template(
        "voir_facture.html",
        facture=facture,
        lignes=lignes
    )
#=======================================
from datetime import datetime
@dashboard_bp.route(
    "/modifier_facture/<int:id>",
    methods=["GET", "POST"]
)
def modifier_facture(id):

    facture = Facture.query.get_or_404(id)

    if request.method == "POST":

        facture.client = request.form.get("client")

        facture.paiement = request.form.get("paiement")
        date_facture = request.form.get("date_facture")

        if date_facture:
            facture.date_facture = datetime.strptime(
                date_facture,
                "%Y-%m-%d"
            )

        db.session.commit()

        return redirect("/voir_facture/" + str(id))

    return render_template(
        "modifier_facture.html",
        facture=facture
    )

#===========================================
@dashboard_bp.route("/depenses")
def depenses():

    toutes_depenses = Depense.query.order_by(
        Depense.created_at.desc()
    ).all()

    return render_template(
        "depenses.html",
        depenses=toutes_depenses
    )
#============================================


@dashboard_bp.route("/ajouter_depense", methods=["GET", "POST"])
def ajouter_depense():

    if request.method == "POST":

        categorie = request.form.get("categorie")

        montant = request.form.get("montant")

        depense = Depense(
            categorie=categorie,
            montant=montant
        )

        db.session.add(depense)

        db.session.commit()

        return redirect("/")

    return render_template("ajouter_depense.html")

