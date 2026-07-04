"""Offline demand/profit simulation using a constant-elasticity demand
curve and the classic monopoly markup (Lerner index) pricing rule.

GlassCart has no real transaction data to fit a demand model against, so
this is explicitly a **simulation over synthetic inputs**
(datasets/pricing/pricing_inputs.json), not a trained model and not a
real pricing recommendation for any product — see
models/pricing/MODEL_CARD.md and datasets/pricing/DATASET_CARD.md. What
*is* real is the economics: given a price elasticity of demand `e` and a
marginal cost `c`, a profit-maximizing monopolist facing a
constant-elasticity demand curve sets price at

    p* = c * e / (e - 1)                          (requires e > 1)

This is the standard Lerner-index / monopoly-markup result (see
docs/research/pricing.md for the derivation and primary sources) — a
real, textbook economic formula, applied here to inputs this project
openly admits are made up, because no real ones exist yet.

Usage:
    uv run training/pricing/simulate.py
"""

from __future__ import annotations

import json
import platform
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

PRICING_INPUTS_PATH = Path(__file__).parents[2] / "datasets" / "pricing" / "pricing_inputs.json"
OUTPUT_DIR = Path(__file__).parents[2] / "models" / "pricing"
RECOMMENDATIONS_PATH = OUTPUT_DIR / "pricing_recommendations.json"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"

# Price multipliers sampled around the reference price for the response
# curve shown in the UI — wide enough to show the shape of the demand/
# revenue/profit curves without extrapolating too far from the reference.
CURVE_MULTIPLIERS = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]

RAISE_THRESHOLD_PCT = 5.0
LOWER_THRESHOLD_PCT = -5.0


@dataclass
class CurvePoint:
    price_multiplier: float
    price: float
    quantity: float
    revenue: float
    profit: float


@dataclass
class PricingRecommendation:
    product_id: str
    elasticity: float
    marginal_cost: float
    current_price: float
    current_quantity: float
    current_revenue: float
    current_profit: float
    optimal_price: float
    optimal_quantity: float
    optimal_revenue: float
    optimal_profit: float
    price_change_pct: float
    profit_uplift_pct: float
    recommendation: str
    curve: list[CurvePoint]


def demand_at(price: float, reference_price: float, reference_quantity: float, elasticity: float) -> float:
    """Constant-elasticity demand curve: Q(p) = Q0 * (p/p0)^(-e)."""
    return reference_quantity * (price / reference_price) ** (-elasticity)


def optimal_price_for(marginal_cost: float, elasticity: float) -> float:
    """Monopoly markup rule: p* = c * e / (e - 1), valid for e > 1."""
    return marginal_cost * elasticity / (elasticity - 1)


def _recommendation_for(price_change_pct: float) -> str:
    if price_change_pct >= RAISE_THRESHOLD_PCT:
        return "raise"
    if price_change_pct <= LOWER_THRESHOLD_PCT:
        return "lower"
    return "near-optimal"


def simulate_product(pricing_input: dict) -> PricingRecommendation:
    p0 = pricing_input["reference_price"]
    q0 = pricing_input["reference_quantity"]
    elasticity = pricing_input["elasticity"]
    c = pricing_input["marginal_cost"]

    current_quantity = q0
    current_revenue = p0 * current_quantity
    current_profit = (p0 - c) * current_quantity

    optimal_price = round(optimal_price_for(c, elasticity), 2)
    optimal_quantity = demand_at(optimal_price, p0, q0, elasticity)
    optimal_revenue = optimal_price * optimal_quantity
    optimal_profit = (optimal_price - c) * optimal_quantity

    price_change_pct = round((optimal_price - p0) / p0 * 100, 1)
    profit_uplift_pct = round((optimal_profit - current_profit) / current_profit * 100, 1) if current_profit else 0.0

    curve = []
    for multiplier in CURVE_MULTIPLIERS:
        price = round(p0 * multiplier, 2)
        quantity = demand_at(price, p0, q0, elasticity)
        revenue = price * quantity
        profit = (price - c) * quantity
        curve.append(
            CurvePoint(
                price_multiplier=multiplier,
                price=price,
                quantity=round(quantity, 1),
                revenue=round(revenue, 2),
                profit=round(profit, 2),
            )
        )

    return PricingRecommendation(
        product_id=pricing_input["product_id"],
        elasticity=elasticity,
        marginal_cost=c,
        current_price=p0,
        current_quantity=round(current_quantity, 1),
        current_revenue=round(current_revenue, 2),
        current_profit=round(current_profit, 2),
        optimal_price=optimal_price,
        optimal_quantity=round(optimal_quantity, 1),
        optimal_revenue=round(optimal_revenue, 2),
        optimal_profit=round(optimal_profit, 2),
        price_change_pct=price_change_pct,
        profit_uplift_pct=profit_uplift_pct,
        recommendation=_recommendation_for(price_change_pct),
        curve=curve,
    )


def build() -> None:
    started_at = datetime.now(timezone.utc)
    pricing_inputs = json.loads(PRICING_INPUTS_PATH.read_text(encoding="utf-8"))

    recommendations = [simulate_product(p) for p in pricing_inputs]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RECOMMENDATIONS_PATH.write_text(
        json.dumps([asdict(r) for r in recommendations], indent=2) + "\n",
        encoding="utf-8",
    )

    finished_at = datetime.now(timezone.utc)
    counts = {
        "raise": sum(1 for r in recommendations if r.recommendation == "raise"),
        "lower": sum(1 for r in recommendations if r.recommendation == "lower"),
        "near-optimal": sum(1 for r in recommendations if r.recommendation == "near-optimal"),
    }
    manifest = {
        "methodology": "constant-elasticity demand curve + monopoly markup rule (p* = c * e / (e - 1))",
        "curve_multipliers": CURVE_MULTIPLIERS,
        "raise_threshold_pct": RAISE_THRESHOLD_PCT,
        "lower_threshold_pct": LOWER_THRESHOLD_PCT,
        "num_products": len(recommendations),
        "recommendation_counts": counts,
        "generated_at": started_at.isoformat(),
        "build_duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "runtime": {"python": platform.python_version()},
        "dataset_seed": 20260704,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Simulated pricing for {len(recommendations)} products: {counts}")
    print(f"-> {RECOMMENDATIONS_PATH}\n-> {MANIFEST_PATH}")


if __name__ == "__main__":
    build()
