"""
app.py — Main application entry point.
Khởi tạo Flask app, đăng ký blueprints, kết nối MongoDB.
"""
import os
import logging
from flask import Flask, render_template
from pymongo import MongoClient
from config import config
from extensions import login_manager, bcrypt, csrf


def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Đảm bảo thư mục upload tồn tại
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Khởi tạo extensions với app ───────────────────────────────────────────
    bcrypt.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # ── Kết nối MongoDB ────────────────────────────────────────────────────────
    mongo_client = MongoClient(app.config["MONGO_URI"])
    app.db = mongo_client.get_database()

    # ── Logging cơ bản ─────────────────────────────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # ── Đăng ký Blueprints ────────────────────────────────────────────────────
    from controllers.auth_controller import auth_bp
    from controllers.dashboard_controller import dashboard_bp
    from controllers.product_controller import product_bp
    from controllers.customer_controller import customer_bp
    from controllers.order_controller import order_bp
    from controllers.forecast_controller import forecast_bp

    app.register_blueprint(auth_bp,       url_prefix="/auth")
    app.register_blueprint(dashboard_bp,  url_prefix="/")
    app.register_blueprint(product_bp,    url_prefix="/products")
    app.register_blueprint(customer_bp,   url_prefix="/customers")
    app.register_blueprint(order_bp,      url_prefix="/orders")
    app.register_blueprint(forecast_bp,   url_prefix="/forecast")

    # ── Error handlers ─────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"Server error: {e}")
        return render_template("errors/500.html"), 500

    # ── User loader cho Flask-Login ────────────────────────────────────────────
    from models.user_model import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(app.db, user_id)

    return app


app = create_app()

if __name__ == "__main__":
    # Seed sample data nếu DB còn trống
    from services.seed_service import seed_data
    with app.app_context():
        seed_data(app.db)
    app.run(debug=True, port=5000)
