#!/usr/bin/env python3
"""
Master script to generate the entire Sales Management System project.
Run: python generate_project.py
"""

import os
import stat

BASE = "/home/claude/sales_system"

files = {}

# ─────────────────────────────────────────────
# requirements.txt
# ─────────────────────────────────────────────
files["requirements.txt"] = """Flask==3.0.0
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-Bcrypt==1.0.1
pymongo==4.6.1
pandas==2.1.4
numpy==1.26.3
scikit-learn==1.4.0
matplotlib==3.8.2
Werkzeug==3.0.1
WTForms==3.1.2
python-dotenv==1.0.0
"""

# ─────────────────────────────────────────────
# config.py
# ─────────────────────────────────────────────
files["config.py"] = '''import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "super-secret-key-change-in-prod-2024")
    WTF_CSRF_ENABLED = True
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/sales_db")
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB upload limit
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "images", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
'''

# ─────────────────────────────────────────────
# app.py
# ─────────────────────────────────────────────
files["app.py"] = '''"""
Main application entry point.
Initializes Flask app, registers blueprints, and sets up extensions.
"""
import os
import logging
from flask import Flask, render_template
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from pymongo import MongoClient
from config import config

# ── Extensions (initialized without app) ──────────────────────────────────────
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
mongo_client = None
db = None

def create_app(config_name="default"):
    global mongo_client, db

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Ensure upload folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # ── Init extensions ────────────────────────────────────────────────────────
    bcrypt.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Vui lòng đăng nhập để tiếp tục."
    login_manager.login_message_category = "warning"

    # ── MongoDB connection ─────────────────────────────────────────────────────
    mongo_client = MongoClient(app.config["MONGO_URI"])
    db = mongo_client.get_database()
    app.db = db

    # ── Logging ────────────────────────────────────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # ── Register blueprints ────────────────────────────────────────────────────
    from controllers.auth_controller import auth_bp
    from controllers.dashboard_controller import dashboard_bp
    from controllers.product_controller import product_bp
    from controllers.customer_controller import customer_bp
    from controllers.order_controller import order_bp
    from controllers.forecast_controller import forecast_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/")
    app.register_blueprint(product_bp, url_prefix="/products")
    app.register_blueprint(customer_bp, url_prefix="/customers")
    app.register_blueprint(order_bp, url_prefix="/orders")
    app.register_blueprint(forecast_bp, url_prefix="/forecast")

    # ── Error handlers ─────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f"Server error: {e}")
        return render_template("errors/500.html"), 500

    # ── User loader for Flask-Login ────────────────────────────────────────────
    from models.user_model import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(db, user_id)

    return app


app = create_app()

if __name__ == "__main__":
    # Seed sample data on first run
    from services.seed_service import seed_data
    with app.app_context():
        seed_data(app.db)
    app.run(debug=True, port=5000)
'''

# ─────────────────────────────────────────────
# models/user_model.py
# ─────────────────────────────────────────────
files["models/__init__.py"] = ""
files["models/user_model.py"] = '''"""User model with Flask-Login integration."""
from flask_login import UserMixin
from bson import ObjectId
from datetime import datetime


class User(UserMixin):
    def __init__(self, data: dict):
        self._id = data.get("_id")
        self.username = data.get("username")
        self.email = data.get("email")
        self.password_hash = data.get("password_hash")
        self.role = data.get("role", "staff")  # admin | staff
        self.full_name = data.get("full_name", "")
        self.created_at = data.get("created_at", datetime.utcnow())

    def get_id(self):
        return str(self._id)

    @property
    def is_admin(self):
        return self.role == "admin"

    # ── Class methods ──────────────────────────────────────────────────────────
    @classmethod
    def get_by_id(cls, db, user_id):
        try:
            data = db.users.find_one({"_id": ObjectId(user_id)})
            return cls(data) if data else None
        except Exception:
            return None

    @classmethod
    def get_by_username(cls, db, username):
        data = db.users.find_one({"username": username})
        return cls(data) if data else None

    @classmethod
    def get_by_email(cls, db, email):
        data = db.users.find_one({"email": email})
        return cls(data) if data else None

    @classmethod
    def create(cls, db, username, email, password_hash, role="staff", full_name=""):
        doc = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "full_name": full_name,
            "created_at": datetime.utcnow(),
        }
        result = db.users.insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls(doc)

    @classmethod
    def get_all(cls, db):
        return [cls(u) for u in db.users.find()]
'''

# ─────────────────────────────────────────────
# models/product_model.py
# ─────────────────────────────────────────────
files["models/product_model.py"] = '''"""Product model."""
from bson import ObjectId
from datetime import datetime


class Product:
    def __init__(self, data: dict):
        self._id = data.get("_id")
        self.name = data.get("name", "")
        self.category = data.get("category", "")
        self.price = data.get("price", 0)
        self.stock = data.get("stock", 0)
        self.description = data.get("description", "")
        self.image = data.get("image", "default_product.png")
        self.created_at = data.get("created_at", datetime.utcnow())
        self.updated_at = data.get("updated_at", datetime.utcnow())

    def to_dict(self):
        return {
            "_id": self._id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "stock": self.stock,
            "description": self.description,
            "image": self.image,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def get_all(cls, db, search=None, category=None):
        query = {}
        if search:
            query["name"] = {"$regex": search, "$options": "i"}
        if category:
            query["category"] = category
        return [cls(p) for p in db.products.find(query).sort("created_at", -1)]

    @classmethod
    def get_by_id(cls, db, product_id):
        try:
            data = db.products.find_one({"_id": ObjectId(product_id)})
            return cls(data) if data else None
        except Exception:
            return None

    @classmethod
    def create(cls, db, name, category, price, stock, description="", image="default_product.png"):
        doc = {
            "name": name,
            "category": category,
            "price": float(price),
            "stock": int(stock),
            "description": description,
            "image": image,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = db.products.insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls(doc)

    @classmethod
    def update(cls, db, product_id, **kwargs):
        kwargs["updated_at"] = datetime.utcnow()
        db.products.update_one({"_id": ObjectId(product_id)}, {"$set": kwargs})

    @classmethod
    def delete(cls, db, product_id):
        db.products.delete_one({"_id": ObjectId(product_id)})

    @classmethod
    def get_categories(cls, db):
        return db.products.distinct("category")

    @classmethod
    def decrement_stock(cls, db, product_id, quantity):
        db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$inc": {"stock": -quantity}, "$set": {"updated_at": datetime.utcnow()}},
        )
'''

# ─────────────────────────────────────────────
# models/customer_model.py
# ─────────────────────────────────────────────
files["models/customer_model.py"] = '''"""Customer model."""
from bson import ObjectId
from datetime import datetime


class Customer:
    def __init__(self, data: dict):
        self._id = data.get("_id")
        self.name = data.get("name", "")
        self.email = data.get("email", "")
        self.phone = data.get("phone", "")
        self.address = data.get("address", "")
        self.total_spent = data.get("total_spent", 0)
        self.created_at = data.get("created_at", datetime.utcnow())

    @classmethod
    def get_all(cls, db, search=None):
        query = {}
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}},
            ]
        return [cls(c) for c in db.customers.find(query).sort("total_spent", -1)]

    @classmethod
    def get_by_id(cls, db, customer_id):
        try:
            data = db.customers.find_one({"_id": ObjectId(customer_id)})
            return cls(data) if data else None
        except Exception:
            return None

    @classmethod
    def create(cls, db, name, email, phone, address=""):
        doc = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "total_spent": 0,
            "created_at": datetime.utcnow(),
        }
        result = db.customers.insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls(doc)

    @classmethod
    def update(cls, db, customer_id, **kwargs):
        db.customers.update_one({"_id": ObjectId(customer_id)}, {"$set": kwargs})

    @classmethod
    def delete(cls, db, customer_id):
        db.customers.delete_one({"_id": ObjectId(customer_id)})

    @classmethod
    def add_spent(cls, db, customer_id, amount):
        db.customers.update_one(
            {"_id": ObjectId(customer_id)},
            {"$inc": {"total_spent": amount}},
        )
'''

# ─────────────────────────────────────────────
# models/order_model.py
# ─────────────────────────────────────────────
files["models/order_model.py"] = '''"""Order (invoice) model."""
from bson import ObjectId
from datetime import datetime


class Order:
    def __init__(self, data: dict):
        self._id = data.get("_id")
        self.order_code = data.get("order_code", "")
        self.customer_id = data.get("customer_id")
        self.customer_name = data.get("customer_name", "")
        self.items = data.get("items", [])  # [{product_id, name, price, qty, subtotal}]
        self.total = data.get("total", 0)
        self.status = data.get("status", "paid")
        self.note = data.get("note", "")
        self.created_at = data.get("created_at", datetime.utcnow())
        self.created_by = data.get("created_by", "")

    @classmethod
    def get_all(cls, db, start=None, end=None, customer_id=None):
        query = {}
        if start or end:
            query["created_at"] = {}
            if start:
                query["created_at"]["$gte"] = start
            if end:
                query["created_at"]["$lte"] = end
        if customer_id:
            query["customer_id"] = ObjectId(customer_id)
        return [cls(o) for o in db.orders.find(query).sort("created_at", -1)]

    @classmethod
    def get_by_id(cls, db, order_id):
        try:
            data = db.orders.find_one({"_id": ObjectId(order_id)})
            return cls(data) if data else None
        except Exception:
            return None

    @classmethod
    def create(cls, db, customer_id, customer_name, items, total, note="", created_by=""):
        # Generate order code
        count = db.orders.count_documents({})
        order_code = f"HD{datetime.utcnow().strftime(\'%Y%m\')}{count+1:04d}"
        doc = {
            "order_code": order_code,
            "customer_id": ObjectId(customer_id) if customer_id else None,
            "customer_name": customer_name,
            "items": items,
            "total": float(total),
            "status": "paid",
            "note": note,
            "created_at": datetime.utcnow(),
            "created_by": created_by,
        }
        result = db.orders.insert_one(doc)
        doc["_id"] = result.inserted_id
        return cls(doc)

    @classmethod
    def monthly_revenue(cls, db):
        """Aggregate revenue by month for the past 12 months."""
        pipeline = [
            {"$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"},
                },
                "revenue": {"$sum": "$total"},
                "count": {"$sum": 1},
            }},
            {"$sort": {"_id.year": 1, "_id.month": 1}},
            {"$limit": 24},
        ]
        return list(db.orders.aggregate(pipeline))

    @classmethod
    def top_products(cls, db, limit=5):
        pipeline = [
            {"$unwind": "$items"},
            {"$group": {
                "_id": "$items.product_id",
                "name": {"$first": "$items.name"},
                "total_qty": {"$sum": "$items.qty"},
                "total_revenue": {"$sum": "$items.subtotal"},
            }},
            {"$sort": {"total_qty": -1}},
            {"$limit": limit},
        ]
        return list(db.orders.aggregate(pipeline))

    @classmethod
    def top_customers(cls, db, limit=5):
        pipeline = [
            {"$group": {
                "_id": "$customer_id",
                "name": {"$first": "$customer_name"},
                "total_orders": {"$sum": 1},
                "total_spent": {"$sum": "$total"},
            }},
            {"$sort": {"total_spent": -1}},
            {"$limit": limit},
        ]
        return list(db.orders.aggregate(pipeline))
'''

# ─────────────────────────────────────────────
# controllers/__init__.py
# ─────────────────────────────────────────────
files["controllers/__init__.py"] = ""

# ─────────────────────────────────────────────
# controllers/auth_controller.py
# ─────────────────────────────────────────────
files["controllers/auth_controller.py"] = '''"""Authentication blueprint: login, register, logout."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.user_model import User
from app import bcrypt

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        if not username or not password:
            flash("Vui lòng điền đầy đủ thông tin.", "danger")
            return render_template("auth/login.html")

        db = current_app.db
        user = User.get_by_username(db, username)

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            flash(f"Chào mừng {user.full_name or user.username}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))

        flash("Tên đăng nhập hoặc mật khẩu không đúng.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        db = current_app.db
        errors = []

        if not all([username, email, password, confirm]):
            errors.append("Vui lòng điền đầy đủ thông tin.")
        if password != confirm:
            errors.append("Mật khẩu xác nhận không khớp.")
        if len(password) < 6:
            errors.append("Mật khẩu phải có ít nhất 6 ký tự.")
        if User.get_by_username(db, username):
            errors.append("Tên đăng nhập đã tồn tại.")
        if User.get_by_email(db, email):
            errors.append("Email đã được sử dụng.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/register.html")

        password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        # First user becomes admin
        role = "admin" if db.users.count_documents({}) == 0 else "staff"
        User.create(db, username, email, password_hash, role, full_name)
        flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Đã đăng xuất.", "info")
    return redirect(url_for("auth.login"))
'''

# ─────────────────────────────────────────────
# controllers/dashboard_controller.py
# ─────────────────────────────────────────────
files["controllers/dashboard_controller.py"] = '''"""Dashboard blueprint."""
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
'''

