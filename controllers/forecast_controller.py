"""Revenue forecasting blueprint."""
from flask import Blueprint, render_template, current_app, request
from flask_login import login_required
from services.forecast_service import ForecastService

forecast_bp = Blueprint("forecast", __name__)


@forecast_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    db = current_app.db
    # Lấy số tháng từ form (POST) hoặc query string (GET), mặc định 3
    try:
        months_ahead = int(request.form.get("months_ahead") or request.args.get("months_ahead", 3))
        months_ahead = max(1, min(12, months_ahead))  # Giới hạn 1-12
    except (ValueError, TypeError):
        months_ahead = 3

    service = ForecastService(db)
    result = service.run_forecast(months_ahead=months_ahead)
    return render_template("forecast/index.html", forecast=result)