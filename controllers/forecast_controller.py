"""Revenue forecasting blueprint."""
from flask import Blueprint, render_template, current_app, request, flash, redirect, url_for
from flask_login import login_required, current_user
from services.forecast_service import ForecastService

forecast_bp = Blueprint("forecast", __name__)


@forecast_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    # Chỉ admin mới được dùng chức năng dự đoán AI
    if not current_user.is_admin:
        flash("Chức năng Dự báo AI chỉ dành cho Admin.", "danger")
        return redirect(url_for("dashboard.index"))

    db = current_app.db
    try:
        months_ahead = int(request.form.get("months_ahead") or request.args.get("months_ahead", 3))
        months_ahead = max(1, min(12, months_ahead))
    except (ValueError, TypeError):
        months_ahead = 3

    service = ForecastService(db)
    result = service.run_forecast(months_ahead=months_ahead)
    return render_template("forecast/index.html", forecast=result)