# ─────────────────────────────────────────────
# controllers/product_controller.py
# ─────────────────────────────────────────────
files["controllers/product_controller.py"] = '''"""Product CRUD blueprint."""
import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models.product_model import Product

product_bp = Blueprint("products", __name__)


def allowed_file(filename, app):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]


@product_bp.route("/")
@login_required
def index():
    db = current_app.db
    search = request.args.get("search", "")
    category = request.args.get("category", "")
    products = Product.get_all(db, search=search or None, category=category or None)
    categories = Product.get_categories(db)
    return render_template("products/index.html", products=products, categories=categories,
                           search=search, selected_category=category)


@product_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if not current_user.is_admin:
        flash("Bạn không có quyền thực hiện thao tác này.", "danger")
        return redirect(url_for("products.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        price = request.form.get("price", 0)
        stock = request.form.get("stock", 0)
        description = request.form.get("description", "").strip()

        if not name or not category:
            flash("Tên và danh mục sản phẩm là bắt buộc.", "danger")
            return render_template("products/form.html", action="create", product=None)

        image_name = "default_product.png"
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename, current_app):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            image_name = filename

        Product.create(current_app.db, name, category, price, stock, description, image_name)
        flash("Thêm sản phẩm thành công!", "success")
        return redirect(url_for("products.index"))

    return render_template("products/form.html", action="create", product=None)


@product_bp.route("/edit/<product_id>", methods=["GET", "POST"])
@login_required
def edit(product_id):
    if not current_user.is_admin:
        flash("Bạn không có quyền thực hiện thao tác này.", "danger")
        return redirect(url_for("products.index"))

    db = current_app.db
    product = Product.get_by_id(db, product_id)
    if not product:
        flash("Sản phẩm không tồn tại.", "danger")
        return redirect(url_for("products.index"))

    if request.method == "POST":
        update_data = {
            "name": request.form.get("name", "").strip(),
            "category": request.form.get("category", "").strip(),
            "price": float(request.form.get("price", 0)),
            "stock": int(request.form.get("stock", 0)),
            "description": request.form.get("description", "").strip(),
        }
        file = request.files.get("image")
        if file and file.filename and allowed_file(file.filename, current_app):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            update_data["image"] = filename

        Product.update(db, product_id, **update_data)
        flash("Cập nhật sản phẩm thành công!", "success")
        return redirect(url_for("products.index"))

    return render_template("products/form.html", action="edit", product=product)


@product_bp.route("/delete/<product_id>", methods=["POST"])
@login_required
def delete(product_id):
    if not current_user.is_admin:
        flash("Bạn không có quyền thực hiện thao tác này.", "danger")
        return redirect(url_for("products.index"))
    Product.delete(current_app.db, product_id)
    flash("Xóa sản phẩm thành công!", "success")
    return redirect(url_for("products.index"))
'''

# ─────────────────────────────────────────────
# controllers/customer_controller.py
# ─────────────────────────────────────────────
files["controllers/customer_controller.py"] = '''"""Customer CRUD blueprint."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from models.customer_model import Customer
from models.order_model import Order

customer_bp = Blueprint("customers", __name__)


@customer_bp.route("/")
@login_required
def index():
    db = current_app.db
    search = request.args.get("search", "")
    customers = Customer.get_all(db, search=search or None)
    return render_template("customers/index.html", customers=customers, search=search)


@customer_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()

        if not name or not phone:
            flash("Tên và số điện thoại là bắt buộc.", "danger")
            return render_template("customers/form.html", action="create", customer=None)

        Customer.create(current_app.db, name, email, phone, address)
        flash("Thêm khách hàng thành công!", "success")
        return redirect(url_for("customers.index"))

    return render_template("customers/form.html", action="create", customer=None)


@customer_bp.route("/edit/<customer_id>", methods=["GET", "POST"])
@login_required
def edit(customer_id):
    db = current_app.db
    customer = Customer.get_by_id(db, customer_id)
    if not customer:
        flash("Khách hàng không tồn tại.", "danger")
        return redirect(url_for("customers.index"))

    if request.method == "POST":
        update_data = {
            "name": request.form.get("name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "address": request.form.get("address", "").strip(),
        }
        Customer.update(db, customer_id, **update_data)
        flash("Cập nhật khách hàng thành công!", "success")
        return redirect(url_for("customers.index"))

    return render_template("customers/form.html", action="edit", customer=customer)


@customer_bp.route("/delete/<customer_id>", methods=["POST"])
@login_required
def delete(customer_id):
    if not current_user.is_admin:
        flash("Bạn không có quyền thực hiện thao tác này.", "danger")
        return redirect(url_for("customers.index"))
    Customer.delete(current_app.db, customer_id)
    flash("Xóa khách hàng thành công!", "success")
    return redirect(url_for("customers.index"))


@customer_bp.route("/detail/<customer_id>")
@login_required
def detail(customer_id):
    db = current_app.db
    customer = Customer.get_by_id(db, customer_id)
    if not customer:
        flash("Khách hàng không tồn tại.", "danger")
        return redirect(url_for("customers.index"))
    orders = Order.get_all(db, customer_id=customer_id)
    return render_template("customers/detail.html", customer=customer, orders=orders)
'''

# ─────────────────────────────────────────────
# controllers/order_controller.py
# ─────────────────────────────────────────────
files["controllers/order_controller.py"] = '''"""Order (invoice) blueprint."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from models.order_model import Order
from models.product_model import Product
from models.customer_model import Customer
from datetime import datetime

order_bp = Blueprint("orders", __name__)


@order_bp.route("/")
@login_required
def index():
    db = current_app.db
    start_str = request.args.get("start", "")
    end_str = request.args.get("end", "")
    start = datetime.strptime(start_str, "%Y-%m-%d") if start_str else None
    end = datetime.strptime(end_str + " 23:59:59", "%Y-%m-%d %H:%M:%S") if end_str else None
    orders = Order.get_all(db, start=start, end=end)
    return render_template("orders/index.html", orders=orders, start=start_str, end=end_str)


@order_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    db = current_app.db
    products = Product.get_all(db)
    customers = Customer.get_all(db)

    if request.method == "POST":
        customer_id = request.form.get("customer_id", "")
        customer_name = request.form.get("customer_name", "").strip()
        note = request.form.get("note", "").strip()
        product_ids = request.form.getlist("product_id[]")
        quantities = request.form.getlist("quantity[]")

        if not product_ids:
            flash("Vui lòng chọn ít nhất một sản phẩm.", "danger")
            return render_template("orders/create.html", products=products, customers=customers)

        items = []
        total = 0

        for pid, qty_str in zip(product_ids, quantities):
            qty = int(qty_str) if qty_str.isdigit() else 1
            product = Product.get_by_id(db, pid)
            if not product:
                continue
            if product.stock < qty:
                flash(f"Sản phẩm '{product.name}' không đủ tồn kho (còn {product.stock}).", "danger")
                return render_template("orders/create.html", products=products, customers=customers)
            subtotal = product.price * qty
            total += subtotal
            items.append({
                "product_id": pid,
                "name": product.name,
                "price": product.price,
                "qty": qty,
                "subtotal": subtotal,
            })

        # Resolve customer name
        if customer_id:
            cust = Customer.get_by_id(db, customer_id)
            if cust:
                customer_name = cust.name

        order = Order.create(db, customer_id or None, customer_name or "Khách lẻ",
                             items, total, note, current_user.username)

        # Decrement stock & update customer spending
        for item in items:
            Product.decrement_stock(db, item["product_id"], item["qty"])
        if customer_id:
            Customer.add_spent(db, customer_id, total)

        flash(f"Tạo hóa đơn {order.order_code} thành công! Tổng: {total:,.0f} ₫", "success")
        return redirect(url_for("orders.detail", order_id=str(order._id)))

    return render_template("orders/create.html", products=products, customers=customers)


@order_bp.route("/detail/<order_id>")
@login_required
def detail(order_id):
    db = current_app.db
    order = Order.get_by_id(db, order_id)
    if not order:
        flash("Hóa đơn không tồn tại.", "danger")
        return redirect(url_for("orders.index"))
    return render_template("orders/detail.html", order=order)


@order_bp.route("/api/product/<product_id>")
@login_required
def api_product(product_id):
    """AJAX endpoint to get product info."""
    product = Product.get_by_id(current_app.db, product_id)
    if product:
        return jsonify({"id": str(product._id), "name": product.name,
                        "price": product.price, "stock": product.stock})
    return jsonify({"error": "not found"}), 404
'''

# ─────────────────────────────────────────────
# controllers/forecast_controller.py
# ─────────────────────────────────────────────
files["controllers/forecast_controller.py"] = '''"""Revenue forecasting blueprint."""
from flask import Blueprint, render_template, current_app
from flask_login import login_required
from services.forecast_service import ForecastService

forecast_bp = Blueprint("forecast", __name__)


@forecast_bp.route("/")
@login_required
def index():
    db = current_app.db
    service = ForecastService(db)
    result = service.run_forecast(months_ahead=3)
    return render_template("forecast/index.html", forecast=result)
'''

# ─────────────────────────────────────────────
# services/__init__.py
# ─────────────────────────────────────────────
files["services/__init__.py"] = ""

# ─────────────────────────────────────────────
# services/stats_service.py
# ─────────────────────────────────────────────
files["services/stats_service.py"] = '''"""Service for dashboard statistics."""
from datetime import datetime, timedelta


def get_dashboard_stats(db):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

    # Today revenue
    today_orders = list(db.orders.find({"created_at": {"$gte": today_start}}))
    today_revenue = sum(o.get("total", 0) for o in today_orders)

    # This month revenue
    month_orders = list(db.orders.find({"created_at": {"$gte": month_start}}))
    month_revenue = sum(o.get("total", 0) for o in month_orders)

    # Prev month revenue (for growth %)
    prev_orders = list(db.orders.find({"created_at": {"$gte": prev_month_start, "$lt": month_start}}))
    prev_revenue = sum(o.get("total", 0) for o in prev_orders)

    growth = 0
    if prev_revenue > 0:
        growth = round(((month_revenue - prev_revenue) / prev_revenue) * 100, 1)

    # Counts
    total_products = db.products.count_documents({})
    total_customers = db.customers.count_documents({})
    total_orders = db.orders.count_documents({})
    low_stock = db.products.count_documents({"stock": {"$lt": 10}})

    # Monthly revenue for chart (last 12 months)
    from models.order_model import Order
    monthly = Order.monthly_revenue(db)
    chart_labels = [f"{r[\'_id\'][\'month\']}/{r[\'_id\'][\'year\']}" for r in monthly]
    chart_data = [r["revenue"] for r in monthly]

    # Top products
    top_products = Order.top_products(db, limit=5)

    # Top customers
    top_customers = Order.top_customers(db, limit=5)

    return {
        "today_revenue": today_revenue,
        "month_revenue": month_revenue,
        "growth": growth,
        "total_products": total_products,
        "total_customers": total_customers,
        "total_orders": total_orders,
        "low_stock": low_stock,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "top_products": top_products,
        "top_customers": top_customers,
        "today_orders": len(today_orders),
    }
'''

# ─────────────────────────────────────────────
# services/forecast_service.py
# ─────────────────────────────────────────────
files["services/forecast_service.py"] = '''"""
Revenue forecasting service using Linear Regression (scikit-learn).
Trains on historical monthly revenue, predicts next N months.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from datetime import datetime, timedelta
from models.order_model import Order


class ForecastService:
    def __init__(self, db):
        self.db = db

    def _get_monthly_data(self):
        """Fetch and format monthly revenue data."""
        raw = Order.monthly_revenue(self.db)
        if not raw:
            return pd.DataFrame(columns=["month_idx", "revenue", "label"])

        rows = []
        for r in raw:
            year = r["_id"]["year"]
            month = r["_id"]["month"]
            label = f"{month:02d}/{year}"
            # Month index as continuous integer
            month_idx = year * 12 + month
            rows.append({"month_idx": month_idx, "revenue": r["revenue"], "label": label})

        df = pd.DataFrame(rows).sort_values("month_idx").reset_index(drop=True)
        return df

    def run_forecast(self, months_ahead=3):
        """Train model and return forecast results."""
        df = self._get_monthly_data()

        result = {
            "has_data": False,
            "actual_labels": [],
            "actual_values": [],
            "forecast_labels": [],
            "forecast_values": [],
            "mae": 0,
            "rmse": 0,
            "r2": 0,
            "months_ahead": months_ahead,
            "message": "",
        }

        if len(df) < 2:
            result["message"] = "Cần ít nhất 2 tháng dữ liệu để dự báo."
            return result

        result["has_data"] = True
        result["actual_labels"] = df["label"].tolist()
        result["actual_values"] = [round(v, 0) for v in df["revenue"].tolist()]

        # Feature: month index (normalized)
        X = df[["month_idx"]].values
        y = df["revenue"].values

        model = LinearRegression()
        model.fit(X, y)

        # Evaluate on training data
        y_pred_train = model.predict(X)
        mae = mean_absolute_error(y, y_pred_train)
        rmse = np.sqrt(mean_squared_error(y, y_pred_train))
        r2 = model.score(X, y)

        result["mae"] = round(mae, 0)
        result["rmse"] = round(rmse, 0)
        result["r2"] = round(r2, 4)

        # Predict future months
        last_idx = int(df["month_idx"].iloc[-1])
        future_idxs = [[last_idx + i] for i in range(1, months_ahead + 1)]
        future_preds = model.predict(future_idxs)

        for i, pred in enumerate(future_preds):
            future_month_idx = last_idx + i + 1
            year = future_month_idx // 12
            month = future_month_idx % 12
            if month == 0:
                month = 12
                year -= 1
            result["forecast_labels"].append(f"{month:02d}/{year}")
            result["forecast_values"].append(max(0, round(float(pred), 0)))

        return result
'''

