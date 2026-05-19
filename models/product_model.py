"""Product model."""
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
