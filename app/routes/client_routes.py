from flask import Blueprint, render_template, request, redirect, url_for
from app.models.models import db, Client

client_bp = Blueprint('client', __name__)

# ==============================
# LISTE DES CLIENTS
# ==============================
@client_bp.route('/clients')
def clients():

    clients = Client.query.order_by(Client.id.desc()).all()

    return render_template(
        'clients.html',
        clients=clients
    )


# ==============================
# AJOUT CLIENT
# ==============================
@client_bp.route('/ajouter_client', methods=['GET', 'POST'])
def ajouter_client():

    if request.method == 'POST':

        nom = request.form.get('nom')
        telephone = request.form.get('telephone')
        adresse = request.form.get('adresse')

        nouveau_client = Client(
            nom=nom,
            telephone=telephone,
            adresse=adresse
        )

        db.session.add(nouveau_client)
        db.session.commit()

        return redirect(url_for('client.clients'))

    return render_template('ajouter_client.html')


# ==============================
# SUPPRIMER CLIENT
# ==============================
@client_bp.route('/supprimer_client/<int:id>')
def supprimer_client(id):

    client = Client.query.get_or_404(id)

    db.session.delete(client)
    db.session.commit()

    return redirect(url_for('client.clients'))