# ─────────────────────────────────────────────
# services/seed_service.py
# ─────────────────────────────────────────────
files["services/seed_service.py"] = '''"""Seed sample data for testing."""
from datetime import datetime, timedelta
import random
from flask_bcrypt import generate_password_hash


def seed_data(db):
    """Populate database with sample data if empty."""
    if db.users.count_documents({}) > 0:
        print("ℹ️  Database already has data, skipping seed.")
        return

    print("🌱 Seeding sample data...")

    # ── Users ──────────────────────────────────────────────────────────────────
    users = [
        {"username": "admin", "email": "admin@sales.vn", "full_name": "Quản trị viên",
         "role": "admin", "password_hash": generate_password_hash("admin123").decode("utf-8"),
         "created_at": datetime.utcnow()},
        {"username": "staff1", "email": "staff1@sales.vn", "full_name": "Nhân viên A",
         "role": "staff", "password_hash": generate_password_hash("staff123").decode("utf-8"),
         "created_at": datetime.utcnow()},
    ]
    db.users.insert_many(users)

    # ── Categories & Products ──────────────────────────────────────────────────
    products_data = [
        ("Laptop Dell XPS 15", "Laptop", 28500000, 15, "Laptop cao cấp Intel i7"),
        ("MacBook Pro M3", "Laptop", 45000000, 8, "MacBook Pro chip M3"),
        ("iPhone 15 Pro Max", "Điện thoại", 34990000, 20, "iPhone mới nhất"),
        ("Samsung Galaxy S24", "Điện thoại", 22990000, 25, "Samsung flagship"),
        ("AirPods Pro 2", "Phụ kiện", 6490000, 50, "Tai nghe không dây"),
        ("Chuột Logitech MX", "Phụ kiện", 1890000, 100, "Chuột không dây cao cấp"),
        ("Bàn phím Keychron K8", "Phụ kiện", 2490000, 60, "Bàn phím cơ"),
        ("Màn hình LG 27 4K", "Màn hình", 12500000, 10, "Màn hình 4K IPS"),
        ("iPad Pro 12.9", "Tablet", 28990000, 12, "iPad Pro M2"),
        ("SSD Samsung 1TB", "Linh kiện", 2290000, 80, "SSD NVMe tốc độ cao"),
    ]
    product_ids = []
    for name, cat, price, stock, desc in products_data:
        r = db.products.insert_one({
            "name": name, "category": cat, "price": price, "stock": stock,
            "description": desc, "image": "default_product.png",
            "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()
        })
        product_ids.append((str(r.inserted_id), name, price))

    # ── Customers ─────────────────────────────────────────────────────────────
    customers_data = [
        ("Nguyễn Văn An", "an.nguyen@gmail.com", "0901234567", "12 Lê Lợi, Hà Nội"),
        ("Trần Thị Bình", "binh.tran@gmail.com", "0912345678", "45 Nguyễn Huệ, TP.HCM"),
        ("Lê Hoàng Cường", "cuong.le@gmail.com", "0923456789", "78 Trần Phú, Đà Nẵng"),
        ("Phạm Minh Đức", "duc.pham@gmail.com", "0934567890", "23 Đinh Tiên Hoàng, Huế"),
        ("Hoàng Thị Em", "em.hoang@gmail.com", "0945678901", "56 Pasteur, Cần Thơ"),
        ("Vũ Quốc Hùng", "hung.vu@gmail.com", "0956789012", "89 Lý Thường Kiệt, HN"),
        ("Đặng Thu Hương", "huong.dang@gmail.com", "0967890123", "34 Hai Bà Trưng, HN"),
        ("Bùi Văn Kiên", "kien.bui@gmail.com", "0978901234", "67 Nguyễn Trãi, HCM"),
    ]
    customer_ids = []
    for name, email, phone, address in customers_data:
        r = db.customers.insert_one({
            "name": name, "email": email, "phone": phone, "address": address,
            "total_spent": 0, "created_at": datetime.utcnow()
        })
        customer_ids.append(str(r.inserted_id))

    # ── Orders (last 12 months) ───────────────────────────────────────────────
    now = datetime.utcnow()
    count = 1
    for month_offset in range(11, -1, -1):
        base_date = now - timedelta(days=month_offset * 30)
        # 5-15 orders per month
        n_orders = random.randint(5, 15)
        for _ in range(n_orders):
            day_offset = random.randint(0, 28)
            order_date = base_date.replace(day=1) + timedelta(days=day_offset)
            customer_idx = random.randint(0, len(customer_ids) - 1)
            cid = customer_ids[customer_idx]
            customer_name = customers_data[customer_idx][0]

            # 1-3 products per order
            n_items = random.randint(1, 3)
            selected_products = random.sample(product_ids, min(n_items, len(product_ids)))
            items = []
            total = 0
            for pid, pname, pprice in selected_products:
                qty = random.randint(1, 3)
                subtotal = pprice * qty
                total += subtotal
                items.append({"product_id": pid, "name": pname, "price": pprice,
                               "qty": qty, "subtotal": subtotal})

            order_code = f"HD{order_date.strftime(\'%Y%m\')}{count:04d}"
            db.orders.insert_one({
                "order_code": order_code,
                "customer_id": None,
                "customer_name": customer_name,
                "items": items,
                "total": float(total),
                "status": "paid",
                "note": "",
                "created_at": order_date,
                "created_by": "admin",
            })
            # Update customer spending
            db.customers.update_one({"_id": __import__("bson").ObjectId(cid)},
                                     {"$inc": {"total_spent": total}})
            count += 1

    print(f"✅ Seeded: {len(users)} users, {len(products_data)} products, "
          f"{len(customers_data)} customers, {count-1} orders")
    print("   Admin: admin / admin123")
    print("   Staff: staff1 / staff123")
'''

# ─────────────────────────────────────────────
# TEMPLATES - base.html
# ─────────────────────────────────────────────
files["templates/base.html"] = '''<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{% block title %}SalesManager Pro{% endblock %}</title>
  <!-- Google Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet"/>
  <!-- Bootstrap 5 -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"/>
  <!-- Font Awesome -->
  <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet"/>
  <!-- Animate.css -->
  <link href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css" rel="stylesheet"/>
  <!-- Custom CSS -->
  <link href="{{ url_for(\'static\', filename=\'css/style.css\') }}" rel="stylesheet"/>
  {% block extra_css %}{% endblock %}
</head>
<body>
{% if current_user.is_authenticated %}
<!-- ── SIDEBAR ────────────────────────────────────────────────────────────── -->
<div class="sidebar" id="sidebar">
  <div class="sidebar-brand">
    <div class="brand-icon"><i class="fas fa-chart-line"></i></div>
    <span class="brand-text">SalesManager</span>
  </div>

  <nav class="sidebar-nav">
    <div class="nav-section-title">CHÍNH</div>
    <a href="{{ url_for(\'dashboard.index\') }}" class="nav-item {% if request.endpoint==\'dashboard.index\' %}active{% endif %}">
      <i class="fas fa-home"></i><span>Tổng quan</span>
    </a>

    <div class="nav-section-title">QUẢN LÝ</div>
    <a href="{{ url_for(\'products.index\') }}" class="nav-item {% if \'products\' in request.endpoint %}active{% endif %}">
      <i class="fas fa-box"></i><span>Sản phẩm</span>
    </a>
    <a href="{{ url_for(\'customers.index\') }}" class="nav-item {% if \'customers\' in request.endpoint %}active{% endif %}">
      <i class="fas fa-users"></i><span>Khách hàng</span>
    </a>
    <a href="{{ url_for(\'orders.index\') }}" class="nav-item {% if \'orders\' in request.endpoint %}active{% endif %}">
      <i class="fas fa-receipt"></i><span>Hóa đơn</span>
    </a>

    <div class="nav-section-title">PHÂN TÍCH</div>
    <a href="{{ url_for(\'forecast.index\') }}" class="nav-item {% if \'forecast\' in request.endpoint %}active{% endif %}">
      <i class="fas fa-brain"></i><span>Dự báo AI</span>
    </a>

    <div class="nav-section-title">TÀI KHOẢN</div>
    <a href="{{ url_for(\'auth.logout\') }}" class="nav-item text-danger-item">
      <i class="fas fa-sign-out-alt"></i><span>Đăng xuất</span>
    </a>
  </nav>

  <div class="sidebar-footer">
    <div class="user-info">
      <div class="user-avatar">{{ current_user.username[0].upper() }}</div>
      <div>
        <div class="user-name">{{ current_user.full_name or current_user.username }}</div>
        <div class="user-role">{{ "Admin" if current_user.is_admin else "Staff" }}</div>
      </div>
    </div>
  </div>
</div>

<!-- ── MAIN CONTENT ──────────────────────────────────────────────────────── -->
<div class="main-content" id="mainContent">
  <!-- Topbar -->
  <nav class="topbar">
    <button class="sidebar-toggle" id="sidebarToggle">
      <i class="fas fa-bars"></i>
    </button>
    <div class="topbar-title">{% block page_title %}Dashboard{% endblock %}</div>
    <div class="topbar-right">
      <span class="badge bg-primary-soft"><i class="fas fa-circle text-success me-1" style="font-size:8px"></i>Online</span>
      <div class="topbar-user">
        <div class="topbar-avatar">{{ current_user.username[0].upper() }}</div>
        <span>{{ current_user.full_name or current_user.username }}</span>
      </div>
    </div>
  </nav>

  <!-- Flash messages -->
  <div class="flash-container">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, message in messages %}
      <div class="alert alert-{{ category }} alert-dismissible animate__animated animate__fadeInDown" role="alert">
        <i class="fas {% if category==\'success\' %}fa-check-circle{% elif category==\'danger\' %}fa-exclamation-circle{% elif category==\'warning\' %}fa-exclamation-triangle{% else %}fa-info-circle{% endif %} me-2"></i>
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
      {% endfor %}
    {% endwith %}
  </div>

  <div class="content-wrapper animate__animated animate__fadeIn">
    {% block content %}{% endblock %}
  </div>
</div>

{% else %}
  {% block auth_content %}{% endblock %}
{% endif %}

<!-- Scripts -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="{{ url_for(\'static\', filename=\'js/main.js\') }}"></script>
{% block extra_js %}{% endblock %}
</body>
</html>
'''

# ─────────────────────────────────────────────
# TEMPLATES - auth/login.html
# ─────────────────────────────────────────────
files["templates/auth/login.html"] = '''{% extends "base.html" %}
{% block auth_content %}
<div class="auth-wrapper">
  <div class="auth-card animate__animated animate__fadeInUp">
    <div class="auth-logo">
      <div class="auth-logo-icon"><i class="fas fa-chart-line"></i></div>
      <h2>SalesManager Pro</h2>
      <p>Hệ thống quản lý bán hàng thông minh</p>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, message in messages %}
      <div class="alert alert-{{ category }}"><i class="fas fa-info-circle me-2"></i>{{ message }}</div>
      {% endfor %}
    {% endwith %}

    <form method="POST" action="{{ url_for(\'auth.login\') }}" novalidate>
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
      <div class="form-floating mb-3">
        <input type="text" class="form-control" id="username" name="username" placeholder="Username" required/>
        <label for="username"><i class="fas fa-user me-2"></i>Tên đăng nhập</label>
      </div>
      <div class="form-floating mb-3">
        <input type="password" class="form-control" id="password" name="password" placeholder="Password" required/>
        <label for="password"><i class="fas fa-lock me-2"></i>Mật khẩu</label>
      </div>
      <div class="form-check mb-3">
        <input class="form-check-input" type="checkbox" name="remember" id="remember"/>
        <label class="form-check-label" for="remember">Ghi nhớ đăng nhập</label>
      </div>
      <button type="submit" class="btn btn-primary w-100 btn-lg">
        <i class="fas fa-sign-in-alt me-2"></i>Đăng nhập
      </button>
    </form>

    <div class="auth-footer">
      Chưa có tài khoản? <a href="{{ url_for(\'auth.register\') }}">Đăng ký ngay</a>
    </div>

    <div class="demo-hint">
      <small><i class="fas fa-key me-1"></i>Demo: admin / admin123</small>
    </div>
  </div>
</div>
{% endblock %}
'''

