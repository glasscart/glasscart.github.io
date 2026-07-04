"""Synthetic daily sales + stock-level history for GlassCart.

Generates a deterministic, seeded 90-day daily history per product —
units sold, end-of-day stock level, and whether the product was stocked
out that day — since GlassCart has no real sales history and the product
catalog only ever carries a static aggregate `rating`/`rating_count`, not
a time series. This exists purely so the inventory-forecasting subsystem
(training/inventory/) has something realistic-shaped to forecast against.

Three things are deliberately built into the simulation, not left to
chance, because a forecasting method needs real structure to recover:

1. **A trend** per product (demand drifting up or down over the period).
2. **Weekly seasonality**, varied by category (e.g. Toys/Beauty skew
   toward weekend demand; Office Supplies skews toward weekdays).
3. **Periodic restocking with occasional stockouts**: stock is replenished
   on a lead-time cadence, but a demand spike can still deplete it first —
   producing *censored* demand (the day's true demand is unknown; only
   "sold out" is observed), a real complication real inventory forecasting
   has to handle and this dataset doesn't shy away from.

Usage:
    uv run datasets/inventory/generate.py
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from pathlib import Path

SEED = 20260704
PRODUCTS_PATH = Path(__file__).parents[1] / "products" / "products.json"
OUTPUT_PATH = Path(__file__).parent / "inventory_history.json"

HISTORY_DAYS = 90
END_DATE = date(2026, 7, 4)

# Category-level baseline daily demand rate (mean units/day) and a weekend
# multiplier — categories people buy on impulse or for weekend activities
# (Toys, Beauty, Sports & Outdoors, Grocery) skew toward weekend demand;
# Office Supplies skews toward weekdays (workplace purchasing).
CATEGORY_DAILY_DEMAND: dict[str, tuple[float, float]] = {
    "Electronics": (1.2, 1.1),
    "Home & Kitchen": (1.5, 1.15),
    "Books": (0.6, 1.1),
    "Clothing": (2.0, 1.2),
    "Sports & Outdoors": (1.0, 1.3),
    "Beauty": (2.5, 1.3),
    "Toys": (1.4, 1.35),
    "Grocery": (5.0, 1.25),
    "Office Supplies": (1.2, 0.75),
    "Pet Supplies": (1.6, 1.1),
}

LEAD_TIME_DAYS_RANGE = (5, 12)  # time between placing a restock order and it arriving
RESTOCK_TARGET_DAYS_OF_SUPPLY = (25, 35)  # a restock tops stock up to roughly this many days of typical demand


@dataclass
class InventoryDay:
    product_id: str
    date: str
    units_sold: int
    stock_level: int
    stockout: bool
    restocked: bool


def _trend_multiplier(day_index: int, total_days: int, trend_pct: float) -> float:
    """Linear drift from 1.0 at day 0 to (1 + trend_pct) at the last day."""
    return 1.0 + trend_pct * (day_index / max(1, total_days - 1))


def simulate_product(rng: random.Random, product: dict) -> list[InventoryDay]:
    category = product["category"]
    base_rate, weekend_multiplier = CATEGORY_DAILY_DEMAND[category]
    base_rate *= rng.uniform(0.7, 1.4)  # per-product variation around the category baseline

    trend_pct = rng.uniform(-0.25, 0.35)
    lead_time_days = rng.randint(*LEAD_TIME_DAYS_RANGE)
    target_days_of_supply = rng.uniform(*RESTOCK_TARGET_DAYS_OF_SUPPLY)

    stock = round(base_rate * target_days_of_supply)
    pending_restock_in = None  # days until a placed order arrives

    history: list[InventoryDay] = []
    start = END_DATE - timedelta(days=HISTORY_DAYS - 1)

    for day_index in range(HISTORY_DAYS):
        current_date = start + timedelta(days=day_index)
        is_weekend = current_date.weekday() >= 5
        seasonal = weekend_multiplier if is_weekend else 1.0
        lam = max(0.05, base_rate * _trend_multiplier(day_index, HISTORY_DAYS, trend_pct) * seasonal)

        demand = rng.gauss(lam, max(0.5, lam**0.5))
        demand = max(0, round(demand))

        units_sold = min(demand, stock)
        stockout = demand > stock
        stock -= units_sold

        restocked = False
        if pending_restock_in is not None:
            pending_restock_in -= 1
            if pending_restock_in <= 0:
                stock += round(base_rate * target_days_of_supply)
                pending_restock_in = None
                restocked = True

        # Place a new restock order once stock drops below ~lead-time's
        # worth of demand and nothing is already on order.
        if pending_restock_in is None and stock <= base_rate * lead_time_days:
            pending_restock_in = lead_time_days

        history.append(
            InventoryDay(
                product_id=product["id"],
                date=current_date.isoformat(),
                units_sold=units_sold,
                stock_level=stock,
                stockout=stockout,
                restocked=restocked,
            )
        )

    return history


def generate_inventory_history(seed: int = SEED) -> list[InventoryDay]:
    rng = random.Random(seed)
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))

    history: list[InventoryDay] = []
    for product in products:
        history.extend(simulate_product(rng, product))
    return history


def main() -> None:
    history = generate_inventory_history()
    OUTPUT_PATH.write_text(
        json.dumps([asdict(h) for h in history], indent=2) + "\n",
        encoding="utf-8",
    )
    num_stockout_days = sum(1 for h in history if h.stockout)
    print(f"Generated {len(history)} product-days ({num_stockout_days} stockout days) -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
