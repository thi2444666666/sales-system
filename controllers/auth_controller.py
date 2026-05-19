"""Authentication blueprint: login, register, logout."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models.user_model import User
from extensions import bcrypt

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
