"""
Revenue forecasting service using Linear Regression (scikit-learn).
Trains on historical monthly revenue, predicts next N months.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from datetime import datetime
from models.order_model import Order


class ForecastService:
    def __init__(self, db):
        self.db = db

    def _get_monthly_data(self):
        """Fetch and format monthly revenue data."""
        raw = Order.monthly_revenue(self.db)
        if not raw:
            return pd.DataFrame(columns=["month_idx", "revenue", "label"])

        rows = []
        for r in raw:
            year = r["_id"]["year"]
            month = r["_id"]["month"]
            label = f"{month:02d}/{year}"
            # Month index as continuous integer (1-based: Jan 2024 = 2024*12+1)
            month_idx = year * 12 + month
            rows.append({"month_idx": month_idx, "revenue": r["revenue"], "label": label})

        df = pd.DataFrame(rows).sort_values("month_idx").reset_index(drop=True)
        return df

    @staticmethod
    def _idx_to_label(month_idx: int) -> str:
        """Convert month_idx back to MM/YYYY string. BUG-FIX: correct formula."""
        # month_idx = year * 12 + month  →  month = month_idx % 12, year = month_idx // 12
        # But month % 12 == 0 means December
        month = month_idx % 12
        year = month_idx // 12
        if month == 0:
            month = 12
            year -= 1
        return f"{month:02d}/{year}"

    @staticmethod
    def _accuracy_label(r2: float) -> dict:
        """Return human-readable accuracy info based on R² score."""
        if r2 >= 0.9:
            return {"text": "Rất tốt", "color": "success", "pct": int(r2 * 100)}
        elif r2 >= 0.75:
            return {"text": "Tốt", "color": "primary", "pct": int(r2 * 100)}
        elif r2 >= 0.5:
            return {"text": "Trung bình", "color": "warning", "pct": int(r2 * 100)}
        elif r2 > 0:
            return {"text": "Cần thêm dữ liệu", "color": "danger", "pct": int(r2 * 100)}
        else:
            return {"text": "Không đủ xu hướng", "color": "secondary", "pct": 0}

    def run_forecast(self, months_ahead=3):
        """Train model and return forecast results."""
        df = self._get_monthly_data()

        result = {
            "has_data": False,
            "actual_labels": [],
            "actual_values": [],
            "forecast_labels": [],
            "forecast_values": [],
            "mae": 0,
            "rmse": 0,
            "r2": 0,
            "accuracy": {"text": "N/A", "color": "secondary", "pct": 0},
            "months_ahead": months_ahead,
            "message": "",
            "n_train": 0,
        }

        if len(df) < 2:
            result["message"] = "Cần ít nhất 2 tháng dữ liệu để dự báo."
            return result

        result["has_data"] = True
        result["actual_labels"] = df["label"].tolist()
        result["actual_values"] = [round(v, 0) for v in df["revenue"].tolist()]
        result["n_train"] = len(df)

        # Feature: month index
        X = df[["month_idx"]].values
        y = df["revenue"].values

        model = LinearRegression()
        model.fit(X, y)

        # Evaluate on training data
        y_pred_train = model.predict(X)
        mae = mean_absolute_error(y, y_pred_train)
        rmse = float(np.sqrt(mean_squared_error(y, y_pred_train)))
        r2 = float(model.score(X, y))

        result["mae"] = round(mae, 0)
        result["rmse"] = round(rmse, 0)
        result["r2"] = round(r2, 4)
        result["accuracy"] = self._accuracy_label(r2)

        # Predict future months — BUG-FIX: use _idx_to_label
        last_idx = int(df["month_idx"].iloc[-1])
        future_idxs = [[last_idx + i] for i in range(1, months_ahead + 1)]
        future_preds = model.predict(future_idxs)

        for i, pred in enumerate(future_preds):
            future_month_idx = last_idx + i + 1
            result["forecast_labels"].append(self._idx_to_label(future_month_idx))
            result["forecast_values"].append(max(0, round(float(pred), 0)))

        return result