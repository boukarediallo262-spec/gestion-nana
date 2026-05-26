from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import db, Facture, Produit

facture_bp = Blueprint('facture', __name__)


# LISTE FACTURES
@facture_bp.route('/factures')
def factures():

    factures = Facture.query.all()

    return render_template(
        'factures.html',
        factures=factures
    )


# AJOUT FACTURE
@facture_bp.route('/ajouter_facture', methods=['GET', 'POST'])
def ajouter_facture():

    produits = Produit.query.all()

    if request.method == 'POST':

        client = request.form.get('client')
        produit_id = request.form.get('produit_id')
        quantite = int(request.form.get('quantite'))

        produit = Produit.query.get(produit_id)

        total = produit.prix * quantite

        nouvelle_facture = Facture(
            client=client,
            produit=produit.nom,
            quantite=quantite,
            total=total
        )

        produit.stock -= quantite

        db.session.add(nouvelle_facture)

        db.session.commit()

        flash("Facture ajoutée avec succès", "success")

        return redirect(url_for('facture.factures'))

    return render_template(
        'ajouter_facture.html',
        produits=produits
    )


# DETAIL FACTURE
@facture_bp.route('/facture/<int:id>')
def voir_facture(id):

    facture = Facture.query.get_or_404(id)

    return render_template(
        'voir_facture.html',
        facture=facture
    )


# SUPPRIMER FACTURE
@facture_bp.route('/supprimer_facture/<int:id>')
def supprimer_facture(id):

    facture = Facture.query.get_or_404(id)

    db.session.delete(facture)

    db.session.commit()

    flash("Facture supprimée", "danger")

    return redirect(url_for('facture.factures'))
