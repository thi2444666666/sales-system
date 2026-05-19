"""User model with Flask-Login integration."""
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
