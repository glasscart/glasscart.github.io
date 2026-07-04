# Subsystem: Transaction Fraud Detection

## What problem does this solve?

Real commerce platforms score every transaction for fraud risk before it settles. GlassCart has no real checkout, so there's no real transaction to score — this subsystem exists to demonstrate the technique (and its real limitations) end-to-end anyway, using a purpose-built synthetic transaction log.

## Why does it exist (in this form)?

The roadmap's "later" bucket lists fraud detection as needing "foundational data (transactions...) that doesn't exist in the catalog yet." Rather than leave it blocked indefinitely, this subsystem builds that foundational data first — [`datasets/transactions/`](https://github.com/glasscart/glasscart.github.io/tree/main/datasets/transactions) — the same move already made for reviews (see [docs/subsystems/reviews.md](reviews.md)) and pricing. Because there's still no real checkout flow anywhere in GlassCart, this subsystem's UI lives on its own small, Glass Mode-gated `/transactions` page rather than anywhere in the shopper storefront.

## How does it work?

1. [`datasets/transactions/generate.py`](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/transactions/generate.py) generates a synthetic transaction log with two deliberately engineered, real-world fraud patterns: card-testing rings (a fresh account making several small transactions within minutes) and mismatched-region high-value purchases (a newish account shipping to a different region than its billing address). See the [dataset card](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/transactions/DATASET_CARD.md).
2. [`training/fraud/detect.py`](https://github.com/glasscart/glasscart.github.io/blob/main/training/fraud/detect.py) scores every transaction with three weighted, hand-set indicators — velocity, region-risk, new-account-high-value — combined into a single fraud score, flagged above a threshold. See [docs/research/fraud.md](../research/fraud.md) for why each indicator reflects real fraud-detection practice.
3. The `/transactions` page renders the log with fraud scores, gated behind Glass Mode — this is an internal/ops-style view, not a shopper-facing feature, linked from the footer alongside "About this project."

## Why this implementation was chosen (vs. alternatives)

| Alternative | Why not (for this slice) |
|---|---|
| A trained fraud classifier | No real transaction data exists to train on; fabricating enough synthetic volume to train a model would risk the model just memorizing the two hand-authored patterns, no more informative than the rule-based version but far less transparent. |
| Leaving fraud detection blocked until real transactions exist | Forgoes a genuine demonstration of a real, representative technique — the same reasoning that motivated building the reviews and transactions datasets rather than waiting for real interaction data. |
| Building a full checkout flow to generate "real" transactions | Out of scope for a static, backend-free site, and a demo checkout still wouldn't produce real payment fraud — it would just be a different flavor of synthetic data. |

## Strengths

- Every indicator and weight is inspectable — a flagged transaction's score is a plain sum of named, documented rules.
- The two evaluation patterns are drawn from real, cited fraud-detection literature (card testing, address mismatch), not invented for this project.
- The evaluation reports a genuine, reproducible miss (see the [model card](https://github.com/glasscart/glasscart.github.io/blob/main/models/fraud/MODEL_CARD.md)'s Metrics section) rather than an implausible perfect score.

## Weaknesses & known failure cases

- Region-mismatch fraud below the $150 "high value" threshold is missed by design (region-risk alone doesn't cross the flag threshold) — a real, documented blind spot, not a hypothetical one.
- Only two fraud patterns exist in the evaluation data; a heuristic performing well here has no demonstrated ability to generalize to fraud patterns outside these two.
- Thresholds (15-minute velocity window, 14-day account age, $150 amount) are hand-picked, not fit to any real cost/benefit trade-off.

## How it could be improved

- Add more fraud patterns to the synthetic dataset (e.g. stolen-card-reuse-across-sellers, promo-code abuse) to stress-test the heuristic against more than two shapes.
- Tune the flag threshold against an explicit cost model (false-positive cost vs. false-negative cost) instead of a round number.
- If GlassCart ever adds a real (even if toy) checkout flow, revisit whether any of this heuristic's rules should gate a real action rather than only ever being displayed.

## Where to look in the code

| Concern | Offline (Python) | Client (TypeScript) |
|---|---|---|
| Synthetic transaction log | `datasets/transactions/generate.py` | — |
| Fraud scoring + build | `training/fraud/detect.py` | — |
| UI (Glass Mode only) | — | `apps/web/src/pages/TransactionsPage.tsx`, `GlassFraudPanel.tsx` |

## Further reading

See the full [research bibliography for fraud](../research/fraud.md) for primary sources on rule-based fraud detection, velocity/card-testing checks, and address-mismatch signals.
