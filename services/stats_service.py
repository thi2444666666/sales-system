"""Service for dashboard statistics."""
from datetime import datetime, timedelta


def get_dashboard_stats(db):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

    # Today revenue
    today_orders = list(db.orders.find({"created_at": {"$gte": today_start}}))
    today_revenue = sum(o.get("total", 0) for o in today_orders)

    # This month revenue
    month_orders = list(db.orders.find({"created_at": {"$gte": month_start}}))
    month_revenue = sum(o.get("total", 0) for o in month_orders)

    # Prev month revenue (for growth %)
    prev_orders = list(db.orders.find({"created_at": {"$gte": prev_month_start, "$lt": month_start}}))
    prev_revenue = sum(o.get("total", 0) for o in prev_orders)

    growth = 0
    if prev_revenue > 0:
        growth = round(((month_revenue - prev_revenue) / prev_revenue) * 100, 1)

    # Counts
    total_products = db.products.count_documents({})
    total_customers = db.customers.count_documents({})
    total_orders = db.orders.count_documents({})

    # Sản phẩm hết hàng (stock = 0) — đúng theo báo cáo
    out_of_stock = db.products.count_documents({"stock": 0})
    # Sản phẩm sắp hết (stock > 0 và < 10) — cảnh báo bổ sung
    low_stock = db.products.count_documents({"stock": {"$gt": 0, "$lt": 10}})

    # Monthly revenue for chart (last 12 months)
    from models.order_model import Order
    monthly = Order.monthly_revenue(db)
    chart_labels = [f"{r['_id']['month']}/{r['_id']['year']}" for r in monthly]
    chart_data = [r["revenue"] for r in monthly]

    # Top products
    top_products = Order.top_products(db, limit=5)

    # Top customers
    top_customers = Order.top_customers(db, limit=5)

    return {
        "today_revenue": today_revenue,
        "month_revenue": month_revenue,
        "growth": growth,
        "total_products": total_products,
        "total_customers": total_customers,
        "total_orders": total_orders,
        "out_of_stock": out_of_stock,   # Hết hàng (stock = 0)
        "low_stock": low_stock,          # Sắp hết (0 < stock < 10)
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "top_products": top_products,
        "top_customers": top_customers,
        "today_orders": len(today_orders),
    }