# ─────────────────────────────────────────────
# TEMPLATES - auth/register.html
# ─────────────────────────────────────────────
files["templates/auth/register.html"] = '''{% extends "base.html" %}
{% block auth_content %}
<div class="auth-wrapper">
  <div class="auth-card animate__animated animate__fadeInUp">
    <div class="auth-logo">
      <div class="auth-logo-icon"><i class="fas fa-user-plus"></i></div>
      <h2>Đăng ký tài khoản</h2>
      <p>Tạo tài khoản mới để bắt đầu</p>
    </div>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, message in messages %}
      <div class="alert alert-{{ category }}"><i class="fas fa-info-circle me-2"></i>{{ message }}</div>
      {% endfor %}
    {% endwith %}

    <form method="POST" novalidate>
      <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
      <div class="form-floating mb-3">
        <input type="text" class="form-control" name="full_name" placeholder="Họ và tên" required/>
        <label><i class="fas fa-id-card me-2"></i>Họ và tên</label>
      </div>
      <div class="form-floating mb-3">
        <input type="text" class="form-control" name="username" placeholder="Username" required/>
        <label><i class="fas fa-user me-2"></i>Tên đăng nhập</label>
      </div>
      <div class="form-floating mb-3">
        <input type="email" class="form-control" name="email" placeholder="Email" required/>
        <label><i class="fas fa-envelope me-2"></i>Email</label>
      </div>
      <div class="form-floating mb-3">
        <input type="password" class="form-control" name="password" placeholder="Mật khẩu" required/>
        <label><i class="fas fa-lock me-2"></i>Mật khẩu</label>
      </div>
      <div class="form-floating mb-3">
        <input type="password" class="form-control" name="confirm_password" placeholder="Xác nhận" required/>
        <label><i class="fas fa-lock me-2"></i>Xác nhận mật khẩu</label>
      </div>
      <button type="submit" class="btn btn-success w-100 btn-lg">
        <i class="fas fa-user-plus me-2"></i>Đăng ký
      </button>
    </form>
    <div class="auth-footer">
      Đã có tài khoản? <a href="{{ url_for(\'auth.login\') }}">Đăng nhập</a>
    </div>
  </div>
</div>
{% endblock %}
'''

# ─────────────────────────────────────────────
# TEMPLATES - dashboard/index.html
# ─────────────────────────────────────────────
files["templates/dashboard/index.html"] = '''{% extends "base.html" %}
{% block title %}Dashboard - SalesManager{% endblock %}
{% block page_title %}Tổng quan{% endblock %}
{% block content %}

<!-- Stat cards -->
<div class="row g-4 mb-4">
  <div class="col-xl-3 col-md-6">
    <div class="stat-card stat-card-blue animate__animated animate__fadeInUp" style="animation-delay:.0s">
      <div class="stat-icon"><i class="fas fa-coins"></i></div>
      <div class="stat-body">
        <div class="stat-label">Doanh thu hôm nay</div>
        <div class="stat-value counter" data-target="{{ stats.today_revenue|int }}">0</div>
        <div class="stat-sub"><i class="fas fa-shopping-cart me-1"></i>{{ stats.today_orders }} đơn hàng</div>
      </div>
    </div>
  </div>
  <div class="col-xl-3 col-md-6">
    <div class="stat-card stat-card-purple animate__animated animate__fadeInUp" style="animation-delay:.1s">
      <div class="stat-icon"><i class="fas fa-calendar-alt"></i></div>
      <div class="stat-body">
        <div class="stat-label">Doanh thu tháng này</div>
        <div class="stat-value counter" data-target="{{ stats.month_revenue|int }}">0</div>
        <div class="stat-sub">
          {% if stats.growth >= 0 %}
            <i class="fas fa-arrow-up text-success me-1"></i><span class="text-success">+{{ stats.growth }}%</span>
          {% else %}
            <i class="fas fa-arrow-down text-danger me-1"></i><span class="text-danger">{{ stats.growth }}%</span>
          {% endif %}
          so với tháng trước
        </div>
      </div>
    </div>
  </div>
  <div class="col-xl-3 col-md-6">
    <div class="stat-card stat-card-green animate__animated animate__fadeInUp" style="animation-delay:.2s">
      <div class="stat-icon"><i class="fas fa-box"></i></div>
      <div class="stat-body">
        <div class="stat-label">Sản phẩm</div>
        <div class="stat-value counter" data-target="{{ stats.total_products }}">0</div>
        <div class="stat-sub"><i class="fas fa-exclamation-triangle text-warning me-1"></i>{{ stats.low_stock }} sắp hết hàng</div>
      </div>
    </div>
  </div>
  <div class="col-xl-3 col-md-6">
    <div class="stat-card stat-card-orange animate__animated animate__fadeInUp" style="animation-delay:.3s">
      <div class="stat-icon"><i class="fas fa-users"></i></div>
      <div class="stat-body">
        <div class="stat-label">Khách hàng</div>
        <div class="stat-value counter" data-target="{{ stats.total_customers }}">0</div>
        <div class="stat-sub"><i class="fas fa-receipt me-1"></i>{{ stats.total_orders }} đơn hàng tổng</div>
      </div>
    </div>
  </div>
</div>

<!-- Charts row -->
<div class="row g-4 mb-4">
  <div class="col-xl-8">
    <div class="card-custom animate__animated animate__fadeInUp" style="animation-delay:.4s">
      <div class="card-custom-header">
        <div>
          <h6 class="mb-0"><i class="fas fa-chart-area me-2 text-primary"></i>Doanh thu theo tháng</h6>
          <small class="text-muted">12 tháng gần nhất</small>
        </div>
      </div>
      <div class="card-custom-body">
        <canvas id="revenueChart" height="100"></canvas>
      </div>
    </div>
  </div>
  <div class="col-xl-4">
    <div class="card-custom animate__animated animate__fadeInUp" style="animation-delay:.5s">
      <div class="card-custom-header">
        <h6 class="mb-0"><i class="fas fa-trophy me-2 text-warning"></i>Top sản phẩm bán chạy</h6>
      </div>
      <div class="card-custom-body">
        {% for p in stats.top_products %}
        <div class="top-item">
          <div class="top-rank rank-{{ loop.index }}">{{ loop.index }}</div>
          <div class="top-info">
            <div class="top-name">{{ p.name }}</div>
            <div class="top-sub">{{ p.total_qty }} sản phẩm &bull; {{ "{:,.0f}".format(p.total_revenue) }} ₫</div>
          </div>
        </div>
        {% else %}
        <p class="text-muted text-center py-3">Chưa có dữ liệu</p>
        {% endfor %}
      </div>
    </div>
  </div>
</div>

<!-- Top customers -->
<div class="row g-4">
  <div class="col-12">
    <div class="card-custom animate__animated animate__fadeInUp" style="animation-delay:.6s">
      <div class="card-custom-header">
        <h6 class="mb-0"><i class="fas fa-star me-2 text-warning"></i>Top khách hàng VIP</h6>
      </div>
      <div class="card-custom-body p-0">
        <div class="table-responsive">
          <table class="table table-custom mb-0">
            <thead><tr><th>#</th><th>Khách hàng</th><th>Số đơn</th><th>Tổng chi tiêu</th></tr></thead>
            <tbody>
              {% for c in stats.top_customers %}
              <tr>
                <td><span class="rank-badge">{{ loop.index }}</span></td>
                <td><i class="fas fa-user-circle me-2 text-primary"></i>{{ c.name }}</td>
                <td><span class="badge bg-info-soft text-info">{{ c.total_orders }} đơn</span></td>
                <td class="fw-600 text-primary">{{ "{:,.0f}".format(c.total_spent) }} ₫</td>
              </tr>
              {% else %}
              <tr><td colspan="4" class="text-center text-muted py-4">Chưa có dữ liệu</td></tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
const labels = {{ stats.chart_labels | tojson }};
const data = {{ stats.chart_data | tojson }};
const ctx = document.getElementById("revenueChart").getContext("2d");
const gradient = ctx.createLinearGradient(0, 0, 0, 300);
gradient.addColorStop(0, "rgba(99,102,241,0.3)");
gradient.addColorStop(1, "rgba(99,102,241,0)");

new Chart(ctx, {
  type: "line",
  data: {
    labels: labels,
    datasets: [{
      label: "Doanh thu (₫)",
      data: data,
      borderColor: "#6366f1",
      backgroundColor: gradient,
      borderWidth: 3,
      pointBackgroundColor: "#6366f1",
      pointRadius: 5,
      pointHoverRadius: 8,
      fill: true,
      tension: 0.4,
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: ctx => " " + new Intl.NumberFormat("vi-VN").format(ctx.parsed.y) + " ₫"
        }
      }
    },
    scales: {
      y: {
        ticks: {
          callback: v => new Intl.NumberFormat("vi-VN", {notation:"compact"}).format(v) + "₫"
        },
        grid: { color: "rgba(0,0,0,0.05)" }
      },
      x: { grid: { display: false } }
    }
  }
});
</script>
{% endblock %}
'''

# ─────────────────────────────────────────────
# TEMPLATES - products/index.html
# ─────────────────────────────────────────────
files["templates/products/index.html"] = '''{% extends "base.html" %}
{% block title %}Sản phẩm{% endblock %}
{% block page_title %}Quản lý sản phẩm{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h4 class="mb-0">Danh sách sản phẩm</h4>
    <small class="text-muted">{{ products|length }} sản phẩm</small>
  </div>
  {% if current_user.is_admin %}
  <a href="{{ url_for(\'products.create\') }}" class="btn btn-primary">
    <i class="fas fa-plus me-2"></i>Thêm sản phẩm
  </a>
  {% endif %}
</div>

<!-- Search & Filter -->
<div class="card-custom mb-4">
  <div class="card-custom-body">
    <form method="GET" class="row g-3">
      <div class="col-md-6">
        <div class="input-group">
          <span class="input-group-text"><i class="fas fa-search"></i></span>
          <input type="text" class="form-control" name="search" value="{{ search }}" placeholder="Tìm sản phẩm..."/>
        </div>
      </div>
      <div class="col-md-4">
        <select class="form-select" name="category">
          <option value="">Tất cả danh mục</option>
          {% for cat in categories %}
          <option value="{{ cat }}" {% if selected_category==cat %}selected{% endif %}>{{ cat }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="col-md-2">
        <button type="submit" class="btn btn-primary w-100"><i class="fas fa-filter me-1"></i>Lọc</button>
      </div>
    </form>
  </div>
</div>

<div class="row g-3">
  {% for p in products %}
  <div class="col-xl-3 col-md-4 col-sm-6 animate__animated animate__fadeIn">
    <div class="product-card">
      <div class="product-img-wrap">
        <img src="{{ url_for(\'static\', filename=\'images/uploads/\' + p.image) if p.image != \'default_product.png\' else url_for(\'static\', filename=\'images/default_product.png\') }}" alt="{{ p.name }}" class="product-img" onerror="this.src=\'{{ url_for(\'static\', filename=\'images/default_product.png\') }}\'"/>
        <span class="category-badge">{{ p.category }}</span>
        {% if p.stock < 10 %}
        <span class="stock-badge-low">Sắp hết</span>
        {% endif %}
      </div>
      <div class="product-body">
        <h6 class="product-name">{{ p.name }}</h6>
        <div class="product-price">{{ "{:,.0f}".format(p.price) }} ₫</div>
        <div class="product-stock"><i class="fas fa-warehouse me-1"></i>Tồn: {{ p.stock }}</div>
        {% if current_user.is_admin %}
        <div class="product-actions mt-3">
          <a href="{{ url_for(\'products.edit\', product_id=p._id) }}" class="btn btn-sm btn-outline-primary">
            <i class="fas fa-edit"></i>
          </a>
          <form method="POST" action="{{ url_for(\'products.delete\', product_id=p._id) }}" class="d-inline"
                onsubmit="return confirm(\'Xóa sản phẩm này?\')">
            <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
            <button type="submit" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></button>
          </form>
        </div>
        {% endif %}
      </div>
    </div>
  </div>
  {% else %}
  <div class="col-12 text-center py-5">
    <i class="fas fa-box-open fa-4x text-muted mb-3"></i>
    <p class="text-muted">Không có sản phẩm nào.</p>
  </div>
  {% endfor %}
</div>
{% endblock %}
'''

