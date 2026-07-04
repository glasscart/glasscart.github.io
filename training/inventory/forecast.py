"""Offline demand forecasting and reorder-point calculation over the
synthetic inventory history — two classical inventory-management
techniques, no ML training, no PyTorch, no paid API:

1. **Holt's linear exponential smoothing** (level + trend, Holt 1957/2004)
   over a weekly-deseasonalized daily demand series, forecasting each
   product's demand forward. Stockout days are corrected before being fed
   into the smoothing update: a stockout day's `units_sold` is a truncated
   (censored) undercount of true demand (see
   datasets/inventory/DATASET_CARD.md), so this substitutes the model's
   own current level+trend estimate for that day instead of the observed
   value — a standard, simple censored-demand correction, not a
   sophisticated one, but a real one (see docs/research/inventory.md).
2. **Reorder point (ROP)**: `forecasted daily demand × lead time + safety
   stock`, where safety stock is `z × demand std dev × √(lead time)` — the
   standard formula from classical inventory theory, given a target
   service level `z`.

Usage:
    uv run training/inventory/forecast.py
"""

from __future__ import annotations

import json
import platform
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

HISTORY_PATH = Path(__file__).parents[2] / "datasets" / "inventory" / "inventory_history.json"
OUTPUT_DIR = Path(__file__).parents[2] / "models" / "inventory"
FORECASTS_PATH = OUTPUT_DIR / "inventory_forecasts.json"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"

ALPHA = 0.3  # level smoothing constant
BETA = 0.1  # trend smoothing constant
FORECAST_HORIZON_DAYS = 14
# Real operations know their own supplier lead time contractually; this
# analysis has no access to datasets/inventory/generate.py's internal
# per-product lead time (using it would mean secretly reading simulation
# ground truth, not analyzing observable data) so it assumes one fixed
# lead time for every product instead — a documented simplification, not
# an inferred or leaked value.
ASSUMED_LEAD_TIME_DAYS = 7
SERVICE_LEVEL_Z = 1.65  # ~95% single-sided service level


@dataclass
class ProductForecast:
    product_id: str
    current_stock: int
    avg_daily_forecast: float
    forecast_horizon_days: int
    demand_std_dev: float
    reorder_point: float
    days_of_supply: float
    needs_reorder: bool
    stockout_days_observed: int


def _weekday_seasonal_index(days: list[dict]) -> dict[int, float]:
    by_weekday: dict[int, list[int]] = defaultdict(list)
    for d in days:
        by_weekday[date.fromisoformat(d["date"]).weekday()].append(d["units_sold"])
    overall_mean = statistics.fmean(d["units_sold"] for d in days) or 1e-6
    index = {}
    for weekday in range(7):
        values = by_weekday.get(weekday, [])
        index[weekday] = (statistics.fmean(values) / overall_mean) if values and overall_mean else 1.0
    return index


def _holt_linear(days: list[dict], seasonal_index: dict[int, float]) -> tuple[float, float]:
    """Returns (level, trend) of the deseasonalized series after Holt's linear smoothing."""
    deseasonalized = []
    for d in days:
        idx = seasonal_index[date.fromisoformat(d["date"]).weekday()] or 1.0
        deseasonalized.append(d["units_sold"] / idx)

    level = deseasonalized[0]
    trend = deseasonalized[1] - deseasonalized[0] if len(deseasonalized) > 1 else 0.0

    for i in range(1, len(deseasonalized)):
        observed = deseasonalized[i]
        if days[i]["stockout"]:
            # Censored day: substitute the model's own current forecast
            # instead of the truncated (undercounted) observed value.
            observed = level + trend
        prev_level = level
        level = ALPHA * observed + (1 - ALPHA) * (level + trend)
        trend = BETA * (level - prev_level) + (1 - BETA) * trend

    return level, trend


def forecast_product(product_id: str, days: list[dict]) -> ProductForecast:
    days = sorted(days, key=lambda d: d["date"])
    seasonal_index = _weekday_seasonal_index(days)
    level, trend = _holt_linear(days, seasonal_index)

    last_date = date.fromisoformat(days[-1]["date"])
    forecasts = []
    for h in range(1, FORECAST_HORIZON_DAYS + 1):
        forecast_date = last_date + timedelta(days=h)
        idx = seasonal_index[forecast_date.weekday()]
        forecasts.append(max(0.0, (level + h * trend) * idx))
    avg_daily_forecast = statistics.fmean(forecasts)

    demand_std_dev = statistics.pstdev(d["units_sold"] for d in days)
    safety_stock = SERVICE_LEVEL_Z * demand_std_dev * (ASSUMED_LEAD_TIME_DAYS**0.5)
    reorder_point = avg_daily_forecast * ASSUMED_LEAD_TIME_DAYS + safety_stock

    current_stock = days[-1]["stock_level"]
    days_of_supply = current_stock / avg_daily_forecast if avg_daily_forecast > 1e-6 else float("inf")

    return ProductForecast(
        product_id=product_id,
        current_stock=current_stock,
        avg_daily_forecast=round(avg_daily_forecast, 2),
        forecast_horizon_days=FORECAST_HORIZON_DAYS,
        demand_std_dev=round(demand_std_dev, 2),
        reorder_point=round(reorder_point, 1),
        days_of_supply=round(days_of_supply, 1) if days_of_supply != float("inf") else -1,
        needs_reorder=current_stock <= reorder_point,
        stockout_days_observed=sum(1 for d in days if d["stockout"]),
    )


def build() -> None:
    started_at = datetime.now().astimezone()
    history = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))

    by_product: dict[str, list[dict]] = defaultdict(list)
    for row in history:
        by_product[row["product_id"]].append(row)

    forecasts = [forecast_product(pid, rows) for pid, rows in by_product.items()]
    forecasts.sort(key=lambda f: f.product_id)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FORECASTS_PATH.write_text(
        json.dumps([asdict(f) for f in forecasts], indent=2) + "\n",
        encoding="utf-8",
    )

    finished_at = datetime.now().astimezone()
    num_needing_reorder = sum(1 for f in forecasts if f.needs_reorder)
    manifest = {
        "methodology": {
            "forecast": "Holt's linear exponential smoothing (level + trend) over a weekly-deseasonalized series, with stockout-day censoring correction",
            "reorder_point": "forecasted daily demand * lead time + z * demand_std_dev * sqrt(lead time)",
        },
        "alpha": ALPHA,
        "beta": BETA,
        "forecast_horizon_days": FORECAST_HORIZON_DAYS,
        "assumed_lead_time_days": ASSUMED_LEAD_TIME_DAYS,
        "service_level_z": SERVICE_LEVEL_Z,
        "num_products": len(forecasts),
        "num_products_needing_reorder": num_needing_reorder,
        "generated_at": started_at.isoformat(),
        "build_duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "runtime": {"python": platform.python_version()},
        "dataset_seed": 20260704,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Forecasted demand for {len(forecasts)} products ({num_needing_reorder} need reorder)")
    print(f"-> {FORECASTS_PATH}\n-> {MANIFEST_PATH}")


if __name__ == "__main__":
    build()
