"""Dashboard blueprint."""
from flask import Blueprint, render_template, current_app
from flask_login import login_required
from services.stats_service import get_dashboard_stats

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    db = current_app.db
    stats = get_dashboard_stats(db)
    return render_template("dashboard/index.html", stats=stats)
