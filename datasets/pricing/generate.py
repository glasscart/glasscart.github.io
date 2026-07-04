"""Synthetic pricing-simulation inputs for GlassCart.

Generates, per product, the inputs a demand/pricing simulation needs that
the product catalog itself doesn't carry: a price elasticity of demand, a
marginal cost, and a reference (baseline) monthly demand quantity. **None
of this represents real cost structure, real demand, or real market
behavior for any product** — GlassCart has no transaction data to fit a
real demand model against, so this dataset exists to make that simulation
possible at all, with every assumption spelled out here rather than
buried in a formula (see the dataset card).

Usage:
    uv run datasets/pricing/generate.py
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

SEED = 20260704
PRODUCTS_PATH = Path(__file__).parents[1] / "products" / "products.json"
OUTPUT_PATH = Path(__file__).parent / "pricing_inputs.json"

# Per-category baseline elasticity (|% change in quantity| / |% change in
# price|) and marginal-cost ratio (cost as a fraction of current price).
# Necessities (Grocery, Pet Supplies) are modeled as less price-sensitive
# than discretionary categories (Electronics, Beauty, Toys) — a common
# qualitative assumption in economics teaching material, not a fitted
# estimate. Elasticity is bounded above 1 (below "unit elastic") because
# the monopoly markup rule this dataset feeds (see
# training/pricing/simulate.py) is only defined for elastic demand.
CATEGORY_ELASTICITY: dict[str, tuple[float, float]] = {
    "Electronics": (1.8, 3.2),
    "Home & Kitchen": (1.5, 2.6),
    "Books": (1.3, 2.2),
    "Clothing": (1.6, 2.8),
    "Sports & Outdoors": (1.5, 2.6),
    "Beauty": (1.8, 3.0),
    "Toys": (1.7, 2.9),
    "Grocery": (1.15, 1.8),
    "Office Supplies": (1.4, 2.4),
    "Pet Supplies": (1.2, 2.0),
}

CATEGORY_COST_RATIO: dict[str, tuple[float, float]] = {
    "Electronics": (0.45, 0.70),
    "Home & Kitchen": (0.35, 0.60),
    "Books": (0.30, 0.50),
    "Clothing": (0.25, 0.50),
    "Sports & Outdoors": (0.35, 0.60),
    "Beauty": (0.20, 0.45),
    "Toys": (0.30, 0.55),
    "Grocery": (0.40, 0.65),
    "Office Supplies": (0.35, 0.60),
    "Pet Supplies": (0.35, 0.60),
}

CATEGORY_MONTHLY_DEMAND: dict[str, tuple[int, int]] = {
    "Electronics": (40, 400),
    "Home & Kitchen": (60, 500),
    "Books": (20, 200),
    "Clothing": (80, 600),
    "Sports & Outdoors": (30, 300),
    "Beauty": (100, 700),
    "Toys": (50, 400),
    "Grocery": (200, 1500),
    "Office Supplies": (40, 350),
    "Pet Supplies": (60, 450),
}


@dataclass
class PricingInput:
    product_id: str
    elasticity: float
    marginal_cost: float
    reference_price: float
    reference_quantity: int


def generate_pricing_inputs(seed: int = SEED) -> list[PricingInput]:
    rng = random.Random(seed)
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))

    inputs: list[PricingInput] = []
    for product in products:
        category = product["category"]
        elasticity_range = CATEGORY_ELASTICITY[category]
        cost_ratio_range = CATEGORY_COST_RATIO[category]
        demand_range = CATEGORY_MONTHLY_DEMAND[category]

        elasticity = round(rng.uniform(*elasticity_range), 2)
        cost_ratio = round(rng.uniform(*cost_ratio_range), 3)
        price = product["price"]

        inputs.append(
            PricingInput(
                product_id=product["id"],
                elasticity=elasticity,
                marginal_cost=round(price * cost_ratio, 2),
                reference_price=price,
                reference_quantity=rng.randint(*demand_range),
            )
        )

    return inputs


def main() -> None:
    inputs = generate_pricing_inputs()
    OUTPUT_PATH.write_text(
        json.dumps([asdict(i) for i in inputs], indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated pricing inputs for {len(inputs)} products -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
