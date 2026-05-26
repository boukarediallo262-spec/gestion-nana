from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.models import db, Depense

depense_bp = Blueprint('depense', __name__)


# LISTE DEPENSES
@depense_bp.route('/depenses')
def depenses():

    depenses = Depense.query.all()

    total_depenses = sum(depense.montant for depense in depenses)

    return render_template(
        'depenses.html',
        depenses=depenses,
        total_depenses=total_depenses
    )


# AJOUT DEPENSE
@depense_bp.route('/ajouter_depense', methods=['GET', 'POST'])
def ajouter_depense():

    if request.method == 'POST':

        nom = request.form.get('nom')
        montant = request.form.get('montant')

        nouvelle_depense = Depense(
            nom=nom,
            montant=montant
        )

        db.session.add(nouvelle_depense)

        db.session.commit()

        flash("Dépense ajoutée avec succès", "success")

        return redirect(url_for('depense.depenses'))

    return render_template('ajouter_depense.html')


# SUPPRIMER DEPENSE
@depense_bp.route('/supprimer_depense/<int:id>')
def supprimer_depense(id):

    depense = Depense.query.get_or_404(id)

    db.session.delete(depense)

    db.session.commit()

    flash("Dépense supprimée", "danger")

    return redirect(url_for('depense.depenses'))
