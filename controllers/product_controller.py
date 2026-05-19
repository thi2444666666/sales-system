"""Product CRUD blueprint."""
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
