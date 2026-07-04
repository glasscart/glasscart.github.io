# Subsystem: Demand-Driven Pricing Simulation

## What problem does this solve?

Sellers price products by intuition far more often than by any explicit model of how demand responds to price. This subsystem demonstrates what a demand-driven pricing tool looks like and how it reasons: given a price elasticity and a cost, it computes the price that would maximize profit under a standard economic model, and shows the shape of the demand/revenue/profit trade-off around the current price.

## Why does it exist (in this form)?

The [roadmap](../roadmap.md) is explicit that pricing should be "elasticity/demand-driven pricing simulation, explicitly labeled as simulation where there's no real transaction data to model against" — the one subsystem in GlassCart's guiding rule that takes the "explicitly-labeled-simulated, with a pointer to a real reference" branch instead of the "real implementation" branch search/recommendations/ranking/reviews all use. There is no honest way to build a *real* demand model without real sales history, so this subsystem instead applies a real, citable economic formula (see [docs/research/pricing.md](../research/pricing.md)) to synthetic inputs it's upfront about having made up.

## How does it work?

1. [`datasets/pricing/generate.py`](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/pricing/generate.py) simulates, per product, a price elasticity of demand, a marginal cost, and a reference monthly demand quantity — category-varied, seeded, and explicitly labeled as synthetic (see the [dataset card](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/pricing/DATASET_CARD.md)).
2. [`training/pricing/simulate.py`](https://github.com/glasscart/glasscart.github.io/blob/main/training/pricing/simulate.py) treats each product's simulated inputs as anchoring a constant-elasticity demand curve, `Q(p) = Q0·(p/p0)^(-e)`, and applies the classic monopoly markup rule, `p* = c·e/(e-1)`, to find the profit-maximizing price. It also samples a 7-point price-response curve (0.7×–1.3× the current price) showing quantity/revenue/profit at each point.
3. The output — current vs. optimal price/quantity/revenue/profit, a raise/lower/near-optimal recommendation, and the response curve — is rendered in a Glass Mode-only panel on the product detail page. Unlike reviews or recommendations, this is never shown to a regular shopper: a synthetic "you should charge more" signal would be actively misleading outside a panel that makes the simulation explicit.

## Why this implementation was chosen (vs. alternatives)

| Alternative | Why not (for this slice) |
|---|---|
| A learned demand model (regression/ML fit to transaction history) | GlassCart has no transaction history — training a "real" model on synthetic sales data would misrepresent a real technique as validated against evidence it never actually had. |
| Hiding the pricing subsystem entirely until real data exists | Would forgo a genuinely educational demonstration of a real, well-known pricing formula — the roadmap's "explicitly-labeled-simulated" option exists precisely so a subsystem like this can still be built honestly. |
| A linear (rather than constant-elasticity) demand curve | Constant elasticity is the standard choice when a single elasticity number is meant to characterize a whole demand curve (see [docs/research/pricing.md](../research/pricing.md) §2) — a linear curve's elasticity varies by price point, which doesn't match having one elasticity value per product. |
| Showing this to shoppers as a "price drops soon" signal | Would present a synthetic simulation as a real promise about future pricing — restricting it to a Glass Mode diagnostic avoids that entirely. |

## Strengths

- The optimization step is real, citable economics (the Lerner-index monopoly markup rule), not an invented heuristic — see [docs/research/pricing.md](../research/pricing.md) §3.
- Every number shown is traceable to a simple formula over a small set of clearly-labeled synthetic inputs — nothing is a black-box output.
- Gating the whole feature behind Glass Mode is itself a transparency decision, not just a UI choice: it prevents a synthetic recommendation from being mistaken for a real one.

## Weaknesses & known failure cases

- Every input (elasticity, marginal cost, reference demand) is synthetic — see the [dataset card](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/pricing/DATASET_CARD.md)'s Limitations section.
- Constant elasticity, no cross-product effects, and no inventory/competitor/seasonal signal are all real simplifications relative to how actual dynamic pricing systems work (see [docs/research/pricing.md](../research/pricing.md) §4).
- Elasticity is constrained above 1.0 purely so the markup formula stays defined — a modeling convenience, not a claim about real elasticity distributions.

## How it could be improved

- If GlassCart ever simulates transaction/click data for other subsystems (see the roadmap's "later" bucket), revisit this with an *estimated* elasticity rather than an assumed one — the optimization logic here wouldn't need to change, only where its inputs come from.
- Add cross-product substitution effects for products in the same category.
- Show the full price-response curve as a real chart rather than a table.

## Where to look in the code

| Concern | Offline (Python) | Client (TypeScript) |
|---|---|---|
| Synthetic inputs | `datasets/pricing/generate.py` | — |
| Demand curve + markup rule + build | `training/pricing/simulate.py` | — |
| UI (Glass Mode only) | — | `apps/web/src/components/PricingInsightsPanel.tsx` |
| Wired into | — | `apps/web/src/pages/ProductDetailPage.tsx` |

## Further reading

See the full [research bibliography for pricing](../research/pricing.md) for primary sources on price elasticity, constant-elasticity demand curves, the Lerner Index / monopoly markup rule, and how real dynamic-pricing systems differ from this simulation.