# ─────────────────────────────────────────────
# TEMPLATES - products/form.html
# ─────────────────────────────────────────────
files["templates/products/form.html"] = '''{% extends "base.html" %}
{% block title %}{{ "Sửa" if action=="edit" else "Thêm" }} sản phẩm{% endblock %}
{% block page_title %}{{ "Cập nhật" if action=="edit" else "Thêm mới" }} sản phẩm{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-lg-8">
    <div class="card-custom animate__animated animate__fadeInUp">
      <div class="card-custom-header">
        <h6 class="mb-0"><i class="fas fa-box me-2"></i>Thông tin sản phẩm</h6>
      </div>
      <div class="card-custom-body">
        <form method="POST" enctype="multipart/form-data" novalidate>
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
          <div class="row g-3">
            <div class="col-md-8">
              <label class="form-label fw-600">Tên sản phẩm <span class="text-danger">*</span></label>
              <input type="text" class="form-control" name="name" value="{{ product.name if product else \'\' }}" required/>
            </div>
            <div class="col-md-4">
              <label class="form-label fw-600">Danh mục <span class="text-danger">*</span></label>
              <input type="text" class="form-control" name="category" value="{{ product.category if product else \'\' }}" placeholder="VD: Laptop" required/>
            </div>
            <div class="col-md-6">
              <label class="form-label fw-600">Giá bán (₫)</label>
              <input type="number" class="form-control" name="price" value="{{ product.price if product else 0 }}" min="0" step="1000"/>
            </div>
            <div class="col-md-6">
              <label class="form-label fw-600">Số lượng tồn kho</label>
              <input type="number" class="form-control" name="stock" value="{{ product.stock if product else 0 }}" min="0"/>
            </div>
            <div class="col-12">
              <label class="form-label fw-600">Mô tả</label>
              <textarea class="form-control" name="description" rows="3">{{ product.description if product else \'\' }}</textarea>
            </div>
            <div class="col-12">
              <label class="form-label fw-600">Hình ảnh sản phẩm</label>
              <input type="file" class="form-control" name="image" accept="image/*"/>
            </div>
            <div class="col-12 d-flex gap-2">
              <button type="submit" class="btn btn-primary px-4">
                <i class="fas fa-save me-2"></i>{{ "Cập nhật" if action=="edit" else "Thêm mới" }}
              </button>
              <a href="{{ url_for(\'products.index\') }}" class="btn btn-outline-secondary">Hủy</a>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
'''

# ─────────────────────────────────────────────
# TEMPLATES - customers/index.html
# ─────────────────────────────────────────────
files["templates/customers/index.html"] = '''{% extends "base.html" %}
{% block title %}Khách hàng{% endblock %}
{% block page_title %}Quản lý khách hàng{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h4 class="mb-0">Danh sách khách hàng</h4>
    <small class="text-muted">{{ customers|length }} khách hàng</small>
  </div>
  <a href="{{ url_for(\'customers.create\') }}" class="btn btn-primary">
    <i class="fas fa-user-plus me-2"></i>Thêm khách hàng
  </a>
</div>

<div class="card-custom mb-4">
  <div class="card-custom-body">
    <form method="GET" class="row g-3">
      <div class="col-md-8">
        <div class="input-group">
          <span class="input-group-text"><i class="fas fa-search"></i></span>
          <input type="text" class="form-control" name="search" value="{{ search }}" placeholder="Tìm theo tên, email, SĐT..."/>
        </div>
      </div>
      <div class="col-md-4">
        <button type="submit" class="btn btn-primary w-100"><i class="fas fa-search me-1"></i>Tìm kiếm</button>
      </div>
    </form>
  </div>
</div>

<div class="card-custom">
  <div class="card-custom-body p-0">
    <div class="table-responsive">
      <table class="table table-custom mb-0">
        <thead>
          <tr><th>#</th><th>Khách hàng</th><th>Điện thoại</th><th>Email</th><th>Tổng chi tiêu</th><th>Hành động</th></tr>
        </thead>
        <tbody>
          {% for c in customers %}
          <tr class="animate__animated animate__fadeIn">
            <td>{{ loop.index }}</td>
            <td>
              <div class="d-flex align-items-center gap-2">
                <div class="avatar-circle">{{ c.name[0] }}</div>
                <a href="{{ url_for(\'customers.detail\', customer_id=c._id) }}" class="fw-600 text-dark">{{ c.name }}</a>
              </div>
            </td>
            <td>{{ c.phone }}</td>
            <td class="text-muted">{{ c.email }}</td>
            <td class="fw-600 text-primary">{{ "{:,.0f}".format(c.total_spent) }} ₫</td>
            <td>
              <div class="d-flex gap-1">
                <a href="{{ url_for(\'customers.detail\', customer_id=c._id) }}" class="btn btn-sm btn-outline-info"><i class="fas fa-eye"></i></a>
                <a href="{{ url_for(\'customers.edit\', customer_id=c._id) }}" class="btn btn-sm btn-outline-primary"><i class="fas fa-edit"></i></a>
                {% if current_user.is_admin %}
                <form method="POST" action="{{ url_for(\'customers.delete\', customer_id=c._id) }}" class="d-inline"
                      onsubmit="return confirm(\'Xóa khách hàng này?\')">
                  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
                  <button type="submit" class="btn btn-sm btn-outline-danger"><i class="fas fa-trash"></i></button>
                </form>
                {% endif %}
              </div>
            </td>
          </tr>
          {% else %}
          <tr><td colspan="6" class="text-center text-muted py-4"><i class="fas fa-users fa-2x mb-2 d-block"></i>Không có khách hàng nào.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
{% endblock %}
'''

# ─────────────────────────────────────────────
# TEMPLATES - customers/form.html
# ─────────────────────────────────────────────
files["templates/customers/form.html"] = '''{% extends "base.html" %}
{% block title %}{{ "Sửa" if action=="edit" else "Thêm" }} khách hàng{% endblock %}
{% block page_title %}{{ "Cập nhật" if action=="edit" else "Thêm" }} khách hàng{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-lg-7">
    <div class="card-custom animate__animated animate__fadeInUp">
      <div class="card-custom-header">
        <h6 class="mb-0"><i class="fas fa-user me-2"></i>Thông tin khách hàng</h6>
      </div>
      <div class="card-custom-body">
        <form method="POST" novalidate>
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
          <div class="row g-3">
            <div class="col-md-6">
              <label class="form-label fw-600">Họ và tên <span class="text-danger">*</span></label>
              <input type="text" class="form-control" name="name" value="{{ customer.name if customer else \'\' }}" required/>
            </div>
            <div class="col-md-6">
              <label class="form-label fw-600">Số điện thoại <span class="text-danger">*</span></label>
              <input type="text" class="form-control" name="phone" value="{{ customer.phone if customer else \'\' }}" required/>
            </div>
            <div class="col-12">
              <label class="form-label fw-600">Email</label>
              <input type="email" class="form-control" name="email" value="{{ customer.email if customer else \'\' }}"/>
            </div>
            <div class="col-12">
              <label class="form-label fw-600">Địa chỉ</label>
              <textarea class="form-control" name="address" rows="2">{{ customer.address if customer else \'\' }}</textarea>
            </div>
            <div class="col-12 d-flex gap-2">
              <button type="submit" class="btn btn-primary px-4">
                <i class="fas fa-save me-2"></i>{{ "Cập nhật" if action=="edit" else "Thêm mới" }}
              </button>
              <a href="{{ url_for(\'customers.index\') }}" class="btn btn-outline-secondary">Hủy</a>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>
{% endblock %}
'''

# ─────────────────────────────────────────────
# TEMPLATES - customers/detail.html
# ─────────────────────────────────────────────
files["templates/customers/detail.html"] = '''{% extends "base.html" %}
{% block title %}Chi tiết khách hàng{% endblock %}
{% block page_title %}Chi tiết khách hàng{% endblock %}
{% block content %}
<div class="row g-4">
  <div class="col-md-4">
    <div class="card-custom animate__animated animate__fadeInLeft">
      <div class="card-custom-body text-center py-4">
        <div class="big-avatar">{{ customer.name[0] }}</div>
        <h5 class="mt-3 mb-1">{{ customer.name }}</h5>
        <p class="text-muted mb-3">{{ customer.email }}</p>
        <div class="customer-stat">
          <div class="cs-item">
            <div class="cs-value text-primary">{{ "{:,.0f}".format(customer.total_spent) }} ₫</div>
            <div class="cs-label">Tổng chi tiêu</div>
          </div>
          <div class="cs-item">
            <div class="cs-value text-success">{{ orders|length }}</div>
            <div class="cs-label">Đơn hàng</div>
          </div>
        </div>
        <div class="mt-3 text-start">
          <p class="mb-1"><i class="fas fa-phone me-2 text-primary"></i>{{ customer.phone }}</p>
          <p class="mb-1"><i class="fas fa-map-marker-alt me-2 text-danger"></i>{{ customer.address or "N/A" }}</p>
          <p class="mb-0"><i class="fas fa-clock me-2 text-info"></i>{{ customer.created_at.strftime("%d/%m/%Y") if customer.created_at else "" }}</p>
        </div>
        <div class="mt-3">
          <a href="{{ url_for(\'customers.edit\', customer_id=customer._id) }}" class="btn btn-primary btn-sm">
            <i class="fas fa-edit me-1"></i>Chỉnh sửa
          </a>
        </div>
      </div>
    </div>
  </div>
  <div class="col-md-8">
    <div class="card-custom animate__animated animate__fadeInRight">
      <div class="card-custom-header">
        <h6 class="mb-0"><i class="fas fa-history me-2"></i>Lịch sử mua hàng</h6>
      </div>
      <div class="card-custom-body p-0">
        <div class="table-responsive">
          <table class="table table-custom mb-0">
            <thead><tr><th>Mã HĐ</th><th>Ngày</th><th>Sản phẩm</th><th>Tổng tiền</th></tr></thead>
            <tbody>
              {% for o in orders %}
              <tr>
                <td><a href="{{ url_for(\'orders.detail\', order_id=o._id) }}" class="fw-600 text-primary">{{ o.order_code }}</a></td>
                <td>{{ o.created_at.strftime("%d/%m/%Y") if o.created_at else "" }}</td>
                <td>{{ o.items|length }} sản phẩm</td>
                <td class="fw-600">{{ "{:,.0f}".format(o.total) }} ₫</td>
              </tr>
              {% else %}
              <tr><td colspan="4" class="text-center text-muted py-4">Chưa có đơn hàng.</td></tr>
              {% endfor %}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
'''

# ─────────────────────────────────────────────
# TEMPLATES - orders/index.html
# ─────────────────────────────────────────────
files["templates/orders/index.html"] = '''{% extends "base.html" %}
{% block title %}Hóa đơn{% endblock %}
{% block page_title %}Quản lý hóa đơn{% endblock %}
{% block content %}
<div class="page-header">
  <div>
    <h4 class="mb-0">Danh sách hóa đơn</h4>
    <small class="text-muted">{{ orders|length }} hóa đơn</small>
  </div>
  <a href="{{ url_for(\'orders.create\') }}" class="btn btn-primary">
    <i class="fas fa-plus me-2"></i>Tạo hóa đơn
  </a>
</div>

<div class="card-custom mb-4">
  <div class="card-custom-body">
    <form method="GET" class="row g-3">
      <div class="col-md-4">
        <label class="form-label fw-600">Từ ngày</label>
        <input type="date" class="form-control" name="start" value="{{ start }}"/>
      </div>
      <div class="col-md-4">
        <label class="form-label fw-600">Đến ngày</label>
        <input type="date" class="form-control" name="end" value="{{ end }}"/>
      </div>
      <div class="col-md-4 d-flex align-items-end">
        <button type="submit" class="btn btn-primary w-100"><i class="fas fa-filter me-1"></i>Lọc</button>
      </div>
    </form>
  </div>
</div>

<div class="card-custom">
  <div class="card-custom-body p-0">
    <div class="table-responsive">
      <table class="table table-custom mb-0">
        <thead>
          <tr><th>Mã HĐ</th><th>Khách hàng</th><th>Ngày tạo</th><th>Sản phẩm</th><th>Tổng tiền</th><th>Trạng thái</th><th>Hành động</th></tr>
        </thead>
        <tbody>
          {% for o in orders %}
          <tr class="animate__animated animate__fadeIn">
            <td class="fw-600 text-primary">{{ o.order_code }}</td>
            <td><i class="fas fa-user-circle me-2 text-muted"></i>{{ o.customer_name }}</td>
            <td>{{ o.created_at.strftime("%d/%m/%Y %H:%M") if o.created_at else "" }}</td>
            <td>{{ o.items|length }} sản phẩm</td>
            <td class="fw-600">{{ "{:,.0f}".format(o.total) }} ₫</td>
            <td><span class="badge bg-success-soft text-success">Đã thanh toán</span></td>
            <td>
              <a href="{{ url_for(\'orders.detail\', order_id=o._id) }}" class="btn btn-sm btn-outline-primary">
                <i class="fas fa-eye"></i>
              </a>
            </td>
          </tr>
          {% else %}
          <tr><td colspan="7" class="text-center text-muted py-4"><i class="fas fa-receipt fa-2x mb-2 d-block"></i>Không có hóa đơn nào.</td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
{% endblock %}
'''

