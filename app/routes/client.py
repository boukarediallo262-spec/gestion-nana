from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from flask_login import (
    login_required,
)

from sqlalchemy import or_

from app import db
from app.models import Client


client_bp = Blueprint(
    "client",
    __name__,
    url_prefix="/clients",
)


# ==========================================================
# LISTE DES CLIENTS
# ==========================================================

@client_bp.route("/")
@login_required
def liste_clients():

    recherche = request.args.get("q", "").strip()

    if recherche:

        clients = (
            Client.query.filter(
                or_(
                    Client.nom.ilike(f"%{recherche}%"),
                    Client.prenom.ilike(f"%{recherche}%"),
                    Client.telephone.ilike(f"%{recherche}%"),
                )
            )
            .order_by(Client.nom.asc())
            .all()
        )

    else:

        clients = (
            Client.query
            .order_by(Client.nom.asc())
            .all()
        )

    return render_template(
        "clients/index.html",
        clients=clients,
        recherche=recherche,
    )


# ==========================================================
# AJOUTER UN CLIENT
# ==========================================================

@client_bp.route("/ajouter", methods=["GET", "POST"])
@login_required
def ajouter_client():

    if request.method == "POST":

        client = Client(
            nom=request.form.get("nom"),
            prenom=request.form.get("prenom"),
            telephone=request.form.get("telephone"),
            email=request.form.get("email"),
            adresse=request.form.get("adresse"),
            ville=request.form.get("ville"),
            pays=request.form.get("pays") or "Burkina Faso",
            entreprise=request.form.get("entreprise"),
            type_client=request.form.get("type_client") or "Particulier",
            actif=True,
        )

        db.session.add(client)
        db.session.commit()

        flash(
            "Client ajouté avec succès.",
            "success",
        )

        return redirect(
            url_for("client.liste_clients")
        )

    return render_template(
        "clients/ajouter.html"
    )


# ==========================================================
# MODIFIER UN CLIENT
# ==========================================================

@client_bp.route("/modifier/<int:id>", methods=["GET", "POST"])
@login_required
def modifier_client(id):

    client = Client.query.get_or_404(id)

    if request.method == "POST":

        client.nom = request.form.get("nom")
        client.prenom = request.form.get("prenom")
        client.telephone = request.form.get("telephone")
        client.email = request.form.get("email")
        client.adresse = request.form.get("adresse")
        client.ville = request.form.get("ville")
        client.pays = request.form.get("pays")
        client.entreprise = request.form.get("entreprise")
        client.type_client = request.form.get("type_client")
        client.actif = (
            request.form.get("actif") == "on"
        )

        db.session.commit()

        flash(
            "Client modifié avec succès.",
            "success",
        )

        return redirect(
            url_for("client.liste_clients")
        )

    return render_template(
        "clients/modifier.html",
        client=client,
    )


# ==========================================================
# SUPPRIMER UN CLIENT
# ==========================================================

@client_bp.route("/supprimer/<int:id>", methods=["POST"])
@login_required
def supprimer_client(id):

    client = Client.query.get_or_404(id)

    db.session.delete(client)
    db.session.commit()

    flash(
        "Client supprimé.",
        "success",
    )

    return redirect(
        url_for("client.liste_clients")
    )
