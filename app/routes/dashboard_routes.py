from flask import Blueprint, render_template, request, redirect
from sqlalchemy import func
from datetime import datetime, date, timedelta

from flask import make_response
from reportlab.pdfgen import canvas
from io import BytesIO

from app.models.models import (
    db,
    Facture,
    Produit,
    Depense,
    Client,
    LigneFacture
)

dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


#============================
@dashboard_bp.route("/")
def home():

    total_produits = Produit.query.count()

    total_clients = Client.query.count()

    total_factures = Facture.query.count()

    total_ventes = db.session.query(
        func.sum(Facture.total)
    ).scalar() or 0

    total_depenses = db.session.query(
        func.sum(Depense.montant)
    ).scalar() or 0

    benefices = total_ventes - total_depenses

    stock_faible = Produit.query.filter(
        Produit.quantite <= 5
    ).count()

    abonnement = "Premium"
    # ===== Dernières factures =====

    dernieres_factures = Facture.query.order_by(
        Facture.id.desc()
    ).limit(5).all()

    # ===== Stock faible =====

    produits_stock = Produit.query.filter(
        Produit.quantite <= 5
    ).all()

    # ===== Ventes des 7 derniers jours =====

    jours = []
    ventes = []

    for i in range(6, -1, -1):

        jour = datetime.now().date() - timedelta(days=i)

        total = db.session.query(
            func.sum(Facture.total)
        ).filter(
            db.func.date(Facture.date_facture) == jour
        ).scalar() or 0

        jours.append(jour.strftime("%d/%m"))

        ventes.append(total)

    return render_template(

        "dashboard/index.html",

        total_produits=total_produits,

        total_clients=total_clients,

        total_factures=total_factures,

        total_ventes=total_ventes,

        total_depenses=total_depenses,

        benefices=benefices,

        stock_faible=stock_faible,

        abonnement=abonnement,
        dernieres_factures=dernieres_factures,
        produits_stock=produits_stock,
        jours=jours,
        ventes=ventes

    )
#===========================


@dashboard_bp.route("/statistiques")
def statistiques():

    # ==========================
    # Statistiques générales
    # ==========================

    total_produits = Produit.query.count()
    total_clients = Client.query.count()
    total_factures = Facture.query.count()

    total_ventes = db.session.query(
        func.sum(Facture.total)
    ).scalar() or 0

    total_depenses = db.session.query(
        func.sum(Depense.montant)
    ).scalar() or 0

    benefices = total_ventes - total_depenses

    # ==========================
    # Ventes aujourd'hui
    # ==========================

    aujourd_hui = date.today()

    ventes_jour = db.session.query(
        func.sum(Facture.total)
    ).filter(
        func.date(Facture.date_facture) == aujourd_hui
    ).scalar() or 0

    # ==========================
    # Ventes semaine
    # ==========================

    debut_semaine = aujourd_hui - timedelta(days=7)

    ventes_semaine = db.session.query(
        func.sum(Facture.total)
    ).filter(
        Facture.date_facture >= debut_semaine
    ).scalar() or 0

    # ==========================
    # Ventes mois
    # ==========================

    mois = datetime.now().month
    annee = datetime.now().year

    ventes_mois = db.session.query(
        func.sum(Facture.total)
    ).filter(
        func.extract("month", Facture.date_facture) == mois,
        func.extract("year", Facture.date_facture) == annee
    ).scalar() or 0
    #++++++++++++++++++++++
    top_clients = db.session.query(
        Facture.client,
        func.count(Facture.id).label("nb")
    ).group_by(Facture.client).order_by(
        func.count(Facture.id).desc()
    ).limit(5).all()

    # ==========================
    # Top produits
    # ==========================

    top_produits = (
        db.session.query(
            Produit.nom,
            func.sum(LigneFacture.quantite).label("quantite")
        )
        .join(LigneFacture)
        .group_by(Produit.id)
        .order_by(func.sum(LigneFacture.quantite).desc())
        .limit(5)
        .all()
    )

    # ==========================
    # Alertes stock
    # ==========================

    stock_faible = Produit.query.filter(
        Produit.quantite <= 5
    ).all()

    return render_template(
        "statistiques.html",

        total_produits=total_produits,
        total_clients=total_clients,
        total_factures=total_factures,

        total_ventes=total_ventes,
        total_depenses=total_depenses,
        benefices=benefices,

        ventes_jour=ventes_jour,
        ventes_semaine=ventes_semaine,
        ventes_mois=ventes_mois,
        
        top_clients=top_clients,
        top_produits=top_produits,
        stock_faible=stock_faible
    )
