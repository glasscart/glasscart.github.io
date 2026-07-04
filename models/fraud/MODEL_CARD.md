# Model Card: `fraud` (rule-based velocity + region-risk heuristic)

Following the structure proposed by [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993) (Mitchell et al., 2019).

> **Status: demo-only, no shopper-facing effect.** GlassCart has no real checkout, so this scores a synthetic transaction log (see [datasets/transactions/DATASET_CARD.md](../../datasets/transactions/DATASET_CARD.md)), not real purchases. It's surfaced only on a Glass Mode-gated `/transactions` page (see [docs/subsystems/fraud.md](../../docs/subsystems/fraud.md)) as a demonstration of what a first-line, rule-based fraud check looks like.

## Purpose

Show a real, production-representative fraud-detection technique — velocity checks and region-mismatch scoring — applied end-to-end, including an honest evaluation of where it succeeds and where it misses, on the only data available: a synthetic transaction log built for this purpose.

## Architecture

Three surface-feature indicators, each normalized to `[0, 1]`, combined as a weighted sum (`training/fraud/detect.py`):

- **Velocity** (weight `0.55`): how many transactions the same buyer made within a rolling 15-minute window — `1.0` at ≥3 nearby transactions, `0.6` at 2, `0.3` at 1. This is the classic card-testing signature.
- **Region risk** (weight `0.30`): `1.0` if shipping/billing regions differ *and* the account is ≤14 days old, `0.4` if they differ but the account is older, `0.0` otherwise.
- **New-account high-value** (weight `0.25`): `1.0` if the account is ≤14 days old *and* the transaction amount is ≥$150.

A transaction is flagged `likely_fraud` at a combined score ≥ `0.5`. All three indicators, and the technique of combining velocity + behavioral + value signals into a weighted rule score, are documented, real-world fraud-detection practice (see [docs/research/fraud.md](../../docs/research/fraud.md)) — not invented for this project.

## Training Data

None — no training happens. The three indicators are hand-set rules evaluated deterministically over `datasets/transactions/transactions.json`.

## What GlassCart Does With It

`training/fraud/detect.py` scores every transaction and writes `models/fraud/fraud_scores.json` (per-transaction indicator breakdown and flag) and `manifest.json` (methodology, weights, and an evaluation against the dataset's synthetic fraud labels). `apps/web/src/pages/TransactionsPage.tsx` — a small, Glass Mode-only "ops" view linked from the footer, not part of the shopper storefront — renders the transaction log with fraud scores and the methodology panel.

## Metrics

Evaluated against `datasets/transactions/transactions.json`'s synthetic `is_fraud_synthetic` labels (see `models/fraud/manifest.json`'s `fraud_evaluation` for the exact numbers from the last build):

| Metric | Value (typical) |
|---|---|
| Precision | ~0.99 |
| Recall | ~0.88 |
| F1 | ~0.93 |

Unlike the reviews subsystem's fake-review heuristic (which scores a suspicious 1.0/1.0/1.0 — see its model card), this one has genuine, documented misses: region-mismatch fraud transactions with an amount under the $150 high-value threshold score only `0.30` (region risk alone), below the `0.5` flag threshold, and are missed. This is reported because it's a more honest picture of a rule-based heuristic's real failure mode (a threshold-driven blind spot) than a perfect score would be — see "Known Limitations." As with reviews, **this still reflects the heuristic's own two engineered patterns**, not real-world fraud diversity — see "Non-Intended Use."

## Confidence & Uncertainty

Fraud scores are a weighted sum of normalized, non-probabilistic indicators in `[0, 1]`, shown with their component breakdown rather than as a calibrated probability of fraud.

## Hardware Used

Pure Python, stdlib only — no GPU, no ML framework, negligible runtime (the full transaction log scores in well under a second).

## Known Limitations & Failure Cases

- **Threshold blind spot (documented, not hypothetical)**: region-mismatch fraud under the $150 high-value threshold scores `0.30`, below the `0.5` flag threshold, and is missed — 18 of 149 synthetic fraud transactions in the last build, all of this exact shape. Lowering the threshold would catch these at the cost of more false positives on legitimate low-value region mismatches (gifts, travel).
- **Only two fraud patterns exist in the evaluation data** (card testing, region-mismatch) — see the [dataset card](../../datasets/transactions/DATASET_CARD.md). A heuristic performing well here has no demonstrated ability to catch fraud patterns outside these two.
- **Velocity window (15 minutes) and thresholds (14 days, $150) are hand-picked**, not fit to any real data or real cost/benefit analysis of false positives vs. false negatives.
- **No real payment-network signals** (card BIN, device fingerprinting, IP reputation, etc.) are available or used — real fraud systems draw on far more signal than this heuristic has access to.

## Ethical & Privacy Considerations

- All transactions, buyers, and fraud patterns are synthetic; no real payment or buyer data is processed anywhere in this pipeline.
- The heuristic only ever renders on a Glass Mode-gated internal/ops-style page, never surfaced to (or acting on) an actual shopper — there is no shopper-facing consequence of being flagged, since there is no real checkout for this to apply to.

## Intended Use

Demonstrating a real, representative first-line fraud-detection technique end-to-end — including generating the transaction data it needs, since none existed — with an honest account of a specific, reproducible failure mode rather than an implausibly perfect score.

## Non-Intended Use

Not intended for, and must not be used for, any real fraud-detection decision. Not validated against any real transaction data or real fraud pattern beyond the two hand-authored ones in `datasets/transactions/generate.py`.

## Reproducibility

```bash
uv sync
uv run datasets/products/generate.py       # if the product catalog changed
uv run datasets/transactions/generate.py   # regenerate the synthetic transaction log
uv run training/fraud/detect.py            # rebuild fraud-score artifacts
uv run scripts/sync_web_data.py            # publish artifacts to apps/web/public/data
```

Re-running `detect.py` against an unchanged transaction log produces byte-identical output (a pure deterministic function, no randomness).
