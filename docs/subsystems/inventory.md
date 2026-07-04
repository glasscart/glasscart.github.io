# Subsystem: Demand Forecasting & Reorder-Point Inventory Management

## What problem does this solve?

Real sellers need to know two things: how much of a product will sell in the near future, and when to reorder stock so it doesn't run out before the next delivery arrives. GlassCart has no real sales history to answer either question — this subsystem demonstrates the classical techniques that would answer them, against a purpose-built synthetic sales/stock time series.

## Why does it exist (in this form)?

The roadmap's "later" bucket lists inventory forecasting as needing foundational data (historical sales/stock) that didn't exist in the catalog. Rather than leave it blocked, this subsystem builds that foundational data first — [`datasets/inventory/`](https://github.com/glasscart/glasscart.github.io/tree/main/datasets/inventory) — the same move already made for reviews, pricing, and fraud. Because there's still no real checkout or warehouse system anywhere in GlassCart, this subsystem's UI lives on its own small, Glass Mode-gated `/inventory` ops page, alongside `/transactions`.

## How does it work?

1. [`datasets/inventory/generate.py`](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/inventory/generate.py) simulates 90 days of daily sales and stock levels per product — with a trend, category-specific weekly seasonality, and periodic restocking that can still run out early if demand spikes (producing genuinely censored demand on stockout days). See the [dataset card](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/inventory/DATASET_CARD.md).
2. [`training/inventory/forecast.py`](https://github.com/glasscart/glasscart.github.io/blob/main/training/inventory/forecast.py) forecasts each product's future daily demand with Holt's linear exponential smoothing over a weekly-deseasonalized series, correcting for censored stockout days, then computes a reorder point using the standard formula from inventory theory. See [docs/research/inventory.md](../research/inventory.md) for the primary sources behind each piece.
3. The `/inventory` page renders every product's current stock, forecasted demand, days of supply, and reorder flag, gated behind Glass Mode — an internal/ops-style view, not a shopper-facing feature.

## Why this implementation was chosen (vs. alternatives)

| Alternative | Why not (for this slice) |
|---|---|
| A trained ML forecasting model (e.g. gradient-boosted trees on lagged features) | No real sales history exists to train or validate one against; a classical statistical method that's still genuinely used in practice is the more honest choice for synthetic data this shape. |
| Ignoring the stockout/censored-demand complication | Would be a cleaner implementation but a less realistic (and less interesting) one — real inventory forecasting has to deal with exactly this problem, and the dataset was built specifically to include it. |
| Full Holt-Winters (adaptively-estimated seasonality) | 90 days is only ~12–13 weeks — too short to reliably re-estimate a seasonal component as the smoothing progresses; a static seasonal index computed once from the full history is the better-justified choice at this data volume. |
| Using the generator's true per-product lead time in the reorder-point formula | Would mean secretly reading simulation ground truth rather than analyzing observable data — a real ops team knows its own contracted lead time, but a forecasting method shouldn't assume access to the simulator's internals. An assumed fixed lead time is used instead, documented as a limitation. |

## Strengths

- Every technique (Holt's method, the reorder-point formula, the seasonal index) is a direct, unmodified implementation of a real, citable, still-practiced inventory-management method — not invented for this project.
- Directly engages with a real data-quality problem (censored demand) instead of simulating it away.
- Fully deterministic and inspectable: no ML training, no black-box model, every number traces to a documented formula.

## Weaknesses & known failure cases

- Lead time is a hand-set assumption (7 days for every product), not measured — see the [model card](https://github.com/glasscart/glasscart.github.io/blob/main/models/inventory/MODEL_CARD.md).
- Only 90 days of synthetic history — too short to fully validate a trend or seasonal estimate.
- No forecast-accuracy metric is reported against real held-out data, since none exists; only internal consistency was checked (see the model card's Metrics section).
- No cross-product substitution, promotions, or supply-chain constraints (minimum order quantities, variable lead times) are modeled.

## How it could be improved

- If GlassCart ever simulates a longer sales history or real interaction data, revisit forecast accuracy against genuinely held-out periods.
- Add prediction intervals around the point forecast, not just a safety-stock margin on the reorder point.
- Model supplier lead-time variability instead of a single fixed assumption.

## Where to look in the code

| Concern | Offline (Python) | Client (TypeScript) |
|---|---|---|
| Synthetic sales/stock history | `datasets/inventory/generate.py` | — |
| Forecasting + reorder point + build | `training/inventory/forecast.py` | — |
| UI (Glass Mode only) | — | `apps/web/src/pages/InventoryPage.tsx`, `GlassInventoryPanel.tsx` |

## Further reading

See the full [research bibliography for inventory](../research/inventory.md) for primary sources on exponential smoothing, Holt's method, seasonal decomposition, censored demand, and the reorder-point formula.
