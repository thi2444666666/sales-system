"""Customer CRUD blueprint."""
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