# ─────────────────────────────────────────────
# TEMPLATES - orders/create.html
# ─────────────────────────────────────────────
files["templates/orders/create.html"] = '''{% extends "base.html" %}
{% block title %}Tạo hóa đơn{% endblock %}
{% block page_title %}Tạo hóa đơn mới{% endblock %}
{% block content %}
<div class="row g-4">
  <div class="col-lg-8">
    <div class="card-custom animate__animated animate__fadeInLeft">
      <div class="card-custom-header">
        <h6 class="mb-0"><i class="fas fa-cart-plus me-2"></i>Chọn sản phẩm</h6>
      </div>
      <div class="card-custom-body">
        <form method="POST" id="orderForm" novalidate>
          <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>

          <!-- Customer -->
          <div class="row g-3 mb-4">
            <div class="col-md-6">
              <label class="form-label fw-600">Khách hàng</label>
              <select class="form-select" name="customer_id" id="customerSelect">
                <option value="">-- Khách lẻ --</option>
                {% for c in customers %}
                <option value="{{ c._id }}">{{ c.name }} ({{ c.phone }})</option>
                {% endfor %}
              </select>
            </div>
            <div class="col-md-6">
              <label class="form-label fw-600">Tên khách (nếu chưa có)</label>
              <input type="text" class="form-control" name="customer_name" placeholder="Nhập tên khách..."/>
            </div>
            <div class="col-12">
              <label class="form-label fw-600">Ghi chú</label>
              <input type="text" class="form-control" name="note" placeholder="Ghi chú hóa đơn..."/>
            </div>
          </div>

          <!-- Product rows -->
          <div id="productRows"></div>

          <button type="button" class="btn btn-outline-primary btn-sm mb-4" onclick="addProductRow()">
            <i class="fas fa-plus me-1"></i>Thêm sản phẩm
          </button>

          <div class="order-total-box">
            <span>Tổng tiền:</span>
            <span class="total-amount" id="totalDisplay">0 ₫</span>
          </div>

          <button type="submit" class="btn btn-primary w-100 btn-lg mt-3" id="submitBtn" disabled>
            <i class="fas fa-check-circle me-2"></i>Xác nhận thanh toán
          </button>
        </form>
      </div>
    </div>
  </div>

  <!-- Product quick reference -->
  <div class="col-lg-4">
    <div class="card-custom animate__animated animate__fadeInRight">
      <div class="card-custom-header">
        <h6 class="mb-0"><i class="fas fa-boxes me-2"></i>Danh sách sản phẩm</h6>
      </div>
      <div class="card-custom-body p-0" style="max-height:500px;overflow-y:auto">
        <table class="table table-sm mb-0">
          {% for p in products %}
          <tr class="product-ref-row" onclick="quickAddProduct(\'{{ p._id }}\', \'{{ p.name }}\', {{ p.price }}, {{ p.stock }})" style="cursor:pointer">
            <td><strong>{{ p.name }}</strong><br><small class="text-muted">{{ p.category }}</small></td>
            <td class="text-end text-primary fw-600">{{ "{:,.0f}".format(p.price) }}₫<br><small class="text-muted">Kho: {{ p.stock }}</small></td>
          </tr>
          {% endfor %}
        </table>
      </div>
    </div>
  </div>
</div>

<script>
const products = {
  {% for p in products %}
  "{{ p._id }}": { name: "{{ p.name }}", price: {{ p.price }}, stock: {{ p.stock }} },
  {% endfor %}
};

let rowCount = 0;
let total = 0;

function addProductRow(pid, pname, pprice, pstock) {
  rowCount++;
  const row = document.createElement("div");
  row.className = "product-row animate__animated animate__fadeIn";
  row.id = "row_" + rowCount;
  row.innerHTML = `
    <div class="row g-2 align-items-end mb-2">
      <div class="col-md-5">
        <label class="form-label small fw-600">Sản phẩm</label>
        <select class="form-select form-select-sm product-select" name="product_id[]" onchange="onProductChange(this, ${rowCount})">
          <option value="">-- Chọn --</option>
          ${Object.entries(products).map(([id,p]) =>
            `<option value="${id}" ${pid===id?"selected":""}>${p.name}</option>`).join("")}
        </select>
      </div>
      <div class="col-md-2">
        <label class="form-label small fw-600">SL</label>
        <input type="number" class="form-control form-control-sm qty-input" name="quantity[]" value="1" min="1" onchange="recalcTotal()" id="qty_${rowCount}"/>
      </div>
      <div class="col-md-3">
        <label class="form-label small fw-600">Đơn giá</label>
        <input type="text" class="form-control form-control-sm" readonly id="price_${rowCount}" value="${pprice ? new Intl.NumberFormat("vi-VN").format(pprice) + " ₫" : ""}"/>
        <input type="hidden" id="priceval_${rowCount}" value="${pprice || 0}"/>
      </div>
      <div class="col-md-2 text-end">
        <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeRow(${rowCount})"><i class="fas fa-times"></i></button>
      </div>
    </div>`;
  document.getElementById("productRows").appendChild(row);
  if (pid) {
    const sel = row.querySelector("select");
    sel.value = pid;
    recalcTotal();
  }
  recalcTotal();
}

function onProductChange(sel, rowId) {
  const pid = sel.value;
  if (products[pid]) {
    document.getElementById("price_" + rowId).value = new Intl.NumberFormat("vi-VN").format(products[pid].price) + " ₫";
    document.getElementById("priceval_" + rowId).value = products[pid].price;
  }
  recalcTotal();
}

function removeRow(rowId) {
  const el = document.getElementById("row_" + rowId);
  if (el) el.remove();
  recalcTotal();
}

function recalcTotal() {
  let t = 0;
  document.querySelectorAll(".product-row").forEach(row => {
    const rowId = row.id.split("_")[1];
    const price = parseFloat(document.getElementById("priceval_" + rowId)?.value || 0);
    const qty = parseInt(document.getElementById("qty_" + rowId)?.value || 1);
    const sel = row.querySelector("select");
    if (sel && sel.value) t += price * qty;
  });
  document.getElementById("totalDisplay").textContent = new Intl.NumberFormat("vi-VN").format(t) + " ₫";
  document.getElementById("submitBtn").disabled = (t === 0);
}

function quickAddProduct(pid, pname, pprice, pstock) {
  addProductRow(pid, pname, pprice, pstock);
}

// Start with one row
addProductRow();
</script>
{% endblock %}
'''

# ─────────────────────────────────────────────
# TEMPLATES - orders/detail.html
# ─────────────────────────────────────────────
files["templates/orders/detail.html"] = '''{% extends "base.html" %}
{% block title %}Chi tiết hóa đơn{% endblock %}
{% block page_title %}Chi tiết hóa đơn{% endblock %}
{% block content %}
<div class="row justify-content-center">
  <div class="col-lg-8">
    <div class="card-custom animate__animated animate__fadeInUp">
      <div class="card-custom-header d-flex justify-content-between align-items-center">
        <div>
          <h6 class="mb-0"><i class="fas fa-receipt me-2"></i>{{ order.order_code }}</h6>
          <small class="text-muted">{{ order.created_at.strftime("%d/%m/%Y %H:%M") if order.created_at else "" }}</small>
        </div>
        <span class="badge bg-success fs-6">Đã thanh toán</span>
      </div>
      <div class="card-custom-body">
        <div class="row mb-4">
          <div class="col-md-6">
            <p class="mb-1 text-muted small">KHÁCH HÀNG</p>
            <p class="fw-600 mb-0"><i class="fas fa-user me-2"></i>{{ order.customer_name }}</p>
          </div>
          <div class="col-md-6 text-md-end">
            <p class="mb-1 text-muted small">NHÂN VIÊN TẠO</p>
            <p class="fw-600 mb-0"><i class="fas fa-user-tie me-2"></i>{{ order.created_by }}</p>
          </div>
        </div>

        <table class="table table-custom">
          <thead><tr><th>#</th><th>Sản phẩm</th><th>Đơn giá</th><th>SL</th><th class="text-end">Thành tiền</th></tr></thead>
          <tbody>
            {% for item in order.items %}
            <tr>
              <td>{{ loop.index }}</td>
              <td class="fw-600">{{ item.name }}</td>
              <td>{{ "{:,.0f}".format(item.price) }} ₫</td>
              <td>{{ item.qty }}</td>
              <td class="text-end fw-600 text-primary">{{ "{:,.0f}".format(item.subtotal) }} ₫</td>
            </tr>
            {% endfor %}
          </tbody>
          <tfoot>
            <tr>
              <td colspan="4" class="text-end fw-700">TỔNG CỘNG:</td>
              <td class="text-end fw-700 fs-5 text-primary">{{ "{:,.0f}".format(order.total) }} ₫</td>
            </tr>
          </tfoot>
        </table>

        {% if order.note %}
        <div class="alert alert-light">
          <i class="fas fa-sticky-note me-2"></i><strong>Ghi chú:</strong> {{ order.note }}
        </div>
        {% endif %}

        <div class="text-center mt-3">
          <a href="{{ url_for(\'orders.index\') }}" class="btn btn-outline-secondary me-2">
            <i class="fas fa-arrow-left me-1"></i>Quay lại
          </a>
          <button onclick="window.print()" class="btn btn-primary">
            <i class="fas fa-print me-1"></i>In hóa đơn
          </button>
        </div>
      </div>
    </div>
  </div>
</div>
{% endblock %}
'''

# ─────────────────────────────────────────────
# TEMPLATES - forecast/index.html
# ─────────────────────────────────────────────
files["templates/forecast/index.html"] = '''{% extends "base.html" %}
{% block title %}Dự báo doanh thu{% endblock %}
{% block page_title %}Dự báo doanh thu AI{% endblock %}
{% block content %}

<!-- Metric cards -->
{% if forecast.has_data %}
<div class="row g-4 mb-4">
  <div class="col-md-4">
    <div class="stat-card stat-card-blue animate__animated animate__fadeInUp">
      <div class="stat-icon"><i class="fas fa-brain"></i></div>
      <div class="stat-body">
        <div class="stat-label">Mô hình</div>
        <div class="stat-value" style="font-size:1.4rem">Linear Regression</div>
        <div class="stat-sub">scikit-learn</div>
      </div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="stat-card stat-card-purple animate__animated animate__fadeInUp" style="animation-delay:.1s">
      <div class="stat-icon"><i class="fas fa-bullseye"></i></div>
      <div class="stat-body">
        <div class="stat-label">MAE</div>
        <div class="stat-value counter" data-target="{{ forecast.mae|int }}">0</div>
        <div class="stat-sub">Mean Absolute Error (₫)</div>
      </div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="stat-card stat-card-green animate__animated animate__fadeInUp" style="animation-delay:.2s">
      <div class="stat-icon"><i class="fas fa-chart-line"></i></div>
      <div class="stat-body">
        <div class="stat-label">R² Score</div>
        <div class="stat-value">{{ "%.3f"|format(forecast.r2) }}</div>
        <div class="stat-sub">Độ chính xác mô hình</div>
      </div>
    </div>
  </div>
</div>

<!-- Forecast chart -->
<div class="card-custom animate__animated animate__fadeInUp" style="animation-delay:.3s">
  <div class="card-custom-header">
    <div>
      <h6 class="mb-0"><i class="fas fa-chart-area me-2 text-primary"></i>Biểu đồ dự báo doanh thu</h6>
      <small class="text-muted">Thực tế vs Dự báo {{ forecast.months_ahead }} tháng tiếp theo</small>
    </div>
  </div>
  <div class="card-custom-body">
    <canvas id="forecastChart" height="80"></canvas>
  </div>
</div>

<!-- Forecast table -->
<div class="row g-4 mt-2">
  <div class="col-md-6">
    <div class="card-custom animate__animated animate__fadeInUp" style="animation-delay:.4s">
      <div class="card-custom-header">
        <h6 class="mb-0"><i class="fas fa-calendar-alt me-2 text-success"></i>Dự báo các tháng tới</h6>
      </div>
      <div class="card-custom-body p-0">
        <table class="table table-custom mb-0">
          <thead><tr><th>Tháng</th><th class="text-end">Dự báo doanh thu</th></tr></thead>
          <tbody>
            {% for i in range(forecast.forecast_labels|length) %}
            <tr>
              <td><i class="fas fa-calendar me-2 text-primary"></i>Tháng {{ forecast.forecast_labels[i] }}</td>
              <td class="text-end fw-600 text-success">{{ "{:,.0f}".format(forecast.forecast_values[i]) }} ₫</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
  </div>
  <div class="col-md-6">
    <div class="card-custom animate__animated animate__fadeInUp" style="animation-delay:.5s">
      <div class="card-custom-header">
        <h6 class="mb-0"><i class="fas fa-info-circle me-2 text-info"></i>Thông tin mô hình</h6>
      </div>
      <div class="card-custom-body">
        <p><strong>Thuật toán:</strong> Linear Regression</p>
        <p><strong>Số tháng huấn luyện:</strong> {{ forecast.actual_labels|length }}</p>
        <p><strong>MAE:</strong> {{ "{:,.0f}".format(forecast.mae) }} ₫</p>
        <p><strong>RMSE:</strong> {{ "{:,.0f}".format(forecast.rmse) }} ₫</p>
        <p class="mb-0"><strong>R² Score:</strong> {{ "%.4f"|format(forecast.r2) }}
          <span class="text-muted">({{ "Tốt" if forecast.r2 > 0.8 else "Trung bình" if forecast.r2 > 0.5 else "Cần thêm dữ liệu" }})</span>
        </p>
      </div>
    </div>
  </div>
</div>

{% else %}
<div class="card-custom text-center py-5 animate__animated animate__fadeIn">
  <i class="fas fa-chart-line fa-4x text-muted mb-3"></i>
  <h5 class="text-muted">{{ forecast.message }}</h5>
  <p class="text-muted">Hãy tạo thêm đơn hàng để hệ thống có đủ dữ liệu dự báo.</p>
  <a href="{{ url_for(\'orders.create\') }}" class="btn btn-primary mt-2">
    <i class="fas fa-plus me-2"></i>Tạo hóa đơn
  </a>
</div>
{% endif %}

{% endblock %}

{% block extra_js %}
{% if forecast.has_data %}
<script>
const actualLabels = {{ forecast.actual_labels | tojson }};
const actualValues = {{ forecast.actual_values | tojson }};
const forecastLabels = {{ forecast.forecast_labels | tojson }};
const forecastValues = {{ forecast.forecast_values | tojson }};

const allLabels = [...actualLabels, ...forecastLabels];
const actualPad = [...actualValues, ...Array(forecastLabels.length).fill(null)];
const forecastPad = [...Array(actualLabels.length - 1).fill(null), actualValues[actualValues.length-1], ...forecastValues];

const ctx = document.getElementById("forecastChart").getContext("2d");
new Chart(ctx, {
  type: "line",
  data: {
    labels: allLabels,
    datasets: [
      {
        label: "Thực tế",
        data: actualPad,
        borderColor: "#6366f1",
        backgroundColor: "rgba(99,102,241,0.1)",
        borderWidth: 3,
        pointRadius: 5,
        pointBackgroundColor: "#6366f1",
        fill: true,
        tension: 0.4,
        spanGaps: false,
      },
      {
        label: "Dự báo",
        data: forecastPad,
        borderColor: "#22c55e",
        backgroundColor: "rgba(34,197,94,0.1)",
        borderWidth: 3,
        borderDash: [8, 4],
        pointRadius: 6,
        pointBackgroundColor: "#22c55e",
        fill: true,
        tension: 0.4,
        spanGaps: false,
      }
    ]
  },
  options: {
    responsive: true,
    plugins: {
      tooltip: {
        callbacks: {
          label: ctx => `${ctx.dataset.label}: ${new Intl.NumberFormat("vi-VN").format(ctx.parsed.y)} ₫`
        }
      },
      legend: { position: "top" }
    },
    scales: {
      y: {
        ticks: { callback: v => new Intl.NumberFormat("vi-VN", {notation:"compact"}).format(v) + "₫" },
        grid: { color: "rgba(0,0,0,0.05)" }
      },
      x: { grid: { display: false } }
    }
  }
});
</script>
{% endif %}
{% endblock %}
'''

