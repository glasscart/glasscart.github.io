# Model Card: `pricing` (constant-elasticity demand simulation + monopoly markup rule)

Following the structure proposed by [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993) (Mitchell et al., 2019).

> **This is an explicitly-labeled simulation, not a trained model and not a real pricing tool.** GlassCart has no transaction data to fit a demand model against, so every elasticity, cost, and demand number this pipeline uses is synthetic (see [datasets/pricing/DATASET_CARD.md](../../datasets/pricing/DATASET_CARD.md)). What's real is the economics applied to those synthetic inputs — see "Architecture." Per the [roadmap](../../docs/roadmap.md), this fulfills the "explicitly-labeled-simulated, with a pointer to a real reference" option in the project's guiding rule, rather than the "real implementation" option search/recommendations/ranking/reviews use.

## Purpose

Show what a demand-driven pricing simulation looks like and how it reasons: given a price elasticity of demand and a marginal cost, compute the profit-maximizing price and show the shape of the demand/revenue/profit trade-off around a product's current price — entirely as an illustrative Glass Mode panel, never presented to a shopper as a real recommendation.

## Architecture

- **Demand model**: a constant-elasticity demand curve, `Q(p) = Q0 * (p / p0)^(-e)`, where `p0`/`Q0` are the product's reference price/quantity and `e` is its elasticity (all from [`datasets/pricing/pricing_inputs.json`](../../datasets/pricing/pricing_inputs.json)). This is the standard textbook demand-curve form used whenever "constant elasticity" is assumed — real, not invented for this project.
- **Pricing rule**: the monopoly markup rule (equivalently, the Lerner index solved for price): `p* = c * e / (e - 1)`, valid for `e > 1` (elastic demand). This is the closed-form profit-maximizing price under a constant-elasticity demand curve and a constant marginal cost `c` — a standard result in microeconomics (see [docs/research/pricing.md](../../docs/research/pricing.md) for the derivation and primary sources), not a heuristic invented for GlassCart.
- **Output per product**: current vs. optimal price/quantity/revenue/profit, the % price change and % profit uplift the optimum implies, a coarse recommendation (`raise` / `lower` / `near-optimal`, thresholded at ±5%), and a 7-point price-response curve (0.7×–1.3× the reference price) for the UI to render as a simple table.

## Training Data

None — there is no training step. `training/pricing/simulate.py` is a deterministic function evaluated over `datasets/pricing/pricing_inputs.json`'s synthetic elasticity/cost/demand values; nothing is fit, estimated, or learned from data.

## What GlassCart Does With It

`training/pricing/simulate.py` reads the pricing inputs and every product's current price, computes the optimal price and the response curve, and writes `models/pricing/pricing_recommendations.json` plus a `manifest.json` (methodology, thresholds, and how many products fell into each recommendation bucket). `apps/web/src/components/PricingInsightsPanel.tsx` renders this on the product detail page, **visible only when Glass Mode is on** — unlike reviews or recommendations, this isn't a shopper-facing feature; it's a transparency panel showing how a demand-driven pricing tool would reason, clearly labeled as simulated throughout.

## Metrics

No accuracy metric applies — there is no real demand or real profit to measure this simulation against. What can be verified is internal consistency: for every product, `optimal_profit >= current_profit` should hold by construction (the markup rule is derived by maximizing the profit function directly), which was spot-checked across sampled products during development. This is a sanity check on the arithmetic, not a claim of real-world validity.

## Confidence & Uncertainty

Not applicable in the usual sense — there is no distribution being estimated, so there's no uncertainty to quantify. The entire simulation's "uncertainty" is that its inputs are made up; that's stated as plainly as possible everywhere this output is shown, rather than attached as a numeric confidence interval that would imply more rigor than exists.

## Hardware Used

Pure Python, stdlib only — no GPU, no ML framework, negligible runtime (312 products simulate in well under a second).

## Known Limitations & Failure Cases

- **Every input is synthetic** (elasticity, marginal cost, reference demand) — see [datasets/pricing/DATASET_CARD.md](../../datasets/pricing/DATASET_CARD.md)'s Limitations section for the full list of what that means in practice.
- **Constant elasticity is a simplifying assumption**: real elasticity typically varies with price level; this model assumes it doesn't.
- **No cross-product effects**: each product is priced independently, ignoring substitution or complementary-goods effects between products in the catalog.
- **No inventory, competitor, or seasonal signal**: the simulation only ever looks at one product's own elasticity/cost/reference demand.
- **The `e > 1` constraint is a modeling convenience**, not a claim that all real products face elastic demand — the dataset generator simply never produces `e <= 1` inputs, sidestepping (not solving) the case where the markup formula is undefined.

## Ethical & Privacy Considerations

- No real cost, sales, or competitor data is used or could be inferred from this pipeline — every number is synthetic and clearly labeled as such.
- This output is never shown to anyone shopping the site — it's a Glass Mode-only panel, specifically to avoid presenting a synthetic "you should charge more" signal as real seller guidance.

## Intended Use

Teaching example of applying a real, citable economic pricing formula to honestly-synthetic inputs, and of using Glass Mode to gate a feature that would be actively misleading if shown outside a clearly-labeled "this is simulated" context.

## Non-Intended Use

Not intended for, and must not be used for, any real pricing decision. Not validated against any real elasticity estimate, real cost structure, or real demand data.

## Reproducibility

```bash
uv sync
uv run datasets/products/generate.py     # if the product catalog changed
uv run datasets/pricing/generate.py      # regenerate synthetic elasticity/cost/demand inputs
uv run training/pricing/simulate.py      # rebuild pricing recommendations
uv run scripts/sync_web_data.py          # publish artifacts to apps/web/public/data
```

Re-running `simulate.py` against unchanged inputs produces byte-identical output (a pure deterministic function, no randomness).
