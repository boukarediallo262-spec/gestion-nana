from flask import Blueprint, render_template, request, redirect, url_for
from app.models.models import db, Depense

depense_bp = Blueprint('depense', __name__)

# ==============================
# LISTE DES DEPENSES
# ==============================
@depense_bp.route('/depenses')
def depenses():

    depenses = Depense.query.order_by(Depense.id.desc()).all()

    total = sum(depense.montant for depense in depenses)

    return render_template(
        'depenses.html',
        depenses=depenses,
        total=total
    )


# ==============================
# AJOUT DEPENSE
# ==============================
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

        return redirect(url_for('depense.depenses'))

    return render_template('ajouter_depense.html')


# ==============================
# SUPPRIMER DEPENSE
# ==============================
@depense_bp.route('/supprimer_depense/<int:id>')
def supprimer_depense(id):

    depense = Depense.query.get_or_404(id)

    db.session.delete(depense)
    db.session.commit()

    return redirect(url_for('depense.depenses'))
