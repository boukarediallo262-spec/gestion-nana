from flask import Blueprint, render_template, request, redirect, url_for

from app.models import db, Client

from flask_login import login_required
from app.utils.abonnement import abonnement_requis

@client_bp.route("/")
@login_required
@abonnement_requis
def clients():
    ...

client_bp = Blueprint("client", __name__)


# ==========================
# LISTE CLIENTS
# ==========================

@client_bp.route("/clients")
def liste_clients():

    clients = Client.query.order_by(Client.id.desc()).all()

    return render_template(
        "clients/liste.html",
        clients=clients
    )


# ==========================
# AJOUT CLIENT
# ==========================

@client_bp.route("/clients/ajouter", methods=["GET", "POST"])
def ajouter_client():

    if request.method == "POST":

        client = Client(

            nom=request.form["nom"],
            prenom=request.form.get("prenom"),
            telephone=request.form.get("telephone"),
            email=request.form.get("email"),
            adresse=request.form.get("adresse"),
            ville=request.form.get("ville"),
            entreprise=request.form.get("entreprise"),
            type_client=request.form.get("type_client", "Particulier")
        )

        db.session.add(client)
        db.session.commit()

        return redirect(url_for("client.liste_clients"))

    return render_template(
        "clients/ajouter.html"
    )


# ==========================
# MODIFIER CLIENT
# ==========================

@client_bp.route("/clients/modifier/<int:id>", methods=["GET", "POST"])
def modifier_client(id):

    client = Client.query.get_or_404(id)

    if request.method == "POST":

        client.nom = request.form["nom"]
        client.prenom = request.form.get("prenom")
        client.telephone = request.form.get("telephone")
        client.email = request.form.get("email")
        client.adresse = request.form.get("adresse")
        client.ville = request.form.get("ville")
        client.entreprise = request.form.get("entreprise")
        client.type_client = request.form.get("type_client")

        db.session.commit()

        return redirect(url_for("client.liste_clients"))

    return render_template(
        "clients/modifier.html",
        client=client
    )


# ==========================
# SUPPRIMER CLIENT
# ==========================

@client_bp.route("/clients/supprimer/<int:id>")
def supprimer_client(id):

    client = Client.query.get_or_404(id)

    db.session.delete(client)
    db.session.commit()

    return redirect(url_for("client.liste_clients"))


# ==========================
# DETAILS CLIENT
# ==========================

@client_bp.route("/clients/<int:id>")
def voir_client(id):

    client = Client.query.get_or_404(id)

    return render_template(
        "clients/voir.html",
        client=client
    )
