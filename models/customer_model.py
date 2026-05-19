"""Customer model."""
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
