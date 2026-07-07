from flask import Blueprint, render_template, request, redirect, url_for

from app.models import db, Fournisseur

fournisseur_bp = Blueprint(
    "fournisseur",
    __name__
)


# ==========================
# LISTE
# ==========================

@fournisseur_bp.route("/fournisseurs")
def liste_fournisseurs():

    fournisseurs = Fournisseur.query.order_by(
        Fournisseur.id.desc()
    ).all()

    return render_template(
        "fournisseurs/liste.html",
        fournisseurs=fournisseurs
    )


# ==========================
# AJOUT
# ==========================

@fournisseur_bp.route(
    "/fournisseurs/ajouter",
    methods=["GET", "POST"]
)
def ajouter_fournisseur():

    if request.method == "POST":

        fournisseur = Fournisseur(

            nom=request.form["nom"],
            telephone=request.form.get("telephone"),
            email=request.form.get("email"),
            adresse=request.form.get("adresse")

        )

        db.session.add(fournisseur)
        db.session.commit()

        return redirect(
            url_for("fournisseur.liste_fournisseurs")
        )

    return render_template(
        "fournisseurs/ajouter.html"
    )


# ==========================
# MODIFIER
# ==========================

@fournisseur_bp.route(
    "/fournisseurs/modifier/<int:id>",
    methods=["GET", "POST"]
)
def modifier_fournisseur(id):

    fournisseur = Fournisseur.query.get_or_404(id)

    if request.method == "POST":

        fournisseur.nom = request.form["nom"]
        fournisseur.telephone = request.form.get("telephone")
        fournisseur.email = request.form.get("email")
        fournisseur.adresse = request.form.get("adresse")

        db.session.commit()

        return redirect(
            url_for("fournisseur.liste_fournisseurs")
        )

    return render_template(
        "fournisseurs/modifier.html",
        fournisseur=fournisseur
    )


# ==========================
# SUPPRIMER
# ==========================

@fournisseur_bp.route(
    "/fournisseurs/supprimer/<int:id>"
)
def supprimer_fournisseur(id):

    fournisseur = Fournisseur.query.get_or_404(id)

    db.session.delete(fournisseur)
    db.session.commit()

    return redirect(
        url_for("fournisseur.liste_fournisseurs")
    )


# ==========================
# DETAILS
# ==========================

@fournisseur_bp.route("/fournisseurs/<int:id>")
def voir_fournisseur(id):

    fournisseur = Fournisseur.query.get_or_404(id)

    return render_template(
        "fournisseurs/voir.html",
        fournisseur=fournisseur
   
