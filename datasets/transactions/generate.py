"""Synthetic transaction log generator for GlassCart.

Generates a deterministic, seeded set of purchase transactions against the
existing product catalog. GlassCart has no real checkout flow or payment
processor — no real transaction ever happens on this site — so this
dataset exists purely to give the fraud-detection subsystem
(training/fraud/) something to run against. No real buyers, payment
instruments, or transactions are represented.

As with datasets/reviews/generate.py, two fraud patterns are deliberately
engineered rather than left to chance, each modeled on a real, documented
type of payment fraud (see docs/research/fraud.md):

1. **Card testing**: a brand-new synthetic account makes a burst of
   several small transactions within minutes, often across unrelated
   products — the classic signature of testing whether a stolen card
   number still works before attempting a larger purchase.
2. **Mismatched-region high-value purchase**: a relatively new account
   makes one unusually large purchase with a shipping region different
   from its billing region — a classic "ship to a different address than
   the cardholder's" fraud tell.

Every fraud transaction is tagged `is_fraud_synthetic: true` — a
ground-truth label used only to *evaluate* the fraud heuristic in
training/fraud/detect.py, never fed into it (same rule as reviews'
`is_fake_synthetic`, see that dataset card for why the distinction
matters).

Usage:
    uv run datasets/transactions/generate.py
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path

SEED = 20260704
PRODUCTS_PATH = Path(__file__).parents[1] / "products" / "products.json"
OUTPUT_PATH = Path(__file__).parent / "transactions.json"

NUM_BUYERS = 600
NUM_LEGIT_TRANSACTIONS = 2200
NUM_CARD_TESTING_RINGS = 18  # each ring = one burst of several small transactions
NUM_MISMATCHED_REGION_FRAUDS = 45

REGIONS = ["US-West", "US-East", "US-South", "US-Central", "EU-West", "APAC"]
PAYMENT_METHODS = ["credit_card", "debit_card", "digital_wallet", "gift_card"]

# Genuine transactions occasionally still have a shipping/billing mismatch
# (gifts, travel) — kept nonzero deliberately so region-mismatch alone
# isn't a perfect fraud signal, which would make the heuristic's job
# artificially easy in a different way than reviews' generic-text signal.
LEGIT_REGION_MISMATCH_RATE = 0.04


@dataclass
class Buyer:
    id: str
    home_region: str
    account_created: datetime


@dataclass
class Transaction:
    id: str
    product_id: str
    buyer_id: str
    quantity: int
    amount: float
    payment_method: str
    shipping_region: str
    billing_region: str
    buyer_account_age_days: int
    created_at: str
    is_fraud_synthetic: bool


def _make_buyers(rng: random.Random, base_date: datetime) -> list[Buyer]:
    buyers = []
    for i in range(NUM_BUYERS):
        created = base_date - timedelta(days=rng.randint(1, 900))
        buyers.append(Buyer(id=f"B{i:04d}", home_region=rng.choice(REGIONS), account_created=created))
    return buyers


def _account_age_days(buyer: Buyer, at: datetime) -> int:
    return max(0, (at - buyer.account_created).days)


def _legit_transaction(rng: random.Random, products: list[dict], buyer: Buyer, at: datetime, index: int) -> Transaction:
    product = rng.choice(products)
    quantity = rng.choice([1, 1, 1, 2, 2, 3])
    mismatched = rng.random() < LEGIT_REGION_MISMATCH_RATE
    shipping_region = rng.choice(REGIONS) if mismatched else buyer.home_region
    return Transaction(
        id=f"TX{index:06d}",
        product_id=product["id"],
        buyer_id=buyer.id,
        quantity=quantity,
        amount=round(product["price"] * quantity, 2),
        payment_method=rng.choice(PAYMENT_METHODS),
        shipping_region=shipping_region,
        billing_region=buyer.home_region,
        buyer_account_age_days=_account_age_days(buyer, at),
        created_at=at.isoformat(timespec="minutes"),
        is_fraud_synthetic=False,
    )


def _card_testing_ring(rng: random.Random, products: list[dict], base_date: datetime, start_index: int) -> list[Transaction]:
    """A fresh account, several small transactions within a few minutes."""
    buyer_id = f"F{rng.randint(10000, 99999)}"
    burst_start = base_date - timedelta(days=rng.randint(0, 200))
    account_created = burst_start - timedelta(minutes=rng.randint(1, 30))
    region = rng.choice(REGIONS)
    n = rng.randint(4, 8)
    # The whole ring fits inside a tight window (well under VELOCITY_WINDOW
    # in training/fraud/detect.py) — real card-testing bursts are rapid-fire,
    # not spread over tens of minutes.
    txs = []
    for i in range(n):
        at = burst_start + timedelta(minutes=rng.uniform(0, 9))
        product = rng.choice(products)
        txs.append(
            Transaction(
                id=f"TX{start_index + i:06d}",
                product_id=product["id"],
                buyer_id=buyer_id,
                quantity=1,
                amount=round(min(product["price"], rng.uniform(3.0, 15.0)), 2),
                payment_method="credit_card",
                shipping_region=region,
                billing_region=region,
                buyer_account_age_days=max(0, (at - account_created).days),
                created_at=at.isoformat(timespec="minutes"),
                is_fraud_synthetic=True,
            )
        )
    return txs


def _mismatched_region_fraud(rng: random.Random, products: list[dict], base_date: datetime, index: int) -> Transaction:
    """A newish account makes one unusually large purchase shipped to a different region than billing."""
    account_created = base_date - timedelta(days=rng.randint(0, 10))
    at = base_date - timedelta(days=rng.randint(0, 200), hours=rng.randint(0, 23))
    product = max(rng.sample(products, k=5), key=lambda p: p["price"])
    quantity = rng.choice([1, 2])
    billing_region = rng.choice(REGIONS)
    shipping_region = rng.choice([r for r in REGIONS if r != billing_region])
    return Transaction(
        id=f"TX{index:06d}",
        product_id=product["id"],
        buyer_id=f"F{rng.randint(10000, 99999)}",
        quantity=quantity,
        amount=round(product["price"] * quantity, 2),
        payment_method="credit_card",
        shipping_region=shipping_region,
        billing_region=billing_region,
        buyer_account_age_days=max(0, (at - account_created).days),
        created_at=at.isoformat(timespec="minutes"),
        is_fraud_synthetic=True,
    )


def generate_transactions(seed: int = SEED) -> list[Transaction]:
    rng = random.Random(seed)
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    base_date = datetime(2026, 7, 4, 12, 0)
    buyers = _make_buyers(rng, base_date)

    transactions: list[Transaction] = []
    index = 0
    for _ in range(NUM_LEGIT_TRANSACTIONS):
        buyer = rng.choice(buyers)
        at = base_date - timedelta(days=rng.randint(0, 400), hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
        if at < buyer.account_created:
            at = buyer.account_created + timedelta(hours=rng.randint(1, 48))
        transactions.append(_legit_transaction(rng, products, buyer, at, index))
        index += 1

    for _ in range(NUM_CARD_TESTING_RINGS):
        ring = _card_testing_ring(rng, products, base_date, index)
        transactions.extend(ring)
        index += len(ring)

    for _ in range(NUM_MISMATCHED_REGION_FRAUDS):
        transactions.append(_mismatched_region_fraud(rng, products, base_date, index))
        index += 1

    transactions.sort(key=lambda t: t.created_at)
    return transactions


def main() -> None:
    transactions = generate_transactions()
    OUTPUT_PATH.write_text(
        json.dumps([asdict(t) for t in transactions], indent=2) + "\n",
        encoding="utf-8",
    )
    num_fraud = sum(1 for t in transactions if t.is_fraud_synthetic)
    print(f"Generated {len(transactions)} transactions ({num_fraud} synthetic fraud) -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