#=======================================

@dashboard_bp.route("/admin")
def admin():

    total_users = User.query.count() if "User" in globals() else 0
    total_produits = Produit.query.count()
    total_factures = Facture.query.count()

    total_ventes = db.session.query(func.sum(Facture.total)).scalar() or 0
    total_depenses = db.session.query(func.sum(Depense.montant)).scalar() or 0

    return render_template(
        "admin.html",
        total_users=total_users,
        total_produits=total_produits,
        total_factures=total_factures,
        total_ventes=total_ventes,
        total_depenses=total_depenses
    )
#======================================================

@dashboard_bp.route("/facture/pdf/<int:id>")
def facture_pdf(id):

    facture = Facture.query.get_or_404(id)
    lignes = LigneFacture.query.filter_by(facture_id=id).all()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    # TITRE
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 800, "FASO GESTION IA")

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 760, f"Facture ID: {facture.id}")
    pdf.drawString(50, 740, f"Client: {facture.client}")
    pdf.drawString(50, 720, f"Paiement: {facture.paiement}")
    pdf.drawString(50, 700, f"Total: {facture.total} FCFA")

    pdf.drawString(50, 670, "Produits:")

    y = 650

    for ligne in lignes:
        produit = Produit.query.get(ligne.produit_id)

        pdf.drawString(
            50,
            y,
            f"- {produit.nom} | {ligne.quantite} x {ligne.prix} = {ligne.total}"
        )

        y -= 20

    pdf.drawString(50, y-20, "Merci pour votre confiance 🙏")

    pdf.save()

    buffer.seek(0)

    response = make_response(buffer.read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=facture_{id}.pdf"

    return response
#===============================================
@dashboard_bp.route("/factures")
def factures():

    factures = Facture.query.order_by(Facture.id.desc()).all()

    total_factures = db.session.query(
        func.sum(Facture.total)
    ).scalar() or 0

    return render_template(
        "factures.html",
        factures=factures,
        total_factures=total_factures
    )
#===============================================
@dashboard_bp.route("/voir_facture/<int:id>")
def voir_facture(id):

    facture = Facture.query.get_or_404(id)

    lignes = LigneFacture.query.filter_by(facture_id=id).all()

    return render_template(
        "voir_facture.html",
        facture=facture,
        lignes=lignes
    )

#===================================================
@dashboard_bp.route("/supprimer_facture/<int:id>")
def supprimer_facture(id):

    facture = Facture.query.get_or_404(id)

    db.session.delete(facture)
    db.session.commit()

    return redirect("/factures")

#=========================================
@dashboard_bp.route("/modifier_facture/<int:id>", methods=["GET", "POST"])
def modifier_facture(id):

    facture = Facture.query.get_or_404(id)

    if request.method == "POST":

        facture.client = request.form["client"]
        facture.paiement = request.form["paiement"]

        db.session.commit()

        return redirect("/factures")

    return render_template("modifier_facture.html", facture=facture)

#===================================================================
@dashboard_bp.route("/ajouter_facture", methods=["GET", "POST"])
def ajouter_facture():

    produits = Produit.query.all()

    if request.method == "POST":

        client = request.form["client"]
        paiement = request.form["paiement"]

        facture = Facture(
            client=client,
            paiement=paiement,
            total=0
        )

        db.session.add(facture)
        db.session.commit()

        return redirect("/factures")

    return render_template("ajouter_facture.html", produits=produits)

#=====================================================================
