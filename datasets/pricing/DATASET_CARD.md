# Dataset Card: `pricing`

Following the spirit of [Datasheets for Datasets](https://arxiv.org/abs/1803.09010) (Gebru et al., 2018).

## Summary

A fully synthetic set of per-product pricing-simulation inputs — price elasticity of demand, marginal cost, and a reference monthly demand quantity — for every product in the [products dataset](../products/DATASET_CARD.md). **This dataset does not represent any real cost structure, demand, or market behavior.** GlassCart has no transaction history to fit a real demand model against; this dataset exists to make a pricing *simulation* possible at all (see [`training/pricing/simulate.py`](../../training/pricing/simulate.py)), with every assumption made explicit here instead of buried inside a formula.

## Schema

| Field                  | Type   | Description                                                                 |
|-------------------------|--------|-------------------------------------------------------------------------------|
| `product_id`            | string | Id of the product this input set applies to                                  |
| `elasticity`            | float  | Simulated \|price elasticity of demand\|, bounded above 1.0 (see "Provenance") |
| `marginal_cost`         | float  | Simulated cost per unit, USD (`price × a category-typical cost ratio`)        |
| `reference_price`       | float  | The product's current catalog price (copied from `products.json` for convenience) |
| `reference_quantity`    | int    | Simulated baseline monthly unit demand *at* `reference_price`                 |

## Provenance & Generation Process

Generated entirely by [`generate.py`](generate.py) with a fixed seed (`20260704`), so **the dataset is byte-for-byte reproducible**:

```bash
uv run datasets/pricing/generate.py
```

For each product, the generator samples:
1. **Elasticity** from a category-specific range (e.g. Grocery 1.15–1.8, Electronics 1.8–3.2) — necessities modeled as less price-sensitive than discretionary categories, a common qualitative assumption in economics teaching material, not a fitted estimate from any real data. Elasticity is kept strictly above 1.0 (elastic demand) because the profit-maximizing markup formula used downstream (the Lerner-index / monopoly markup rule) is only defined for elastic demand — see the [pricing model card](../../models/pricing/MODEL_CARD.md).
2. **Marginal cost** as the product's current price times a category-specific cost-ratio range (e.g. Beauty 0.20–0.45, Electronics 0.45–0.70).
3. **Reference quantity** from a category-specific typical-monthly-volume range, independent of any other field in the catalog (in particular, *not* derived from `rating_count` — conflating a rating-count proxy with a demand simulation would imply a relationship between the two that was never modeled).

No network access, no external API keys, and no manual curation are required.

## Intended Use

- Input to the pricing subsystem's demand/profit simulation (see [docs/subsystems/pricing.md](../../docs/subsystems/pricing.md)) — a teaching example of applying a real economic formula (constant-elasticity monopoly pricing) to clearly-labeled synthetic inputs, in the absence of real transaction data.

## Non-Intended Use

- Not intended to represent real costs, real demand, or real price sensitivity for any product, category, or market. Do not use this dataset, or any pricing recommendation derived from it, to make a real pricing decision.
- Not a benchmark dataset for demand-estimation or pricing-optimization research.

## Limitations & Bias Discussion

- **Category elasticity/cost ranges are hand-authored**, reflecting the GlassCart maintainers' general, textbook-level intuitions about which categories tend to be more or less price-sensitive — not fit to any real market research.
- **Elasticity is assumed constant** (a single number per product, not a function of price) — real demand curves usually have elasticity that varies with price level; this is the standard simplifying assumption behind the "constant-elasticity demand curve" model used downstream, not a claim that real elasticity is actually constant.
- **No cross-product effects**: each product's simulated demand depends only on its own price, ignoring substitution/complementary effects between products (e.g. a cheaper competing product in the same category would, in reality, affect this one's demand).
- **Reference quantity is an assumption, not a projection**: it does not correlate with the product's actual `rating`/`rating_count` in the products dataset, and shouldn't be read as a sales forecast.

## Regeneration / Extension Instructions

To change the elasticity/cost/demand ranges per category, edit the constants at the top of [`generate.py`](generate.py) and re-run:

```bash
uv run datasets/products/generate.py     # if the product catalog itself changed
uv run datasets/pricing/generate.py
uv run training/pricing/simulate.py      # rebuild pricing recommendations
```
