"""Service for dashboard statistics."""
from datetime import datetime, timedelta


def get_dashboard_stats(db):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())  # Monday
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_start = (month_start - timedelta(days=1)).replace(day=1)
    prev_week_start = week_start - timedelta(days=7)
    prev_week_end = week_start

    # Today revenue
    today_orders = list(db.orders.find({"created_at": {"$gte": today_start}}))
    today_revenue = sum(o.get("total", 0) for o in today_orders)

    # This month revenue
    month_orders = list(db.orders.find({"created_at": {"$gte": month_start}}))
    month_revenue = sum(o.get("total", 0) for o in month_orders)

    # This week revenue
    week_orders = list(db.orders.find({"created_at": {"$gte": week_start}}))
    week_revenue = sum(o.get("total", 0) for o in week_orders)

    # Prev month revenue (for growth %)
    prev_orders = list(db.orders.find({"created_at": {"$gte": prev_month_start, "$lt": month_start}}))
    prev_revenue = sum(o.get("total", 0) for o in prev_orders)

    # Prev week revenue
    prev_week_orders = list(db.orders.find({"created_at": {"$gte": prev_week_start, "$lt": prev_week_end}}))
    prev_week_revenue = sum(o.get("total", 0) for o in prev_week_orders)

    # Growth percentages
    growth = 0
    if prev_revenue > 0:
        growth = round(((month_revenue - prev_revenue) / prev_revenue) * 100, 1)

    week_growth = 0
    if prev_week_revenue > 0:
        week_growth = round(((week_revenue - prev_week_revenue) / prev_week_revenue) * 100, 1)

    # Counts
    total_products = db.products.count_documents({})
    total_customers = db.customers.count_documents({})
    total_orders = db.orders.count_documents({})

    out_of_stock = db.products.count_documents({"stock": 0})
    low_stock = db.products.count_documents({"stock": {"$gt": 0, "$lt": 10}})

    # Monthly revenue for chart (last 12 months) — truyền rõ months=12,
    # không dùng default của Order.monthly_revenue() (giờ là 36, phục vụ
    # forecast_service.py) để dashboard tổng quan vẫn đúng ý định ban đầu:
    # chỉ hiển thị 12 tháng gần nhất cho gọn, không phải toàn bộ 3 năm.
    from models.order_model import Order
    monthly = Order.monthly_revenue(db, months=12)
    chart_labels = [f"{r['_id']['month']}/{r['_id']['year']}" for r in monthly]
    chart_data = [r["revenue"] for r in monthly]

    # Top products
    top_products = Order.top_products(db, limit=5)

    # Top customers
    top_customers = Order.top_customers(db, limit=5)

    # --- Trend analysis by category ---
    category_trend = get_category_trend(db, month_start, prev_month_start)

    return {
        "today_revenue": today_revenue,
        "month_revenue": month_revenue,
        "week_revenue": week_revenue,
        "prev_revenue": prev_revenue,
        "prev_week_revenue": prev_week_revenue,
        "growth": growth,
        "week_growth": week_growth,
        "total_products": total_products,
        "total_customers": total_customers,
        "total_orders": total_orders,
        "out_of_stock": out_of_stock,
        "low_stock": low_stock,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
        "top_products": top_products,
        "top_customers": top_customers,
        "today_orders": len(today_orders),
        "week_orders": len(week_orders),
        "month_orders_count": len(month_orders),
        "prev_month_orders_count": len(prev_orders),
        "category_trend": category_trend,
    }


def get_category_trend(db, month_start, prev_month_start):
    """Tính doanh thu theo danh mục: tháng này vs tháng trước."""
    now = datetime.utcnow()

    # Pipeline: tháng này
    pipeline_current = [
        {"$match": {"created_at": {"$gte": month_start}}},
        {"$unwind": "$items"},
        {"$lookup": {
            "from": "products",
            "localField": "items.product_id",
            "foreignField": "_id",
            "as": "product_info"
        }},
        {"$unwind": {"path": "$product_info", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": {"$ifNull": ["$product_info.category", "Khác"]},
            "revenue": {"$sum": "$items.subtotal"},
            "qty": {"$sum": "$items.qty"},
        }},
    ]

    # Pipeline: tháng trước
    pipeline_prev = [
        {"$match": {"created_at": {"$gte": prev_month_start, "$lt": month_start}}},
        {"$unwind": "$items"},
        {"$lookup": {
            "from": "products",
            "localField": "items.product_id",
            "foreignField": "_id",
            "as": "product_info"
        }},
        {"$unwind": {"path": "$product_info", "preserveNullAndEmptyArrays": True}},
        {"$group": {
            "_id": {"$ifNull": ["$product_info.category", "Khác"]},
            "revenue": {"$sum": "$items.subtotal"},
            "qty": {"$sum": "$items.qty"},
        }},
    ]

    current_data = {r["_id"]: r for r in db.orders.aggregate(pipeline_current)}
    prev_data = {r["_id"]: r for r in db.orders.aggregate(pipeline_prev)}

    all_categories = set(list(current_data.keys()) + list(prev_data.keys()))

    result = []
    for cat in sorted(all_categories):
        cur = current_data.get(cat, {"revenue": 0, "qty": 0})
        prv = prev_data.get(cat, {"revenue": 0, "qty": 0})
        cur_rev = cur["revenue"]
        prv_rev = prv["revenue"]
        if prv_rev > 0:
            pct = round(((cur_rev - prv_rev) / prv_rev) * 100, 1)
        elif cur_rev > 0:
            pct = 100.0
        else:
            pct = 0.0
        result.append({
            "category": cat,
            "current_revenue": cur_rev,
            "prev_revenue": prv_rev,
            "current_qty": cur["qty"],
            "prev_qty": prv["qty"],
            "pct_change": pct,
        })

    # Sort by current revenue desc
    result.sort(key=lambda x: x["current_revenue"], reverse=True)
    return result