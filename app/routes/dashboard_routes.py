from flask import Blueprint, render_template, request, redirect
from app.models.models import (
    db,
    Produit,
    Facture,
    LigneFacture,
    Depense
)
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file
import os
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
from datetime import datetime
@dashboard_bp.route("/ajouter_facture", methods=["GET", "POST"])
def ajouter_facture():

    produits = Produit.query.all()

    if request.method == "POST":

        client = request.form.get("client")
        paiement = request.form.get("paiement")

        produits_ids = request.form.getlist("produit_id[]")
        quantites = request.form.getlist("quantite[]")

        facture = Facture(
            client=client,
            paiement=paiement,
            total=0,
            date_facture=datetime.utcnow()
        )

        db.session.add(facture)
        db.session.commit()

        total_facture = 0

        for i in range(len(produits_ids)):

            produit = Produit.query.get(
                int(produits_ids[i])
            )

            quantite = int(
                quantites[i]
            )

            if not produit:
                return "Produit introuvable"

            if produit.quantite < quantite:
                return f"Stock insuffisant pour {produit.nom}"

            total_ligne = produit.prix * quantite

            produit.quantite -= quantite

            ligne = LigneFacture(
                facture_id=facture.id,
                produit_id=produit.id,
                quantite=quantite,
                prix=produit.prix,
                total=total_ligne
            )

            db.session.add(ligne)

            total_facture += total_ligne

        facture.total = total_facture

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

@dashboard_bp.route("/facture_pdf/<int:id>")
def facture_pdf(id):

    facture = Facture.query.get_or_404(id)

    lignes = LigneFacture.query.filter_by(
        facture_id=id
    ).all()

    filename = f"facture_{id}.pdf"

    pdf = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    elements = []

    elements.append(
        Paragraph(
            "FASO GESTION IA",
            styles['Title']
        )
    )

    elements.append(
        Paragraph(
            f"Facture N° {facture.id}",
            styles['Heading2']
        )
    )

    elements.append(
        Paragraph(
            f"Client : {facture.client}",
            styles['Normal']
        )
    )

    elements.append(
        Paragraph(
            f"Paiement : {facture.paiement}",
            styles['Normal']
        )
    )

    elements.append(Spacer(1, 20))

    for ligne in lignes:

        elements.append(
            Paragraph(
                f"{ligne.produit.nom} | "
                f"{ligne.quantite} x "
                f"{ligne.prix} FCFA = "
                f"{ligne.total} FCFA",
                styles['Normal']
            )
        )

    elements.append(Spacer(1, 20))

    elements.append(
        Paragraph(
            f"TOTAL : {facture.total} FCFA",
            styles['Heading2']
        )
    )

    pdf.build(elements)

    return send_file(
        filename,
        as_attachment=True
    )
