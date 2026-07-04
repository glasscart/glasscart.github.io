# Dataset Card: `transactions`

Following the spirit of [Datasheets for Datasets](https://arxiv.org/abs/1803.09010) (Gebru et al., 2018).

## Summary

A fully synthetic transaction log (~2,360 purchases) against the [products dataset](../products/DATASET_CARD.md). **GlassCart has no real checkout flow, payment processor, or buyers — no real transaction has ever happened on this site.** This dataset exists so the fraud-detection subsystem has something realistic-shaped to run against, the same reason [`datasets/reviews/`](../reviews/DATASET_CARD.md) exists for the reviews subsystem.

## Schema

| Field                    | Type    | Description                                                        |
|---------------------------|---------|----------------------------------------------------------------------|
| `id`                      | string  | Stable transaction id, e.g. `TX000042`                               |
| `product_id`              | string  | Id of the purchased product                                          |
| `buyer_id`                | string  | Synthetic buyer id (`B####` for the recurring buyer pool, `F#####` for one-off/fraud accounts) |
| `quantity`                | int     | Units purchased                                                       |
| `amount`                  | float   | USD, `price × quantity`                                              |
| `payment_method`          | string  | One of `credit_card`, `debit_card`, `digital_wallet`, `gift_card`     |
| `shipping_region`         | string  | One of 6 synthetic regions                                            |
| `billing_region`          | string  | One of 6 synthetic regions                                            |
| `buyer_account_age_days`  | int     | Days between the (synthetic) account's creation and this transaction |
| `created_at`              | string  | ISO datetime, minute precision                                       |
| `is_fraud_synthetic`      | bool    | **Ground-truth label, not a model output.** True for the ~7% of transactions deliberately generated to match one of two known fraud patterns (see "Provenance"). Used only to *evaluate* the fraud heuristic in [`training/fraud/detect.py`](../../training/fraud/detect.py) — the heuristic itself never reads this field, only the transaction's surface features (see the [model card](../../models/fraud/MODEL_CARD.md)). |

## Provenance & Generation Process

Generated entirely by [`generate.py`](generate.py) with a fixed seed (`20260704`), so **the dataset is byte-for-byte reproducible**:

```bash
uv run datasets/transactions/generate.py
```

The generator creates a pool of 600 synthetic recurring buyers (each with a home region and an account-creation date), then:
1. Generates ~2,200 genuine transactions: an existing buyer purchases 1–3 units of a random product, shipped to their home region except for a small (4%) rate of legitimate shipping/billing mismatches (gifts, travel) — kept nonzero deliberately so region mismatch alone isn't a perfect fraud signal.
2. Injects **card-testing rings**: a handful of brand-new accounts (0 days old) each make 4–8 small transactions within minutes of each other, the classic signature of testing whether a stolen card number still works.
3. Injects **mismatched-region high-value frauds**: a handful of newish accounts each make one unusually large purchase with a shipping region different from their billing region — a classic "ship to a different address than the cardholder's" tell.

No network access, no external API keys, and no manual curation are required.

## Intended Use

- Input corpus for the fraud-detection subsystem (see [docs/subsystems/fraud.md](../../docs/subsystems/fraud.md)): velocity-based and region-mismatch-based rule scoring.
- A held-out evaluation set for the fraud heuristic via the `is_fraud_synthetic` ground-truth field — see the [model card](../../models/fraud/MODEL_CARD.md)'s Metrics section for the same "evaluated against the generator's own synthetic pattern" caveat the reviews subsystem's fake-review heuristic carries.

## Non-Intended Use

- Not intended to represent real buyers, real payment behavior, or real fraud patterns. Do not use this dataset to draw conclusions about real payment fraud rates or techniques.
- Not a benchmark dataset for academic fraud-detection research — the two fraud patterns here are simple, hand-authored signatures, not representative of the sophistication or diversity of real payment fraud.

## Limitations & Bias Discussion

- **Only two fraud patterns exist**, both hand-authored and both well-known, textbook fraud signatures (card testing, region-mismatch). Real fraud is far more varied and adversarial; a heuristic that performs well here should not be assumed to generalize.
- **No real buyers, no real payment instruments, no real addresses** — every buyer, region, and account age is synthetic.
- **Region set is small (6 regions)** and arbitrary, not modeled on real geographic fraud-risk distributions.
- **Transaction volume is modest** (~2,360 over roughly 13 months of simulated activity) — too small to support any robust statistical fraud model even if one were appropriate here.

## Regeneration / Extension Instructions

To change the buyer pool size, transaction volume, fraud pattern parameters, or region list, edit the constants at the top of [`generate.py`](generate.py) and re-run:

```bash
uv run datasets/products/generate.py         # if the product catalog itself changed
uv run datasets/transactions/generate.py
uv run training/fraud/detect.py              # rebuild fraud-score artifacts
```
