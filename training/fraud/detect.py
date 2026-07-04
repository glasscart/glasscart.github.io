"""Offline, rule-based fraud scoring over the synthetic transaction log.

Three surface-feature indicators, combined into a weighted fraud score —
no trained model, no PyTorch, no paid API. Real production fraud systems
use exactly these kinds of velocity/behavioral rules as a first line,
often ahead of (or alongside) any learned model, precisely because they're
cheap, fast, and fully explainable (see docs/research/fraud.md):

1. **Velocity**: how many transactions the same buyer made within a short
   rolling time window — the classic card-testing signature.
2. **Region-mismatch risk**: a shipping/billing region mismatch, weighted
   higher when combined with a newish account.
3. **New-account high-value purchase**: a newish account making an
   unusually large purchase.

None of these read datasets/transactions/generate.py's `is_fraud_synthetic`
ground-truth field — only surface features every real payment processor
actually has access to. That field is used strictly for the evaluation
this script reports (see "Metrics" in models/fraud/MODEL_CARD.md for the
same circularity caveat datasets/reviews/ and training/reviews/ carry).

Usage:
    uv run training/fraud/detect.py
"""

from __future__ import annotations

import json
import platform
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

TRANSACTIONS_PATH = Path(__file__).parents[2] / "datasets" / "transactions" / "transactions.json"
OUTPUT_DIR = Path(__file__).parents[2] / "models" / "fraud"
SCORES_PATH = OUTPUT_DIR / "fraud_scores.json"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"

VELOCITY_WINDOW = timedelta(minutes=15)
WEIGHT_VELOCITY = 0.55
WEIGHT_REGION_RISK = 0.30
WEIGHT_NEW_ACCOUNT_HIGH_VALUE = 0.25
FRAUD_SCORE_THRESHOLD = 0.5

NEW_ACCOUNT_DAYS = 14
HIGH_VALUE_AMOUNT = 150.0


@dataclass
class FraudScore:
    transaction_id: str
    buyer_id: str
    velocity_indicator: float
    region_risk_indicator: float
    new_account_high_value_indicator: float
    fraud_score: float
    likely_fraud: bool
    is_fraud_synthetic: bool  # carried through for the evaluation report only


def _velocity_indicators(transactions: list[dict]) -> dict[str, float]:
    """For each transaction, how many *other* transactions the same buyer
    made within VELOCITY_WINDOW of it (in either direction)."""
    by_buyer: dict[str, list[dict]] = defaultdict(list)
    for t in transactions:
        by_buyer[t["buyer_id"]].append(t)

    indicators: dict[str, float] = {}
    for buyer_txs in by_buyer.values():
        times = [(t, datetime.fromisoformat(t["created_at"])) for t in buyer_txs]
        for t, at in times:
            nearby = sum(1 for _, other_at in times if abs((other_at - at)) <= VELOCITY_WINDOW) - 1
            if nearby >= 3:
                indicators[t["id"]] = 1.0
            elif nearby == 2:
                indicators[t["id"]] = 0.6
            elif nearby == 1:
                indicators[t["id"]] = 0.3
            else:
                indicators[t["id"]] = 0.0
    return indicators


def _region_risk(transaction: dict) -> float:
    mismatched = transaction["shipping_region"] != transaction["billing_region"]
    if not mismatched:
        return 0.0
    return 1.0 if transaction["buyer_account_age_days"] <= NEW_ACCOUNT_DAYS else 0.4


def _new_account_high_value(transaction: dict) -> float:
    if transaction["buyer_account_age_days"] <= NEW_ACCOUNT_DAYS and transaction["amount"] >= HIGH_VALUE_AMOUNT:
        return 1.0
    return 0.0


def evaluate(scores: list[FraudScore]) -> dict:
    tp = sum(1 for s in scores if s.likely_fraud and s.is_fraud_synthetic)
    fp = sum(1 for s in scores if s.likely_fraud and not s.is_fraud_synthetic)
    fn = sum(1 for s in scores if not s.likely_fraud and s.is_fraud_synthetic)
    tn = sum(1 for s in scores if not s.likely_fraud and not s.is_fraud_synthetic)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "caveat": (
            "Evaluated against this dataset's own synthetically-generated fraud patterns "
            "(card testing, region-mismatch), not real payment fraud — see models/fraud/MODEL_CARD.md."
        ),
    }


def build() -> None:
    started_at = datetime.now().astimezone()
    transactions = json.loads(TRANSACTIONS_PATH.read_text(encoding="utf-8"))
    velocity = _velocity_indicators(transactions)

    scores: list[FraudScore] = []
    for t in transactions:
        velocity_indicator = velocity[t["id"]]
        region_risk_indicator = _region_risk(t)
        new_account_indicator = _new_account_high_value(t)
        fraud_score = round(
            WEIGHT_VELOCITY * velocity_indicator
            + WEIGHT_REGION_RISK * region_risk_indicator
            + WEIGHT_NEW_ACCOUNT_HIGH_VALUE * new_account_indicator,
            3,
        )
        scores.append(
            FraudScore(
                transaction_id=t["id"],
                buyer_id=t["buyer_id"],
                velocity_indicator=velocity_indicator,
                region_risk_indicator=region_risk_indicator,
                new_account_high_value_indicator=new_account_indicator,
                fraud_score=fraud_score,
                likely_fraud=fraud_score >= FRAUD_SCORE_THRESHOLD,
                is_fraud_synthetic=t["is_fraud_synthetic"],
            )
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCORES_PATH.write_text(
        json.dumps(
            [
                {
                    "transaction_id": s.transaction_id,
                    "fraud_score": s.fraud_score,
                    "likely_fraud": s.likely_fraud,
                    "indicators": {
                        "velocity": s.velocity_indicator,
                        "region_risk": s.region_risk_indicator,
                        "new_account_high_value": s.new_account_high_value_indicator,
                    },
                }
                for s in scores
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    evaluation = evaluate(scores)
    finished_at = datetime.now().astimezone()
    manifest = {
        "methodology": {
            "velocity": f"count of same-buyer transactions within a {VELOCITY_WINDOW.total_seconds() / 60:.0f}-minute window",
            "region_risk": "shipping/billing region mismatch, weighted higher for newer accounts",
            "new_account_high_value": f"account age <= {NEW_ACCOUNT_DAYS} days and amount >= ${HIGH_VALUE_AMOUNT}",
        },
        "weights": {
            "velocity": WEIGHT_VELOCITY,
            "region_risk": WEIGHT_REGION_RISK,
            "new_account_high_value": WEIGHT_NEW_ACCOUNT_HIGH_VALUE,
        },
        "fraud_score_threshold": FRAUD_SCORE_THRESHOLD,
        "num_transactions": len(transactions),
        "fraud_evaluation": evaluation,
        "generated_at": started_at.isoformat(),
        "build_duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "runtime": {"python": platform.python_version()},
        "dataset_seed": 20260704,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Scored {len(transactions)} transactions")
    print(f"Fraud heuristic: precision={evaluation['precision']}, recall={evaluation['recall']}, f1={evaluation['f1']}")
    print(f"-> {SCORES_PATH}\n-> {MANIFEST_PATH}")


if __name__ == "__main__":
    build()
