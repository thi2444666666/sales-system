"""Order (invoice) blueprint."""
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