# ─────────────────────────────────────────────
# TEMPLATES - errors
# ─────────────────────────────────────────────
files["templates/errors/404.html"] = '''{% extends "base.html" %}
{% block content %}
<div class="error-page text-center py-5 animate__animated animate__fadeIn">
  <div class="error-code">404</div>
  <h3 class="text-muted">Trang không tồn tại</h3>
  <p class="text-muted">Trang bạn tìm kiếm không tồn tại hoặc đã bị xóa.</p>
  <a href="{{ url_for(\'dashboard.index\') }}" class="btn btn-primary mt-3">
    <i class="fas fa-home me-2"></i>Về trang chủ
  </a>
</div>
{% endblock %}
'''
files["templates/errors/500.html"] = '''{% extends "base.html" %}
{% block content %}
<div class="error-page text-center py-5 animate__animated animate__fadeIn">
  <div class="error-code text-danger">500</div>
  <h3 class="text-muted">Lỗi máy chủ</h3>
  <p class="text-muted">Đã xảy ra lỗi nội bộ. Vui lòng thử lại sau.</p>
  <a href="{{ url_for(\'dashboard.index\') }}" class="btn btn-primary mt-3">
    <i class="fas fa-home me-2"></i>Về trang chủ
  </a>
</div>
{% endblock %}
'''

# ─────────────────────────────────────────────
# STATIC - CSS
# ─────────────────────────────────────────────
files["static/css/style.css"] = ''':root {
  --primary: #6366f1;
  --primary-dark: #4f46e5;
  --secondary: #8b5cf6;
  --success: #22c55e;
  --warning: #f59e0b;
  --danger: #ef4444;
  --sidebar-width: 260px;
  --topbar-height: 64px;
  --bg: #f1f5f9;
  --card-bg: #ffffff;
  --text: #1e293b;
  --text-muted: #64748b;
  --border: #e2e8f0;
  --shadow: 0 4px 24px rgba(99,102,241,.08);
  --shadow-hover: 0 8px 32px rgba(99,102,241,.16);
  --radius: 16px;
  --radius-sm: 10px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Inter", sans-serif; background: var(--bg); color: var(--text); }

/* ── SIDEBAR ──────────────────────────────────────────────────────────────── */
.sidebar {
  position: fixed; top: 0; left: 0; height: 100vh; width: var(--sidebar-width);
  background: linear-gradient(160deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
  display: flex; flex-direction: column; z-index: 1000;
  transition: transform .3s ease; overflow-y: auto;
  scrollbar-width: thin; scrollbar-color: rgba(255,255,255,.1) transparent;
}

.sidebar-brand {
  padding: 24px 20px; display: flex; align-items: center; gap: 14px;
  border-bottom: 1px solid rgba(255,255,255,.08);
}
.brand-icon {
  width: 44px; height: 44px; background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-radius: 12px; display: flex; align-items: center; justify-content: center;
  font-size: 20px; color: #fff; box-shadow: 0 4px 12px rgba(99,102,241,.4);
}
.brand-text { color: #fff; font-size: 1.15rem; font-weight: 700; letter-spacing: .5px; }

.sidebar-nav { padding: 16px 12px; flex: 1; }
.nav-section-title {
  font-size: .65rem; font-weight: 600; letter-spacing: 1.2px;
  color: rgba(255,255,255,.3); padding: 12px 12px 6px; text-transform: uppercase;
}
.nav-item {
  display: flex; align-items: center; gap: 14px; padding: 12px 16px;
  color: rgba(255,255,255,.7); text-decoration: none; border-radius: var(--radius-sm);
  margin-bottom: 4px; transition: all .25s; font-size: .9rem; font-weight: 500;
}
.nav-item:hover { background: rgba(255,255,255,.1); color: #fff; transform: translateX(4px); }
.nav-item.active { background: linear-gradient(135deg, rgba(99,102,241,.5), rgba(139,92,246,.3)); color: #fff; box-shadow: 0 4px 12px rgba(99,102,241,.2); }
.nav-item i { width: 20px; text-align: center; font-size: 1rem; }
.text-danger-item:hover { background: rgba(239,68,68,.15) !important; color: #fca5a5 !important; }

.sidebar-footer {
  padding: 16px 20px; border-top: 1px solid rgba(255,255,255,.08);
}
.user-info { display: flex; align-items: center; gap: 12px; }
.user-avatar {
  width: 40px; height: 40px; background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 700; font-size: 1.1rem;
}
.user-name { color: #fff; font-weight: 600; font-size: .85rem; }
.user-role { color: rgba(255,255,255,.4); font-size: .75rem; }

/* ── MAIN CONTENT ─────────────────────────────────────────────────────────── */
.main-content {
  margin-left: var(--sidebar-width); min-height: 100vh;
  transition: margin-left .3s ease;
}

/* ── TOPBAR ───────────────────────────────────────────────────────────────── */
.topbar {
  height: var(--topbar-height); background: #fff; padding: 0 28px;
  display: flex; align-items: center; gap: 16px;
  border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 999;
  box-shadow: 0 2px 8px rgba(0,0,0,.04);
}
.sidebar-toggle {
  background: none; border: none; font-size: 1.2rem; color: var(--text-muted);
  cursor: pointer; padding: 8px; border-radius: 8px; transition: all .2s;
}
.sidebar-toggle:hover { background: var(--bg); color: var(--primary); }
.topbar-title { font-weight: 600; font-size: 1.05rem; flex: 1; color: var(--text); }
.topbar-right { display: flex; align-items: center; gap: 12px; }
.topbar-user { display: flex; align-items: center; gap: 10px; font-weight: 500; font-size: .9rem; }
.topbar-avatar {
  width: 36px; height: 36px; background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 700; font-size: .9rem;
}
.bg-primary-soft { background: rgba(99,102,241,.1); color: var(--primary); }

/* ── CONTENT WRAPPER ──────────────────────────────────────────────────────── */
.content-wrapper { padding: 28px; }
.flash-container { padding: 0 28px; }

/* ── STAT CARDS ───────────────────────────────────────────────────────────── */
.stat-card {
  background: #fff; border-radius: var(--radius); padding: 24px;
  display: flex; align-items: center; gap: 20px;
  box-shadow: var(--shadow); transition: all .3s; border: 1px solid var(--border);
  position: relative; overflow: hidden;
}
.stat-card::before {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
}
.stat-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-hover); }
.stat-card-blue::before { background: linear-gradient(90deg, #6366f1, #8b5cf6); }
.stat-card-purple::before { background: linear-gradient(90deg, #8b5cf6, #ec4899); }
.stat-card-green::before { background: linear-gradient(90deg, #22c55e, #16a34a); }
.stat-card-orange::before { background: linear-gradient(90deg, #f59e0b, #ef4444); }

.stat-icon {
  width: 56px; height: 56px; border-radius: 14px; display: flex;
  align-items: center; justify-content: center; font-size: 1.4rem; flex-shrink: 0;
}
.stat-card-blue .stat-icon { background: rgba(99,102,241,.12); color: #6366f1; }
.stat-card-purple .stat-icon { background: rgba(139,92,246,.12); color: #8b5cf6; }
.stat-card-green .stat-icon { background: rgba(34,197,94,.12); color: #22c55e; }
.stat-card-orange .stat-icon { background: rgba(245,158,11,.12); color: #f59e0b; }

.stat-label { font-size: .8rem; color: var(--text-muted); font-weight: 500; text-transform: uppercase; letter-spacing: .5px; margin-bottom: 4px; }
.stat-value { font-size: 1.6rem; font-weight: 800; color: var(--text); line-height: 1.1; margin-bottom: 6px; }
.stat-sub { font-size: .78rem; color: var(--text-muted); }

/* ── CARDS ────────────────────────────────────────────────────────────────── */
.card-custom {
  background: #fff; border-radius: var(--radius); box-shadow: var(--shadow);
  border: 1px solid var(--border); overflow: hidden; transition: all .3s;
}
.card-custom:hover { box-shadow: var(--shadow-hover); }
.card-custom-header {
  padding: 18px 24px; border-bottom: 1px solid var(--border);
  background: linear-gradient(135deg, #fafbff, #f8f9ff);
  display: flex; align-items: center; justify-content: space-between;
}
.card-custom-body { padding: 24px; }

/* ── TABLES ───────────────────────────────────────────────────────────────── */
.table-custom { font-size: .9rem; }
.table-custom thead th {
  background: linear-gradient(135deg, #f8faff, #eef2ff);
  color: var(--text-muted); font-weight: 600; font-size: .78rem;
  text-transform: uppercase; letter-spacing: .5px; padding: 14px 20px;
  border-bottom: 2px solid var(--border); border-top: none;
}
.table-custom tbody td { padding: 14px 20px; vertical-align: middle; border-color: var(--border); }
.table-custom tbody tr:hover { background: rgba(99,102,241,.03); }
.fw-600 { font-weight: 600 !important; }
.fw-700 { font-weight: 700 !important; }

/* ── PAGE HEADER ──────────────────────────────────────────────────────────── */
.page-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 24px; flex-wrap: wrap; gap: 12px;
}

/* ── PRODUCT CARDS ────────────────────────────────────────────────────────── */
.product-card {
  background: #fff; border-radius: var(--radius); box-shadow: var(--shadow);
  border: 1px solid var(--border); overflow: hidden; transition: all .3s;
}
.product-card:hover { transform: translateY(-6px); box-shadow: var(--shadow-hover); }
.product-img-wrap { position: relative; overflow: hidden; height: 180px; background: #f8f9ff; }
.product-img { width: 100%; height: 100%; object-fit: contain; padding: 16px; transition: transform .3s; }
.product-card:hover .product-img { transform: scale(1.05); }
.category-badge {
  position: absolute; top: 10px; left: 10px;
  background: rgba(99,102,241,.9); color: #fff;
  font-size: .7rem; padding: 4px 10px; border-radius: 20px; font-weight: 600;
}
.stock-badge-low {
  position: absolute; top: 10px; right: 10px;
  background: rgba(239,68,68,.9); color: #fff;
  font-size: .7rem; padding: 4px 10px; border-radius: 20px; font-weight: 600;
}
.product-body { padding: 16px; }
.product-name { font-weight: 700; font-size: .95rem; margin-bottom: 8px; color: var(--text); }
.product-price { font-size: 1.1rem; font-weight: 800; color: var(--primary); margin-bottom: 4px; }
.product-stock { font-size: .8rem; color: var(--text-muted); }
.product-actions { display: flex; gap: 8px; }

/* ── TOP ITEMS ────────────────────────────────────────────────────────────── */
.top-item { display: flex; align-items: center; gap: 14px; padding: 12px 0; border-bottom: 1px solid var(--border); }
.top-item:last-child { border-bottom: none; }
.top-rank {
  width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-weight: 700; font-size: .85rem; flex-shrink: 0;
}
.rank-1 { background: linear-gradient(135deg, #fbbf24, #f59e0b); color: #fff; }
.rank-2 { background: linear-gradient(135deg, #9ca3af, #6b7280); color: #fff; }
.rank-3 { background: linear-gradient(135deg, #cd7c2f, #a05e1c); color: #fff; }
.rank-4, .rank-5 { background: var(--bg); color: var(--text-muted); }
.top-name { font-weight: 600; font-size: .88rem; }
.top-sub { font-size: .76rem; color: var(--text-muted); }

/* ── RANK BADGES ──────────────────────────────────────────────────────────── */
.rank-badge {
  width: 28px; height: 28px; border-radius: 50%; background: var(--bg);
  display: inline-flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: .8rem; color: var(--text-muted);
}

/* ── AUTH ─────────────────────────────────────────────────────────────────── */
.auth-wrapper {
  min-height: 100vh; background: linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #6366f1 100%);
  display: flex; align-items: center; justify-content: center; padding: 20px;
}
.auth-card {
  background: #fff; border-radius: 24px; padding: 40px; width: 100%; max-width: 440px;
  box-shadow: 0 24px 64px rgba(0,0,0,.2);
}
.auth-logo { text-align: center; margin-bottom: 28px; }
.auth-logo-icon {
  width: 72px; height: 72px; background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-radius: 20px; display: inline-flex; align-items: center; justify-content: center;
  font-size: 2rem; color: #fff; margin-bottom: 16px;
  box-shadow: 0 8px 24px rgba(99,102,241,.4);
}
.auth-logo h2 { font-weight: 800; font-size: 1.5rem; color: var(--text); }
.auth-logo p { color: var(--text-muted); font-size: .9rem; }
.auth-footer { text-align: center; margin-top: 20px; font-size: .9rem; color: var(--text-muted); }
.auth-footer a { color: var(--primary); font-weight: 600; text-decoration: none; }
.demo-hint { text-align: center; margin-top: 12px; background: rgba(99,102,241,.06); border-radius: 10px; padding: 10px; }
.demo-hint small { color: var(--text-muted); }

/* ── BUTTONS ──────────────────────────────────────────────────────────────── */
.btn-primary { background: linear-gradient(135deg, var(--primary), var(--primary-dark)); border: none; font-weight: 600; border-radius: 10px; transition: all .25s; }
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(99,102,241,.4); background: linear-gradient(135deg, var(--primary-dark), #3730a3); }
.btn-outline-primary { border-color: var(--primary); color: var(--primary); font-weight: 500; border-radius: 10px; }
.btn-outline-primary:hover { background: var(--primary); border-color: var(--primary); transform: translateY(-1px); }
.btn-success { background: linear-gradient(135deg, #22c55e, #16a34a); border: none; border-radius: 10px; font-weight: 600; }
.btn-outline-secondary { border-radius: 10px; font-weight: 500; }
.btn-outline-danger { border-radius: 10px; }
.btn-outline-info { border-radius: 10px; }

/* ── FORM CONTROLS ────────────────────────────────────────────────────────── */
.form-control, .form-select {
  border: 2px solid var(--border); border-radius: 10px; padding: 10px 14px;
  transition: all .25s; font-size: .9rem;
}
.form-control:focus, .form-select:focus {
  border-color: var(--primary); box-shadow: 0 0 0 4px rgba(99,102,241,.1); outline: none;
}
.form-label { font-size: .85rem; color: var(--text-muted); margin-bottom: 6px; }
.form-floating label { color: var(--text-muted); }

/* ── BADGES ───────────────────────────────────────────────────────────────── */
.bg-success-soft { background: rgba(34,197,94,.12) !important; }
.bg-info-soft { background: rgba(6,182,212,.12) !important; }
.badge { font-weight: 600; border-radius: 8px; padding: 5px 10px; }

/* ── ORDER FORM ───────────────────────────────────────────────────────────── */
.order-total-box {
  background: linear-gradient(135deg, #eef2ff, #ede9fe);
  border-radius: 12px; padding: 18px 24px;
  display: flex; justify-content: space-between; align-items: center;
  font-weight: 600; font-size: 1rem;
}
.total-amount { font-size: 1.5rem; font-weight: 800; color: var(--primary); }
.product-row { background: rgba(99,102,241,.03); border-radius: 10px; padding: 12px; margin-bottom: 8px; border: 1px solid rgba(99,102,241,.1); }
.product-ref-row:hover { background: rgba(99,102,241,.05); }

/* ── CUSTOMER DETAIL ──────────────────────────────────────────────────────── */
.big-avatar {
  width: 80px; height: 80px; background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
  font-size: 2rem; font-weight: 700; color: #fff;
  box-shadow: 0 8px 24px rgba(99,102,241,.4);
}
.avatar-circle {
  width: 36px; height: 36px; background: linear-gradient(135deg, var(--primary), var(--secondary));
  border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
  color: #fff; font-weight: 700; font-size: .85rem; flex-shrink: 0;
}
.customer-stat { display: flex; gap: 20px; justify-content: center; margin-top: 16px; }
.cs-item { text-align: center; }
.cs-value { font-size: 1.1rem; font-weight: 700; }
.cs-label { font-size: .75rem; color: var(--text-muted); }

/* ── ERROR PAGE ───────────────────────────────────────────────────────────── */
.error-code { font-size: 6rem; font-weight: 800; color: var(--primary); opacity: .15; line-height: 1; }
.error-page { padding: 60px; }

/* ── ALERTS ───────────────────────────────────────────────────────────────── */
.alert { border-radius: var(--radius-sm); border: none; font-weight: 500; }
.alert-success { background: rgba(34,197,94,.1); color: #16a34a; }
.alert-danger { background: rgba(239,68,68,.1); color: #dc2626; }
.alert-warning { background: rgba(245,158,11,.1); color: #d97706; }
.alert-info { background: rgba(6,182,212,.1); color: #0891b2; }

/* ── INPUT GROUP ──────────────────────────────────────────────────────────── */
.input-group-text { border: 2px solid var(--border); border-right: none; background: var(--bg); border-radius: 10px 0 0 10px; }
.input-group .form-control { border-left: none; border-radius: 0 10px 10px 0; }

/* ── RESPONSIVE ───────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  .sidebar { transform: translateX(-100%); }
  .sidebar.show { transform: translateX(0); }
  .main-content { margin-left: 0; }
  .stat-value { font-size: 1.3rem; }
}

/* ── SCROLLBAR ────────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ── PRINT ────────────────────────────────────────────────────────────────── */
@media print {
  .sidebar, .topbar, .btn, .page-header a { display: none !important; }
  .main-content { margin-left: 0 !important; }
}
'''

