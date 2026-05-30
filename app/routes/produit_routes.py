from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import db, Produit

produit_bp = Blueprint('produit', __name__)

# LISTE PRODUITS
@produit_bp.route('/produits')
def produits():

    produits = Produit.query.all()

    return render_template(
        'produits.html',
        produits=produits
    )


# AJOUT PRODUIT
@produit_bp.route('/ajouter_produit', methods=['GET', 'POST'])
def ajouter_produit():

    if request.method == 'POST':

        nom = request.form.get('nom')
        prix = request.form.get('prix')
        quantite = request.form.get('quantite')

        nouveau_produit = Produit(
            nom=nom,
            prix=prix,
            quantite=quantite
        )

        db.session.add(nouveau_produit)
        db.session.commit()

        flash("Produit ajouté avec succès", "success")

        return redirect(url_for('produit.produits'))

    return render_template('ajouter_produit.html')


# MODIFIER PRODUIT
@produit_bp.route('/modifier_produit/<int:id>', methods=['GET', 'POST'])
def modifier_produit(id):

    produit = Produit.query.get_or_404(id)

    if request.method == 'POST':

        produit.nom = request.form.get('nom')
        produit.prix = request.form.get('prix')
        produit.quantite = request.form.get('quantite')

        db.session.commit()

        flash("Produit modifié avec succès", "info")

        return redirect(url_for('produit.produits'))

    return render_template(
        'modifier_produit.html',
        produit=produit
    )


# SUPPRIMER PRODUIT
@produit_bp.route('/supprimer_produit/<int:id>')
def supprimer_produit(id):

    produit = Produit.query.get_or_404(id)

    db.session.delete(produit)
    db.session.commit()

    flash("Produit supprimé", "danger")

    return redirect(url_for('produit.produits'))
