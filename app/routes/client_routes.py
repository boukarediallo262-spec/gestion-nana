from flask import Blueprint, render_template, request, redirect, url_for
from app.models.models import db, Client

client_bp = Blueprint('client', __name__)


# =========================
# LISTE CLIENTS
# =========================
@client_bp.route("/clients")
def clients():

    recherche = request.args.get("recherche", "")

    if recherche:
        clients = Client.query.filter(
            Client.nom.contains(recherche)
        ).all()
    else:
        clients = Client.query.all()

    total_clients = Client.query.count()

    return render_template(
        "clients.html",
        clients=clients,
        total_clients=total_clients
    )


# =========================
# AJOUT CLIENT
# =========================
@client_bp.route("/ajouter-client", methods=["GET", "POST"])
def ajouter_client():

    if request.method == "POST":

        nom = request.form["nom"]
        telephone = request.form["telephone"]

        nouveau_client = Client(
            nom=nom,
            telephone=telephone
        )

        db.session.add(nouveau_client)
        db.session.commit()

        return redirect(url_for("client.clients"))

    return render_template("ajouter_client.html")


# =========================
# MODIFIER CLIENT
# =========================
@client_bp.route("/modifier-client/<int:id>", methods=["GET", "POST"])
def modifier_client(id):

    client = Client.query.get_or_404(id)

    if request.method == "POST":

        client.nom = request.form["nom"]
        client.telephone = request.form["telephone"]

        db.session.commit()

        return redirect(url_for("client.clients"))

    return render_template(
        "modifier_client.html",
        client=client
    )


# =========================
# SUPPRIMER CLIENT
# =========================
@client_bp.route("/supprimer-client/<int:id>")
def supprimer_client(id):

    client = Client.query.get_or_404(id)

    db.session.delete(client)
    db.session.commit()

    return redirect(url_for("client.clients"))
