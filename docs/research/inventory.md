# Research Notes: Demand Forecasting & Reorder-Point Inventory Management

> Bibliography and design rationale for GlassCart's inventory subsystem: Holt's linear
> exponential smoothing over a synthetic sales history, combined with the classical
> reorder-point formula, since GlassCart has no real sales or stock data. Like the other
> subsystem research notes, this is written from what actually drove the implementation.

---

## 1. Exponential Smoothing for Demand Forecasting

**Explanation.** Exponential smoothing forecasts a time series by weighting recent observations more heavily than older ones, with weights decaying exponentially into the past — computationally cheap, requires no training data beyond the series itself, and remains a strong, widely-used baseline for demand forecasting in practice, not merely a historical stepping stone to more complex methods.

**Citations.**
- Gardner, E. S. (2006). *Exponential Smoothing: The State of the Art—Part II*. International Journal of Forecasting, 22(4), 637–666. https://doi.org/10.1016/j.ijforecast.2006.03.005 — comprehensive modern survey of exponential smoothing methods and their continued practical relevance.
- Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and Practice* (3rd ed.), Chapter 8 (Exponential smoothing). OTexts. https://otexts.com/fpp3/expsmooth.html — standard modern reference and freely available.

**Used in GlassCart:** directly justifies choosing exponential smoothing over a heavier machine-learned forecasting model — it's a real, still-relevant production technique appropriately scaled to a synthetic 90-day series per product, not a toy simplification chosen only because GlassCart lacks the data for something bigger.

---

## 2. Holt's Linear Trend Method

**Explanation.** Simple exponential smoothing has no way to represent a trend — it will always lag behind a series that's steadily rising or falling. Holt's linear method extends it with a second smoothed component (the trend), updated alongside the level, letting the forecast extrapolate a trend rather than just the most recent level.

**Citations.**
- Holt, C. C. (2004). *Forecasting Seasonals and Trends by Exponentially Weighted Moving Averages*. International Journal of Forecasting, 20(1), 5–10. https://doi.org/10.1016/j.ijforecast.2003.09.015 (reprint of the 1957 Carnegie Institute of Technology memorandum that originated the method).
- Hyndman & Athanasopoulos (2021) (as cited in §1), §8.2 — modern notation and worked examples of Holt's method.

**Used in GlassCart:** `training/inventory/forecast.py`'s `_holt_linear()` implements the method's level/trend update equations directly (`level = α·observed + (1−α)·(level+trend)`, `trend = β·(level−prev_level) + (1−β)·trend`), exactly as the source describes — since [`datasets/inventory/generate.py`](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/inventory/generate.py) deliberately builds in a per-product linear trend, a method that can't represent trend at all would be a poor fit for the very data it's asked to forecast.

---

## 3. Seasonal Decomposition (Weekly Seasonality)

**Explanation.** When a series has a repeating seasonal pattern (here, day-of-week effects), forecasting accuracy improves by removing that pattern before smoothing/trending the remainder, then reapplying it to the forecast — classical seasonal decomposition, one of the oldest and simplest ways to handle seasonality without a full seasonal-smoothing model (Holt-Winters) that estimates the seasonal component adaptively over time.

**Citations.**
- Hyndman & Athanasopoulos (2021) (as cited in §1), Chapter 3 (Time series decomposition) — the classical decompose-forecast-recompose pattern this implementation follows, in simplified (static index, not adaptively re-estimated) form.
- Winters, P. R. (1960). *Forecasting Sales by Exponentially Weighted Moving Averages*. Management Science, 6(3), 324–342. https://doi.org/10.1287/mnsc.6.3.324 — the fuller Holt-Winters method that estimates seasonality adaptively alongside level and trend, cited here to be explicit about what this implementation *doesn't* do (its seasonal index is computed once from the whole history, not re-estimated as the smoothing progresses).

**Used in GlassCart:** `_weekday_seasonal_index()` computes a static per-weekday index once from the full 90-day history (each weekday's mean relative to the overall mean), used to deseasonalize before Holt's method runs and to reseasonalize the forecast — a deliberately simpler choice than full Holt-Winters, appropriate given only 90 days (roughly 12-13 weeks) of history, too short to reliably re-estimate a seasonal component adaptively.

---

## 4. Censored Demand from Stockouts

**Explanation.** When a product sells out, the day's recorded sales figure is not the true demand — it's demand truncated at whatever stock happened to be available. Naively treating a stockout day's sales as if it were the true demand systematically biases a demand estimate downward. This is a well-known, practically important problem in inventory forecasting, distinct from ordinary noise.

**Citations.**
- Nahmias, S. (1994). *Demand Estimation in Lost Sales Inventory Systems*. Naval Research Logistics, 41(6), 739–757. https://doi.org/10.1002/1520-6750(199410)41:6%3C739::AID-NAV3220410603%3E3.0.CO;2-D — foundational treatment of demand estimation under lost sales / stockouts (censored demand).
- Conrad, S. A. (1976). *Sales Data and the Estimation of Demand*. Operational Research Quarterly, 27(1), 123–127. https://doi.org/10.2307/3009103 — early identification of the censoring problem and simple correction approaches.

**Used in GlassCart:** [`datasets/inventory/generate.py`](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/inventory/generate.py) deliberately produces this exact complication (a `stockout` flag alongside a truncated `units_sold`), and `training/inventory/forecast.py`'s Holt update substitutes its own current level+trend estimate for censored days rather than the truncated observed value — the simplest member of the correction-approach family these sources describe, chosen for its readability over more statistically rigorous censored-demand estimators.

---

## 5. The Reorder Point Formula and Safety Stock

**Explanation.** The reorder point — the stock level at which a new order should be placed so it arrives before stock runs out — is `expected demand during lead time + safety stock`, where safety stock buffers against demand variability during that lead time: `safety_stock = z × σ_demand × √(lead time)`, with `z` chosen from the standard normal distribution to hit a target service level (probability of not stocking out before the next delivery).

**Citations.**
- Silver, E. A., Pyke, D. F., & Thomas, D. J. (2016). *Inventory and Production Management in Supply Chains* (4th ed.), CRC Press, Chapter 5 — the standard modern textbook derivation of the reorder-point formula and safety-stock calculation under the normal-demand assumption.
- Axsäter, S. (2015). *Inventory Control* (3rd ed.), Springer International Series in Operations Research & Management Science. https://doi.org/10.1007/978-3-319-15729-0 — alternative standard reference deriving the same formula.

**Used in GlassCart:** `training/inventory/forecast.py` implements this formula verbatim, using the forecast's average daily demand, the observed demand standard deviation (`statistics.pstdev`), an assumed lead time (see the model card's "Known Limitations" for why this is assumed rather than measured), and `z = 1.65` for an approximately 95% service level — a direct, unmodified application of the standard formula, not an approximation invented for this project.
