"""Revenue forecasting blueprint - NÂNG CẤP 9+"""
from flask import Blueprint, render_template, current_app, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from bson import ObjectId
from bson.errors import InvalidId
from services.forecast_service import ForecastService
from services.export_service import build_pdf_report, build_excel_report, _slugify_filename

forecast_bp = Blueprint("forecast", __name__)


@forecast_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if not current_user.is_admin:
        flash("Chức năng Dự báo AI chỉ dành cho Admin.", "danger")
        return redirect(url_for("dashboard.index"))

    db = current_app.db
    service = ForecastService(db)

    try:
        months_ahead = int(request.form.get("months_ahead") or request.args.get("months_ahead", 3))
        months_ahead = max(1, min(12, months_ahead))
    except (ValueError, TypeError):
        months_ahead = 3

    model_type = request.form.get("model_type") or request.args.get("model_type", "linear")
    if model_type not in ("linear", "random_forest"):
        model_type = "linear"
    # Lưu ý: tab "Tổng doanh thu" vẫn cho chọn riêng Linear/RF (model_comparison
    # đã tự so sánh R² hai mô hình bên dưới biểu đồ). Chế độ "auto" dành cho
    # dự báo theo sản phẩm ở route /product bên dưới.

    # Tab hiện tại
    active_tab = request.args.get("tab", "total")

    # Dự báo tổng
    result = service.run_forecast(months_ahead=months_ahead, model_type=model_type)

    # Danh sách sản phẩm để chọn
    product_list = service.get_product_list()

    # Cảnh báo tồn kho
    inventory = service.get_inventory_alerts()

    # Lịch sử độ chính xác
    accuracy_history = service.model_accuracy_history()

    return render_template(
        "forecast/index.html",
        forecast=result,
        product_list=product_list,
        inventory=inventory,
        accuracy_history=accuracy_history,
        active_tab=active_tab,
    )


@forecast_bp.route("/product", methods=["GET", "POST"])
@login_required
def product_forecast():
    """AJAX hoặc page: dự báo theo sản phẩm."""
    if not current_user.is_admin:
        return jsonify({"error": "Không có quyền"}), 403

    db = current_app.db
    service = ForecastService(db)

    product_id = request.form.get("product_id") or request.args.get("product_id", "")
    try:
        months_ahead = int(request.form.get("months_ahead") or request.args.get("months_ahead", 3))
        months_ahead = max(1, min(12, months_ahead))
    except (ValueError, TypeError):
        months_ahead = 3

    model_type = request.form.get("model_type") or request.args.get("model_type", "auto")
    if model_type not in ("linear", "random_forest", "auto"):
        model_type = "auto"

    if not product_id:
        return jsonify({"error": "Chưa chọn sản phẩm"}), 400

    result = service.forecast_product(product_id, months_ahead, model_type)

    # Walk-forward validation — đo sai số trên dữ liệu mô hình CHƯA từng
    # thấy lúc train (khác R² ở forecast_product, là độ khớp in-sample).
    result["walk_forward"] = service.product_accuracy_history(product_id)

    return jsonify(result)


@forecast_bp.route("/compare", methods=["POST"])
@login_required
def compare_products():
    """So sánh nhiều sản phẩm."""
    if not current_user.is_admin:
        return jsonify({"error": "Không có quyền"}), 403

    db = current_app.db
    service = ForecastService(db)

    product_ids = request.json.get("product_ids", [])
    months_ahead = int(request.json.get("months_ahead", 3))
    model_type = request.json.get("model_type", "auto")
    if model_type not in ("linear", "random_forest", "auto"):
        model_type = "auto"
    results = service.compare_products(product_ids, months_ahead, model_type)
    return jsonify(results)


def _resolve_export_forecast(service, db):
    """Dùng chung cho 2 route export: đọc query string, chạy lại đúng
    forecast tương ứng (total hoặc product), trả về (scope, forecast, product_name, filename_base)."""
    scope = request.args.get("scope", "total")
    if scope not in ("total", "product"):
        scope = "total"

    try:
        months_ahead = int(request.args.get("months_ahead", 3))
        months_ahead = max(1, min(12, months_ahead))
    except (ValueError, TypeError):
        months_ahead = 3

    if scope == "product":
        product_id = request.args.get("product_id", "")
        model_type = request.args.get("model_type", "auto")
        if model_type not in ("linear", "random_forest", "auto"):
            model_type = "auto"
        if not product_id:
            return None, None, None, None

        forecast = service.forecast_product(product_id, months_ahead, model_type)

        product_name = "San_pham"
        try:
            prod = db.products.find_one({"_id": ObjectId(product_id)})
            if prod:
                product_name = prod.get("name", product_name)
        except InvalidId:
            pass

        filename_base = f"du_bao_{_slugify_filename(product_name)}"
        return scope, forecast, product_name, filename_base

    model_type = request.args.get("model_type", "linear")
    if model_type not in ("linear", "random_forest"):
        model_type = "linear"
    forecast = service.run_forecast(months_ahead=months_ahead, model_type=model_type)
    return scope, forecast, None, "du_bao_doanh_thu_tong"


@forecast_bp.route("/export/pdf", methods=["GET"])
@login_required
def export_pdf():
    if not current_user.is_admin:
        flash("Chức năng Dự báo AI chỉ dành cho Admin.", "danger")
        return redirect(url_for("dashboard.index"))

    db = current_app.db
    service = ForecastService(db)

    scope, forecast, product_name, filename_base = _resolve_export_forecast(service, db)
    if scope is None:
        flash("Chưa chọn sản phẩm để xuất báo cáo.", "warning")
        return redirect(url_for("forecast.index", tab="product"))

    pdf_buf = build_pdf_report(scope, forecast, product_name=product_name)
    return send_file(
        pdf_buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{filename_base}.pdf",
    )


@forecast_bp.route("/export/excel", methods=["GET"])
@login_required
def export_excel():
    if not current_user.is_admin:
        flash("Chức năng Dự báo AI chỉ dành cho Admin.", "danger")
        return redirect(url_for("dashboard.index"))

    db = current_app.db
    service = ForecastService(db)

    scope, forecast, product_name, filename_base = _resolve_export_forecast(service, db)
    if scope is None:
        flash("Chưa chọn sản phẩm để xuất báo cáo.", "warning")
        return redirect(url_for("forecast.index", tab="product"))

    excel_buf = build_excel_report(scope, forecast, product_name=product_name)
    return send_file(
        excel_buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"{filename_base}.xlsx",
    )