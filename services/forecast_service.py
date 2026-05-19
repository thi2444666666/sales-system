"""
Revenue forecasting service using Linear Regression (scikit-learn).
Trains on historical monthly revenue, predicts next N months.
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from datetime import datetime, timedelta
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
            # Month index as continuous integer
            month_idx = year * 12 + month
            rows.append({"month_idx": month_idx, "revenue": r["revenue"], "label": label})

        df = pd.DataFrame(rows).sort_values("month_idx").reset_index(drop=True)
        return df

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
            "months_ahead": months_ahead,
            "message": "",
        }

        if len(df) < 2:
            result["message"] = "Cần ít nhất 2 tháng dữ liệu để dự báo."
            return result

        result["has_data"] = True
        result["actual_labels"] = df["label"].tolist()
        result["actual_values"] = [round(v, 0) for v in df["revenue"].tolist()]

        # Feature: month index (normalized)
        X = df[["month_idx"]].values
        y = df["revenue"].values

        model = LinearRegression()
        model.fit(X, y)

        # Evaluate on training data
        y_pred_train = model.predict(X)
        mae = mean_absolute_error(y, y_pred_train)
        rmse = np.sqrt(mean_squared_error(y, y_pred_train))
        r2 = model.score(X, y)

        result["mae"] = round(mae, 0)
        result["rmse"] = round(rmse, 0)
        result["r2"] = round(r2, 4)

        # Predict future months
        last_idx = int(df["month_idx"].iloc[-1])
        future_idxs = [[last_idx + i] for i in range(1, months_ahead + 1)]
        future_preds = model.predict(future_idxs)

        for i, pred in enumerate(future_preds):
            future_month_idx = last_idx + i + 1
            year = future_month_idx // 12
            month = future_month_idx % 12
            if month == 0:
                month = 12
                year -= 1
            result["forecast_labels"].append(f"{month:02d}/{year}")
            result["forecast_values"].append(max(0, round(float(pred), 0)))

        return result
