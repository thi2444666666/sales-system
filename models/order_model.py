"""Order (invoice) model."""
from bson import ObjectId
from datetime import datetime, timedelta


class Order:
    def __init__(self, data: dict):
        self._id = data.get("_id")
        self.order_code = data.get("order_code", "")
        self.customer_id = data.get("customer_id")
        self.customer_name = data.get("customer_name", "")
        self.items = data.get("items", [])
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
    def get_by_staff(cls, db, username, start=None, end=None):
        """Lấy hóa đơn của một nhân viên cụ thể."""
        query = {"created_by": username}
        if start or end:
            query["created_at"] = {}
            if start:
                query["created_at"]["$gte"] = start
            if end:
                query["created_at"]["$lte"] = end
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
        count = db.orders.count_documents({})
        order_code = f"HD{datetime.utcnow().strftime('%Y%m')}{count+1:04d}"
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
    def monthly_revenue(cls, db, months=24):
        """Aggregate revenue by month. BUG-FIX: filter to last N months so old data doesn't skew forecast."""
        cutoff = datetime.utcnow() - timedelta(days=months * 31)
        pipeline = [
            {"$match": {"created_at": {"$gte": cutoff}}},
            {"$group": {
                "_id": {
                    "year": {"$year": "$created_at"},
                    "month": {"$month": "$created_at"},
                },
                "revenue": {"$sum": "$total"},
                "count": {"$sum": 1},
            }},
            {"$sort": {"_id.year": 1, "_id.month": 1}},
            {"$limit": months},
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