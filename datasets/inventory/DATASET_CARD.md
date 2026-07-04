# Dataset Card: `inventory`

Following the spirit of [Datasheets for Datasets](https://arxiv.org/abs/1803.09010) (Gebru et al., 2018).

## Summary

A fully synthetic 90-day daily sales + stock-level history (28,080 product-days) for every product in the [products dataset](../products/DATASET_CARD.md). **GlassCart has no real sales history** — the product catalog only ever carries a static aggregate `rating`/`rating_count`, never a time series. This dataset exists so the inventory-forecasting subsystem has something realistic-shaped to forecast against, the same reason [`datasets/transactions/`](../transactions/DATASET_CARD.md) exists for fraud detection.

## Schema

| Field           | Type    | Description                                                                 |
|------------------|---------|--------------------------------------------------------------------------------|
| `product_id`     | string  | Id of the product                                                              |
| `date`           | string  | ISO date (90 consecutive days per product, ending 2026-07-04)                  |
| `units_sold`     | int     | Units sold that day (capped by available stock — see "Provenance")            |
| `stock_level`    | int     | End-of-day stock level, after sales and any same-day restock                   |
| `stockout`       | bool    | True if that day's *true* demand exceeded available stock — `units_sold` undercounts true demand on these days (demand is *censored*, not observed) |
| `restocked`      | bool    | True if a pending restock order arrived and replenished stock that day        |

## Provenance & Generation Process

Generated entirely by [`generate.py`](generate.py) with a fixed seed (`20260704`), so **the dataset is byte-for-byte reproducible**:

```bash
uv run datasets/inventory/generate.py
```

For each product, the generator simulates a 90-day period with:
1. A **category-level baseline daily demand rate** (e.g. Grocery ~5 units/day, Books ~0.6/day), scaled by per-product variation.
2. A **linear trend** (−25% to +35% drift in demand over the 90 days), randomized per product.
3. **Weekly seasonality**: a category-specific weekend multiplier (Beauty/Toys/Sports skew toward weekends; Office Supplies skews toward weekdays) — not a single global pattern, since real seasonal skew genuinely varies by what's being bought.
4. **Stock depletion and periodic restocking**: each day's demand (`Gaussian(λ, √λ)`, floored at 0) is served from available stock; if demand exceeds stock, the day is marked `stockout` and `units_sold` is capped at whatever was available — true demand on stockout days is **not recoverable** from this data, matching a real, well-known complication in inventory forecasting (censored demand). A restock order is placed once stock drops below roughly one lead-time's worth of demand, arriving 5–12 days later and topping stock back up to ~25–35 days of typical demand.

No network access, no external API keys, and no manual curation are required.

## Intended Use

- Input time series for the inventory-forecasting subsystem (see [docs/subsystems/inventory.md](../../docs/subsystems/inventory.md)): demand forecasting and reorder-point calculation.
- Teaching example of a synthetic dataset that includes a real, well-known data-quality complication (censored demand on stockout days) rather than a clean, idealized signal — a forecasting method that ignores this will be measurably worse, which is the point.

## Non-Intended Use

- Not intended to represent real sales, real stock levels, or real seasonal demand patterns for any product or category. Do not use this dataset to draw conclusions about real retail demand.
- Not a benchmark dataset for academic demand-forecasting research — trend/seasonality parameters are hand-picked, not fit to any real market.

## Limitations & Bias Discussion

- **Category demand/seasonality parameters are hand-authored**, reflecting the maintainers' general intuitions (e.g. "Beauty skews weekend"), not real point-of-sale data.
- **Only 90 days of history** — too short to reliably separate a real trend from noise, or to observe more than one full monthly/seasonal cycle, which any forecasting method built on this data should account for.
- **No cross-product or promotional effects**: no discounts, no marketing campaigns, no substitution when a related product stocks out — this dataset's only two sales-affecting parameters are trend and weekly seasonality.
- **Restock quantities/lead times are simplified**: real supply chains have variable lead times, minimum order quantities, and supplier constraints none of which are modeled here.

## Regeneration / Extension Instructions

To change the simulation period, demand rates, seasonality, or restock policy, edit the constants at the top of [`generate.py`](generate.py) and re-run:

```bash
uv run datasets/products/generate.py       # if the product catalog itself changed
uv run datasets/inventory/generate.py
uv run training/inventory/forecast.py      # rebuild forecast/reorder artifacts
```
