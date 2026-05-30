from flask import Blueprint, render_template, request, redirect, url_for
from app.models.models import db, Facture


facture_bp = Blueprint('facture', __name__)

# ==============================
# LISTE DES FACTURES
# ==============================
@facture_bp.route('/factures')
def factures():

    factures = Facture.query.order_by(Facture.id.desc()).all()

    return render_template(
        'factures.html',
        factures=factures
    )


# ==============================
# AJOUT FACTURE
# ==============================
@facture_bp.route('/ajouter_facture', methods=['GET', 'POST'])
def ajouter_facture():

    if request.method == 'POST':

        client = request.form.get('client')
        montant = request.form.get('montant')

        nouvelle_facture = Facture(
            client=client,
            montant=montant
        )

        db.session.add(nouvelle_facture)
        db.session.commit()

        return redirect(url_for('facture.factures'))

    return render_template('ajouter_facture.html')
#===============================
# SUPPRIMER FACTURE
# ==============================
@facture_bp.route('/supprimer_facture/<int:id>')
def supprimer_facture(id):

    facture = Facture.query.get_or_404(id)

    db.session.delete(facture)
    db.session.commit()

    return redirect(url_for('facture.factures'))
