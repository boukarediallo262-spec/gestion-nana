from flask import Blueprint, render_template, redirect, url_for
from app.models.models import Produit, db

stock_bp = Blueprint('stock', __name__)

# ==============================
# PAGE STOCK
# ==============================
@stock_bp.route('/stock')
def stock():

    produits = Produit.query.order_by(Produit.id.desc()).all()

    total_stock = 0

    for produit in produits:
        total_stock += produit.quantite

    return render_template(
        'stock.html',
        produits=produits,
        total_stock=total_stock
    )


# ==============================
# SUPPRIMER PRODUIT
# ==============================
@stock_bp.route('/supprimer_stock/<int:id>')
def supprimer_stock(id):

    produit = Produit.query.get_or_404(id)

    db.session.delete(produit)
    db.session.commit()

    return redirect(url_for('stock.stock'))
