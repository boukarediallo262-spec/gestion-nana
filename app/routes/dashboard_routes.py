from flask import Blueprint, render_template

dashboard_bp = Blueprint("dashboard", __name__)


# =========================
# HOME
# =========================
@dashboard_bp.route("/")
def home():
    return render_template("dashboard/index.html")
