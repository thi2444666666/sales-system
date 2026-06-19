"""
Revenue forecasting service - NÂNG CẤP 9+
Hỗ trợ: Linear Regression, Random Forest, dự báo theo sản phẩm, cảnh báo tồn kho.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.preprocessing import LabelEncoder
from datetime import datetime, timedelta
from models.order_model import Order
from bson import ObjectId


class ForecastService:
    # Cửa sổ dữ liệu lịch sử dùng cho mọi truy vấn theo tháng trong service
    # này — PHẢI khớp với số tháng seed_service.py tạo ra (hiện là 36 = 3
    # năm). Đây là nguồn duy nhất (single source of truth): mọi nơi cần
    # cutoff hoặc giới hạn số tháng đều tham chiếu hằng số này, tránh lặp
    # lại lỗi hard-code rải rác từng nơi rồi lệch nhau khi seed thay đổi.
    DATA_WINDOW_MONTHS = 36

    def __init__(self, db):
        self.db = db

    # ──────────────────────────────────────────────
    # HELPER: chuyển month_idx → nhãn MM/YYYY
    # ──────────────────────────────────────────────
    @staticmethod
    def _idx_to_label(month_idx: int) -> str:
        month = month_idx % 12
        year  = month_idx // 12
        if month == 0:
            month = 12
            year -= 1
        return f"{month:02d}/{year}"

    @staticmethod
    def _accuracy_label(r2: float) -> dict:
        if r2 >= 0.9:
            return {"text": "Rất tốt",         "color": "success",   "pct": int(r2 * 100)}
        elif r2 >= 0.75:
            return {"text": "Tốt",              "color": "primary",   "pct": int(r2 * 100)}
        elif r2 >= 0.5:
            return {"text": "Trung bình",        "color": "warning",   "pct": int(r2 * 100)}
        elif r2 > 0:
            return {"text": "Cần thêm dữ liệu", "color": "danger",    "pct": int(r2 * 100)}
        else:
            return {"text": "Không đủ xu hướng","color": "secondary", "pct": 0}

    # ──────────────────────────────────────────────
    # 1. DỰ BÁO TỔNG DOANH THU (tất cả sản phẩm)
    # ──────────────────────────────────────────────
    def _get_monthly_data(self):
        # Truyền rõ months=self.DATA_WINDOW_MONTHS thay vì để Order.monthly_revenue()
        # tự dùng giá trị mặc định — tránh lệch nhau nếu default ở order_model.py
        # đổi mà quên cập nhật ở đây (đúng lỗi đã xảy ra: default cũ là 24,
        # seed tạo 36, forecast chỉ thấy 24 tháng).
        raw = Order.monthly_revenue(self.db, months=self.DATA_WINDOW_MONTHS)
        if not raw:
            return pd.DataFrame(columns=["month_idx","revenue","label","month","quarter"])

        rows = []
        for r in raw:
            year  = r["_id"]["year"]
            month = r["_id"]["month"]
            label = f"{month:02d}/{year}"
            midx  = year * 12 + month
            quarter = (month - 1) // 3 + 1
            rows.append({"month_idx": midx, "revenue": r["revenue"],
                         "label": label, "month": month, "quarter": quarter})
        df = pd.DataFrame(rows).sort_values("month_idx").reset_index(drop=True)
        return df

    def run_forecast(self, months_ahead=3, model_type="linear"):
        """Dự báo tổng doanh thu với model_type = 'linear' | 'random_forest'."""
        df = self._get_monthly_data()

        result = {
            "has_data": False,
            "actual_labels":   [],
            "actual_values":   [],
            "forecast_labels": [],
            "forecast_values": [],
            "mae": 0, "rmse": 0, "r2": 0,
            "accuracy":    {"text": "N/A", "color": "secondary", "pct": 0},
            "months_ahead": months_ahead,
            "model_type":   model_type,
            "message":      "",
            "n_train":      0,
            "model_comparison": None,
        }

        if len(df) < 2:
            result["message"] = "Cần ít nhất 2 tháng dữ liệu để dự báo."
            return result

        result["has_data"]       = True
        result["actual_labels"]  = df["label"].tolist()
        result["actual_values"]  = [round(v, 0) for v in df["revenue"].tolist()]
        result["n_train"]        = len(df)

        # Feature matrix: thêm tháng, quý như đề xuất nâng cấp
        X = df[["month_idx", "month", "quarter"]].values
        y = df["revenue"].values

        # ── Chọn model ──
        if model_type == "random_forest" and len(df) >= 4:
            model = RandomForestRegressor(n_estimators=100, random_state=42)
        else:
            model_type = "linear"
            model = LinearRegression()
            X = df[["month_idx"]].values  # Linear chỉ cần 1 feature

        model.fit(X, y)

        y_pred_train = model.predict(X)
        mae  = float(mean_absolute_error(y, y_pred_train))
        rmse = float(np.sqrt(mean_squared_error(y, y_pred_train)))
        r2   = float(model.score(X, y))

        result["mae"]      = round(mae, 0)
        result["rmse"]     = round(rmse, 0)
        result["r2"]       = round(r2, 4)
        result["accuracy"] = self._accuracy_label(r2)

        # ── Dự báo tương lai ──
        last_idx = int(df["month_idx"].iloc[-1])
        forecast_labels, forecast_values = [], []
        for i in range(1, months_ahead + 1):
            fidx   = last_idx + i
            fmonth = fidx % 12 or 12
            fquart = (fmonth - 1) // 3 + 1
            if model_type == "linear":
                X_fut = [[fidx]]
            else:
                X_fut = [[fidx, fmonth, fquart]]
            pred = float(model.predict(X_fut)[0])
            forecast_labels.append(self._idx_to_label(fidx))
            forecast_values.append(max(0, round(pred, 0)))

        result["forecast_labels"] = forecast_labels
        result["forecast_values"] = forecast_values

        # ── SO SÁNH R² giữa hai mô hình (nếu đủ dữ liệu) ──
        result["model_comparison"] = self._compare_models(df)

        return result

    def _compare_models(self, df):
        """Trả về dict so sánh R² của Linear và Random Forest."""
        if len(df) < 4:
            return None
        X_lin = df[["month_idx"]].values
        X_rf  = df[["month_idx", "month", "quarter"]].values
        y     = df["revenue"].values

        lin = LinearRegression().fit(X_lin, y)
        rf  = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_rf, y)

        r2_lin = round(float(lin.score(X_lin, y)), 4)
        r2_rf  = round(float(rf.score(X_rf, y)),  4)
        return {
            "linear":        r2_lin,
            "random_forest": r2_rf,
            "better":        "random_forest" if r2_rf > r2_lin else "linear",
        }

    # ──────────────────────────────────────────────
    # 2. DỰ BÁO THEO TỪNG SẢN PHẨM
    # ──────────────────────────────────────────────
    def get_product_list(self):
        """Trả về danh sách sản phẩm có dữ liệu lịch sử."""
        pipeline = [
            {"$unwind": "$items"},
            {"$group": {"_id": "$items.product_id",
                        "name": {"$first": "$items.name"},
                        "total_revenue": {"$sum": "$items.subtotal"}}},
            {"$sort": {"total_revenue": -1}},
            {"$limit": 30},
        ]
        return list(self.db.orders.aggregate(pipeline))

    def _get_product_monthly(self, product_id):
        """Dữ liệu doanh thu theo tháng của một sản phẩm cụ thể.
        Dùng self.DATA_WINDOW_MONTHS (36) thay vì hard-code 24*31 — trước
        đây bị cố định 24 tháng dù seed đã tạo 36 tháng, khiến
        forecast_product() và product_accuracy_history() (walk-forward)
        chỉ nhìn thấy 2/3 dữ liệu thật có."""
        cutoff = datetime.utcnow() - timedelta(days=self.DATA_WINDOW_MONTHS * 31)
        # QUAN TRỌNG: items.product_id trong orders luôn được lưu là STRING
        # (xem seed_service.py dòng "product_id": prod["id"] với prod["id"] =
        # str(r.inserted_id), và cart_controller.py/order_controller.py lấy
        # trực tiếp từ request.form, cũng là string). Trước đây code này convert
        # sang ObjectId rồi match — không bao giờ khớp với string đã lưu, khiến
        # mọi dự báo theo sản phẩm trả về rỗng ("chưa đủ dữ liệu").
        pid = str(product_id)

        pipeline = [
            {"$match": {"created_at": {"$gte": cutoff}}},
            {"$unwind": "$items"},
            {"$match": {"items.product_id": pid}},
            {"$group": {
                "_id": {
                    "year":  {"$year":  "$created_at"},
                    "month": {"$month": "$created_at"},
                },
                "revenue": {"$sum": "$items.subtotal"},
                "qty":     {"$sum": "$items.qty"},
            }},
            {"$sort": {"_id.year": 1, "_id.month": 1}},
        ]
        raw = list(self.db.orders.aggregate(pipeline))
        if not raw:
            return pd.DataFrame()

        rows = []
        for r in raw:
            y = r["_id"]["year"]
            m = r["_id"]["month"]
            rows.append({
                "month_idx": y * 12 + m,
                "label":  f"{m:02d}/{y}",
                "revenue": r["revenue"],
                "qty":     r["qty"],
                "month":   m,
                "quarter": (m - 1) // 3 + 1,
            })
        return pd.DataFrame(rows).sort_values("month_idx").reset_index(drop=True)

    def forecast_product(self, product_id, months_ahead=3, model_type="auto"):
        """
        Dự báo doanh thu + số lượng của một sản phẩm cụ thể.
        model_type = "auto" → fit cả Linear + RF, chọn R² cao hơn tự động.
        """
        df = self._get_product_monthly(product_id)

        result = {
            "has_data":        False,
            "product_id":      product_id,
            "actual_labels":   [],
            "actual_values":   [],
            "actual_qty":      [],
            "forecast_labels": [],
            "forecast_values": [],
            "forecast_qty":    [],
            "r2":              0,
            "r2_linear":       None,
            "r2_rf":           None,
            "mae":             0,
            "accuracy":        {"text": "N/A", "color": "secondary", "pct": 0},
            "months_ahead":    months_ahead,
            "model_type":      model_type,
            "model_chosen":    "linear",
            "message":         "",
        }

        if len(df) < 2:
            result["message"] = "Sản phẩm này chưa đủ dữ liệu (cần ≥2 tháng)."
            return result

        result["has_data"]      = True
        result["actual_labels"] = df["label"].tolist()
        result["actual_values"] = [round(v, 0) for v in df["revenue"].tolist()]
        result["actual_qty"]    = df["qty"].tolist()

        X_lin = df[["month_idx"]].values
        X_rf  = df[["month_idx", "month", "quarter"]].values
        y_rev = df["revenue"].values
        y_qty = df["qty"].values

        # ── Fit Linear Regression ──
        lin_rev = LinearRegression().fit(X_lin, y_rev)
        r2_lin  = float(lin_rev.score(X_lin, y_rev))

        # ── Fit Random Forest (chỉ khi đủ dữ liệu ≥4 tháng) ──
        rf_rev  = None
        r2_rf   = None
        if len(df) >= 4:
            rf_rev = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_rf, y_rev)
            r2_rf  = float(rf_rev.score(X_rf, y_rev))

        result["r2_linear"] = round(r2_lin, 4)
        result["r2_rf"]     = round(r2_rf, 4) if r2_rf is not None else None

        # ── Chọn model tốt hơn ──
        if model_type == "auto":
            if r2_rf is not None and r2_rf > r2_lin:
                chosen     = "random_forest"
                model_rev  = rf_rev
                r2_chosen  = r2_rf
            else:
                chosen     = "linear"
                model_rev  = lin_rev
                r2_chosen  = r2_lin
        elif model_type == "random_forest" and rf_rev is not None:
            chosen     = "random_forest"
            model_rev  = rf_rev
            r2_chosen  = r2_rf
        else:
            chosen     = "linear"
            model_rev  = lin_rev
            r2_chosen  = r2_lin

        result["model_chosen"] = chosen
        result["model_type"]   = chosen

        mae = float(mean_absolute_error(y_rev, model_rev.predict(X_lin if chosen == "linear" else X_rf)))
        result["r2"]       = round(r2_chosen, 4)
        result["mae"]      = round(mae, 0)
        result["accuracy"] = self._accuracy_label(r2_chosen)

        # ── Qty model: cũng so sánh Linear vs RF ──
        lin_qty = LinearRegression().fit(X_lin, y_qty)
        if len(df) >= 4:
            rf_qty    = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_rf, y_qty)
            r2_qty_rf = float(rf_qty.score(X_rf, y_qty))
            r2_qty_lin= float(lin_qty.score(X_lin, y_qty))
            qty_model  = rf_qty  if r2_qty_rf > r2_qty_lin else lin_qty
            qty_uses_rf = r2_qty_rf > r2_qty_lin
        else:
            qty_model   = lin_qty
            qty_uses_rf = False

        # ── Dự báo ──
        last_idx = int(df["month_idx"].iloc[-1])
        for i in range(1, months_ahead + 1):
            fidx   = last_idx + i
            fmonth = fidx % 12 or 12
            fquart = (fmonth - 1) // 3 + 1

            if chosen == "linear":
                pred_rev = float(model_rev.predict([[fidx]])[0])
            else:
                pred_rev = float(model_rev.predict([[fidx, fmonth, fquart]])[0])

            if qty_uses_rf:
                pred_qty = float(qty_model.predict([[fidx, fmonth, fquart]])[0])
            else:
                pred_qty = float(qty_model.predict([[fidx]])[0])

            result["forecast_labels"].append(self._idx_to_label(fidx))
            result["forecast_values"].append(max(0, round(pred_rev, 0)))
            result["forecast_qty"].append(max(0, round(pred_qty, 1)))

        return result

    def compare_products(self, product_ids: list, months_ahead=3, model_type="auto"):
        """So sánh dự báo của nhiều sản phẩm cùng lúc."""
        results = []
        for pid in product_ids[:5]:
            r = self.forecast_product(pid, months_ahead, model_type)
            if r["has_data"]:
                # Lấy thêm tên sản phẩm
                prod = self.db.products.find_one({"_id": ObjectId(pid)})
                r["product_name"] = prod["name"] if prod else str(pid)
                results.append(r)
        return results

    # ──────────────────────────────────────────────
    # 3. CẢNH BÁO TỒN KHO & GỢI Ý NHẬP HÀNG
    # ──────────────────────────────────────────────
    def get_inventory_alerts(self, low_stock_threshold=10, forecast_months=2):
        """
        Phân tích tồn kho + dự báo nhu cầu dựa trên forecast_product().
        suggest_qty = tổng forecast_qty N tháng tới (từ ML) - tồn kho hiện có.
        """
        products = list(self.db.products.find({}))
        alerts   = []
        reorder  = []

        for p in products:
            stock = p.get("stock", 0)
            name  = p.get("name", "")
            pid   = str(p["_id"])

            # ── Tính daily_rate từ 30 ngày thực tế (để tính days_left) ──
            cutoff = datetime.utcnow() - timedelta(days=30)
            pipeline = [
                {"$match": {"created_at": {"$gte": cutoff}}},
                {"$unwind": "$items"},
                {"$match": {"items.product_id": str(p["_id"])}},
                {"$group": {"_id": None, "total_qty": {"$sum": "$items.qty"}}},
            ]
            agg = list(self.db.orders.aggregate(pipeline))
            sold_30d   = agg[0]["total_qty"] if agg else 0
            daily_rate = sold_30d / 30 if sold_30d else 0
            days_left  = (stock / daily_rate) if daily_rate > 0 else 999

            # ── Xác định trạng thái ──
            status = "ok"
            if stock == 0:
                status = "out"
            elif stock < low_stock_threshold or days_left < 14:
                status = "low"

            if status in ("out", "low"):
                alerts.append({
                    "name":       name,
                    "product_id": pid,
                    "stock":      stock,
                    "sold_30d":   int(sold_30d),
                    "daily_rate": round(daily_rate, 1),
                    "days_left":  round(days_left, 0) if days_left < 999 else "∞",
                    "status":     status,
                })

            # ── Gợi ý nhập hàng dùng kết quả dự báo ML ──
            if 0 < days_left < 30 * forecast_months or stock == 0:
                forecast = self.forecast_product(pid, months_ahead=forecast_months)

                if forecast["has_data"] and forecast["forecast_qty"]:
                    # Tổng số lượng cần bán trong N tháng tới theo dự báo
                    total_forecast_qty = sum(forecast["forecast_qty"])
                    # Số cần nhập = dự báo - tồn kho hiện có (tối thiểu 0)
                    suggest_qty = max(0, round(total_forecast_qty - stock, 0))
                    model_used  = forecast["model_chosen"]
                    r2_used     = forecast["r2"]
                    reason      = (
                        f"Dự báo cần {total_forecast_qty:.0f} sp trong {forecast_months} tháng tới "
                        f"(model: {model_used}, R²={r2_used})"
                    )
                else:
                    # Fallback nếu không đủ dữ liệu dự báo
                    suggest_qty = int(daily_rate * 30 * forecast_months)
                    model_used  = "fallback"
                    reason      = f"Không đủ dữ liệu ML — ước tính từ tốc độ bán {daily_rate:.1f} sp/ngày"

                if suggest_qty > 0:
                    reorder.append({
                        "name":        name,
                        "product_id":  pid,
                        "stock":       stock,
                        "suggest_qty": int(suggest_qty),
                        "model_used":  model_used,
                        "r2":          r2_used if forecast["has_data"] else None,
                        "reason":      reason,
                    })

        alerts.sort(key=lambda x: 0 if x["status"] == "out" else 1)
        reorder.sort(key=lambda x: x["stock"])

        return {
            "alerts":        alerts,
            "reorder":       reorder,
            "total_out":     sum(1 for a in alerts if a["status"] == "out"),
            "total_low":     sum(1 for a in alerts if a["status"] == "low"),
            "low_threshold": low_stock_threshold,
            "forecast_months": forecast_months,
        }

    # ──────────────────────────────────────────────
    # 4. LỊCH SỬ ĐỘ CHÍNH XÁC MÔ HÌNH (rolling)
    # ──────────────────────────────────────────────
    def _walk_forward_validate(self, df, min_points=4):
        """
        Lõi chung của walk-forward validation — dùng lại cho cả dự báo
        tổng doanh thu (model_accuracy_history) và từng sản phẩm
        (product_accuracy_history).

        Với mỗi điểm t từ t=3 trở đi: train trên [0..t-1], dự đoán điểm t,
        so với giá trị thật để tính sai số. Đây là validation trên dữ liệu
        mô hình CHƯA từng thấy khi train — khác với R² thông thường (đo
        trên chính tập đã dùng để train, dễ lạc quan ảo).
        """
        if len(df) < min_points:
            return {"has_data": False}

        X_all = df["month_idx"].values
        y_all = df["revenue"].values

        history = []
        for t in range(3, len(df)):
            X_train = X_all[:t].reshape(-1, 1)
            y_train = y_all[:t]
            X_test  = [[X_all[t]]]
            y_true  = y_all[t]

            lin = LinearRegression().fit(X_train, y_train)
            pred_lin = float(lin.predict(X_test)[0])
            err_lin  = abs(pred_lin - y_true)

            rec = {
                "label":     df["label"].iloc[t],
                "actual":    round(y_true, 0),
                "pred_lin":  max(0, round(pred_lin, 0)),
                "err_lin":   round(err_lin, 0),
                "pct_lin":   round(err_lin / y_true * 100, 1) if y_true else 0,
            }

            if t >= 4:
                X_rf_train = df[["month_idx", "month", "quarter"]].iloc[:t].values
                X_rf_test  = df[["month_idx", "month", "quarter"]].iloc[[t]].values
                rf = RandomForestRegressor(n_estimators=50, random_state=42).fit(X_rf_train, y_train)
                pred_rf = float(rf.predict(X_rf_test)[0])
                err_rf  = abs(pred_rf - y_true)
                rec["pred_rf"] = max(0, round(pred_rf, 0))
                rec["err_rf"]  = round(err_rf, 0)
                rec["pct_rf"]  = round(err_rf / y_true * 100, 1) if y_true else 0
            else:
                rec["pred_rf"] = rec["pred_lin"]
                rec["err_rf"]  = rec["err_lin"]
                rec["pct_rf"]  = rec["pct_lin"]

            history.append(rec)

        avg_pct_lin = round(float(np.mean([h["pct_lin"] for h in history])), 1)
        avg_pct_rf  = round(float(np.mean([h["pct_rf"]  for h in history])), 1)

        return {
            "has_data":    True,
            "history":     history,
            "avg_err_lin": avg_pct_lin,
            "avg_err_rf":  avg_pct_rf,
            "better":      "Random Forest" if avg_pct_rf < avg_pct_lin else "Linear Regression",
            "n_points":    len(history),
        }

    def model_accuracy_history(self):
        """Walk-forward validation cho dự báo TỔNG doanh thu (tất cả sản phẩm)."""
        df = self._get_monthly_data()
        return self._walk_forward_validate(df, min_points=4)

    def product_accuracy_history(self, product_id):
        """
        Walk-forward validation cho TỪNG SẢN PHẨM cụ thể.
        Tái sử dụng đúng logic _walk_forward_validate() đã kiểm chứng ở
        dự báo tổng — chỉ khác nguồn dữ liệu đầu vào (theo sản phẩm).

        Cần tối thiểu 5 tháng dữ liệu của sản phẩm (4 điểm train tối thiểu
        + 1 điểm để bắt đầu validate ở t=3), vì vậy ngưỡng cao hơn dự báo
        tổng — sản phẩm đơn lẻ thường ít dữ liệu hơn tổng toàn hệ thống.
        """
        df = self._get_product_monthly(product_id)
        result = self._walk_forward_validate(df, min_points=5)
        result["product_id"] = product_id
        if not result.get("has_data"):
            result["message"] = (
                f"Sản phẩm này có {len(df)} tháng dữ liệu — cần tối thiểu 5 tháng "
                f"để chạy walk-forward validation đáng tin cậy."
            )
        return result