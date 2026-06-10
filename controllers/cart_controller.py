"""Cart blueprint – Staff adds products to cart then checks out to create an order."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session, jsonify
from flask_login import login_required, current_user
from models.product_model import Product
from models.customer_model import Customer
from models.order_model import Order

cart_bp = Blueprint("cart", __name__)

# ── helpers ────────────────────────────────────────────────────────────────

def get_cart():
    return session.get("cart", [])   # list of {product_id, name, price, qty}

def save_cart(cart):
    session["cart"] = cart
    session.modified = True

# ── routes ─────────────────────────────────────────────────────────────────

@cart_bp.route("/")
@login_required
def index():
    if current_user.is_admin:
        flash("Admin dùng trang tạo hóa đơn trực tiếp.", "info")
        return redirect(url_for("orders.create"))
    cart = get_cart()
    total = sum(item["price"] * item["qty"] for item in cart)
    db = current_app.db
    customers = Customer.get_all(db)
    return render_template("cart/index.html", cart=cart, total=total, customers=customers)


@cart_bp.route("/add", methods=["POST"])
@login_required
def add():
    if current_user.is_admin:
        flash("Admin dùng trang tạo hóa đơn trực tiếp.", "info")
        return redirect(url_for("orders.create"))

    product_id = request.form.get("product_id", "").strip()
    qty = int(request.form.get("qty", 1))
    db = current_app.db
    product = Product.get_by_id(db, product_id)
    if not product:
        flash("Sản phẩm không tồn tại.", "danger")
        return redirect(url_for("products.index"))

    if qty < 1:
        qty = 1

    cart = get_cart()
    for item in cart:
        if item["product_id"] == product_id:
            new_qty = item["qty"] + qty
            if new_qty > product.stock:
                flash(f"Chỉ còn {product.stock} sản phẩm trong kho.", "warning")
                new_qty = product.stock
            item["qty"] = new_qty
            save_cart(cart)
            flash(f"Đã cập nhật '{product.name}' trong giỏ hàng.", "success")
            return redirect(request.referrer or url_for("products.index"))

    if qty > product.stock:
        flash(f"Chỉ còn {product.stock} sản phẩm trong kho.", "warning")
        qty = product.stock

    cart.append({
        "product_id": product_id,
        "name": product.name,
        "price": product.price,
        "qty": qty,
    })
    save_cart(cart)
    flash(f"Đã thêm '{product.name}' vào giỏ hàng!", "success")
    return redirect(request.referrer or url_for("products.index"))


@cart_bp.route("/update", methods=["POST"])
@login_required
def update():
    product_id = request.form.get("product_id", "").strip()
    qty = int(request.form.get("qty", 1))
    cart = get_cart()
    db = current_app.db
    product = Product.get_by_id(db, product_id)

    if qty <= 0:
        cart = [i for i in cart if i["product_id"] != product_id]
        save_cart(cart)
        flash("Đã xóa sản phẩm khỏi giỏ.", "info")
    else:
        if product and qty > product.stock:
            qty = product.stock
            flash(f"Điều chỉnh về tối đa tồn kho: {qty}.", "warning")
        for item in cart:
            if item["product_id"] == product_id:
                item["qty"] = qty
                break
        save_cart(cart)

    return redirect(url_for("cart.index"))


@cart_bp.route("/remove/<product_id>", methods=["POST"])
@login_required
def remove(product_id):
    cart = [i for i in get_cart() if i["product_id"] != product_id]
    save_cart(cart)
    flash("Đã xóa sản phẩm khỏi giỏ hàng.", "info")
    return redirect(url_for("cart.index"))


@cart_bp.route("/clear", methods=["POST"])
@login_required
def clear():
    save_cart([])
    flash("Đã xóa toàn bộ giỏ hàng.", "info")
    return redirect(url_for("cart.index"))


@cart_bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    if current_user.is_admin:
        return redirect(url_for("orders.create"))

    cart = get_cart()
    if not cart:
        flash("Giỏ hàng trống, không thể thanh toán.", "danger")
        return redirect(url_for("cart.index"))

    db = current_app.db
    customer_id = request.form.get("customer_id", "").strip()
    customer_name = request.form.get("customer_name", "").strip()
    note = request.form.get("note", "").strip()

    items = []
    total = 0
    for item in cart:
        product = Product.get_by_id(db, item["product_id"])
        if not product:
            flash(f"Sản phẩm '{item['name']}' không còn tồn tại.", "danger")
            return redirect(url_for("cart.index"))
        if product.stock < item["qty"]:
            flash(f"Sản phẩm '{product.name}' không đủ tồn kho (còn {product.stock}).", "danger")
            return redirect(url_for("cart.index"))
        subtotal = product.price * item["qty"]
        total += subtotal
        items.append({
            "product_id": item["product_id"],
            "name": product.name,
            "price": product.price,
            "qty": item["qty"],
            "subtotal": subtotal,
        })

    if customer_id:
        cust = Customer.get_by_id(db, customer_id)
        if cust:
            customer_name = cust.name

    order = Order.create(
        db, customer_id or None,
        customer_name or "Khách lẻ",
        items, total, note, current_user.username
    )

    for item in items:
        Product.decrement_stock(db, item["product_id"], item["qty"])
    if customer_id:
        Customer.add_spent(db, customer_id, total)

    save_cart([])
    flash(f"Tạo hóa đơn {order.order_code} thành công! Tổng: {total:,.0f} ₫", "success")
    return redirect(url_for("orders.detail", order_id=str(order._id)))
