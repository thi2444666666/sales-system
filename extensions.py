"""
extensions.py — Khởi tạo các Flask extension ở đây để tránh circular import.
Import module này từ bất kỳ đâu cần dùng bcrypt, login_manager, csrf.
"""
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Vui lòng đăng nhập để tiếp tục."
login_manager.login_message_category = "warning"

bcrypt = Bcrypt()
csrf = CSRFProtect()