# ─────────────────────────────────────────────
# STATIC - JS
# ─────────────────────────────────────────────
files["static/js/main.js"] = '''/**
 * Main JavaScript - SalesManager Pro
 */

document.addEventListener("DOMContentLoaded", function () {

  // ── Sidebar toggle ─────────────────────────────────────────────────────────
  const sidebarToggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  const mainContent = document.getElementById("mainContent");

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener("click", () => {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle("show");
      } else {
        const collapsed = sidebar.style.width === "0px";
        if (collapsed) {
          sidebar.style.width = "var(--sidebar-width)";
          mainContent.style.marginLeft = "var(--sidebar-width)";
        } else {
          sidebar.style.width = "0px";
          mainContent.style.marginLeft = "0";
        }
      }
    });
  }

  // ── Animated counter ──────────────────────────────────────────────────────
  const counters = document.querySelectorAll(".counter");
  const formatter = new Intl.NumberFormat("vi-VN");

  const observerOptions = { threshold: 0.2 };
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.getAttribute("data-target")) || 0;
        animateCount(el, target, formatter);
        observer.unobserve(el);
      }
    });
  }, observerOptions);

  counters.forEach(c => observer.observe(c));

  function animateCount(el, target, fmt) {
    let current = 0;
    const duration = 1500;
    const steps = 60;
    const increment = target / steps;
    const interval = duration / steps;

    const timer = setInterval(() => {
      current = Math.min(current + increment, target);
      el.textContent = fmt.format(Math.floor(current));
      if (current >= target) {
        el.textContent = fmt.format(target);
        clearInterval(timer);
      }
    }, interval);
  }

  // ── Auto dismiss alerts ────────────────────────────────────────────────────
  setTimeout(() => {
    document.querySelectorAll(".alert.alert-dismissible").forEach(alert => {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    });
  }, 4000);

  // ── Active nav highlight ───────────────────────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll(".nav-item").forEach(item => {
    if (item.getAttribute("href") === currentPath) {
      item.classList.add("active");
    }
  });

  // ── Tooltips ───────────────────────────────────────────────────────────────
  const tooltipEls = document.querySelectorAll("[data-bs-toggle=\'tooltip\']");
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));

});
'''

# ─────────────────────────────────────────────
# STATIC - default product image (placeholder SVG)
# ─────────────────────────────────────────────
files["static/images/default_product.png"] = None  # Will create as SVG redirect

# ─────────────────────────────────────────────
# README
# ─────────────────────────────────────────────
files["README.md"] = '''# SalesManager Pro

Hệ thống quản lý bán hàng tích hợp phân tích và dự báo doanh thu.

## Cài đặt

```bash
# 1. Tạo virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\\Scripts\\activate     # Windows

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Đảm bảo MongoDB đang chạy
# MongoDB: mongodb://localhost:27017

# 4. Chạy ứng dụng (sẽ tự seed sample data)
python app.py
```

## Tài khoản mặc định

| Vai trò | Username | Password |
|---------|----------|----------|
| Admin   | admin    | admin123 |
| Staff   | staff1   | staff123 |

## Truy cập

http://localhost:5000

## Tính năng

- 🔐 Đăng nhập / Đăng ký / Phân quyền Admin & Staff
- 📦 Quản lý sản phẩm (CRUD, upload ảnh, tồn kho)
- 👤 Quản lý khách hàng (CRUD, lịch sử mua hàng)
- 🧾 Hóa đơn (tạo, xem, lọc theo thời gian)
- 📊 Dashboard với Chart.js (animated)
- 🤖 Dự báo doanh thu AI (Linear Regression)
'''

# ─────────────────────────────────────────────
# Write all files
# ─────────────────────────────────────────────
def write_files():
    for path, content in files.items():
        if content is None:
            continue
        full_path = os.path.join(BASE, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ {path}")

    # Create default product SVG
    svg_path = os.path.join(BASE, "static/images/default_product.png")
    with open(svg_path, "wb") as f:
        # Write a minimal PNG (1x1 transparent, base64 decoded)
        import base64
        png_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAABHNCSVQICAgIfAhki"
            "AAAAAlwSFlzAAADsQAAA7EB9YPtSQAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoA"
            "AAANTSUQBVR42u3BAQEAAAIBoH9n7kAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOACAAIAAAAAAAAAAAAAAIgBAAD"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
            "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOAAgAAAAAAAAAAA"
        )
        try:
            f.write(base64.b64decode(png_b64))
        except Exception:
            # Fallback: write a simple text placeholder
            f.write(b"PNG")

    # Create uploads directory
    os.makedirs(os.path.join(BASE, "static/images/uploads"), exist_ok=True)

    print(f"\n{'='*60}")
    print("  🎉 Project generated at:", BASE)
    print("="*60)
    print("\n  HƯỚNG DẪN CHẠY:")
    print(f"  cd {BASE}")
    print("  python -m venv venv && source venv/bin/activate")
    print("  pip install -r requirements.txt")
    print("  python app.py")
    print("\n  📍 URL: http://localhost:5000")
    print("  👤 Admin: admin / admin123")
    print("  👤 Staff: staff1 / staff123")
    print("="*60)

if __name__ == "__main__":
    write_files()
