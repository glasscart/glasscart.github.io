# Research Notes: Demand-Driven Pricing Simulation

> Bibliography and design rationale for GlassCart's pricing subsystem: a constant-elasticity
> demand simulation combined with the classic monopoly markup pricing rule, applied to
> explicitly-synthetic inputs since no real transaction data exists. Like the other subsystem
> research notes, this is written from what actually drove the implementation.

---

## 1. Price Elasticity of Demand

**Explanation.** Price elasticity of demand measures how sensitive quantity demanded is to a price change: `e = -(%Δquantity / %Δprice)`. Demand is called "elastic" when `e > 1` (a price change produces a proportionally larger quantity change) and "inelastic" when `e < 1`. It's one of the oldest and most widely taught quantitative concepts in microeconomics, originating with Alfred Marshall.

**Citations.**
- Marshall, A. (1890). *Principles of Economics*. Macmillan — the original formalization of elasticity of demand.
- Varian, H. R. (2014). *Intermediate Microeconomics: A Modern Approach* (9th ed.), Chapter 15 (Market Demand) — standard modern textbook treatment of elasticity and its role in pricing.

**Used in GlassCart:** `datasets/pricing/pricing_inputs.json` assigns every product a simulated elasticity, deliberately kept above 1.0 (see §3 for why) and varied by category to loosely mirror the well-known real-world pattern that necessities (groceries, pet supplies) tend to be less price-elastic than discretionary goods (electronics, beauty) — a qualitative pattern from the economics literature, applied here as a labeled assumption, not a fitted estimate.

---

## 2. The Constant-Elasticity Demand Curve

**Explanation.** A constant-elasticity (or "iso-elastic," or "log-log") demand curve takes the form `Q(p) = Q0 * (p/p0)^(-e)`, chosen specifically because its elasticity is the same `e` at every price point — unlike, say, a linear demand curve, whose elasticity varies continuously along the curve. This makes it the standard tractable choice whenever a single elasticity number is meant to characterize a product's whole demand curve, at the cost of being a real simplification (see the model card's limitations).

**Citations.**
- Varian, H. R. (2014). *Intermediate Microeconomics* (as cited in §1), Chapter 15 — derives the constant-elasticity demand form and contrasts it with linear demand.
- Pindyck, R. S., & Rubinfeld, D. L. (2017). *Microeconomics* (9th ed.), Pearson, Chapter 2 — standard treatment of demand curve functional forms including constant elasticity.

**Used in GlassCart:** `training/pricing/simulate.py`'s `demand_at()` implements this formula directly, using each product's simulated `reference_price`/`reference_quantity` as the `(p0, Q0)` anchor point and its simulated `elasticity` as `e`.

---

## 3. Monopoly Pricing and the Lerner Index

**Explanation.** For a seller with market power facing a demand curve with elasticity `e`, the profit-maximizing price satisfies `(p - MC) / p = 1/e` — the Lerner Index, a measure of markup power. Solved for price under a *constant*-elasticity demand curve specifically (where `e` doesn't change with price), this rearranges to the closed form `p* = MC * e / (e - 1)`, valid only for `e > 1`: at `e = 1` the formula is undefined (infinite markup), and for `e < 1` (inelastic demand) a monopolist's marginal revenue is never zero at any finite price, so there is no interior profit-maximizing price at all under this model — pushing price arbitrarily high always increases profit in the pure inelastic case, which is precisely why real elasticity is never allowed to fall below 1 in this simulation (see §1, and the dataset card).

**Citations.**
- Lerner, A. P. (1934). *The Concept of Monopoly and the Measurement of Monopoly Power*. The Review of Economic Studies, 1(3), 157–175. https://doi.org/10.2307/2967480 — the original Lerner Index paper.
- Varian, H. R. (2014). *Microeconomic Analysis* (3rd ed.), W. W. Norton, Chapter 14 (Monopoly) — derives the `p* = MC * e/(e-1)` closed form for constant-elasticity demand explicitly.

**Used in GlassCart:** `training/pricing/simulate.py`'s `optimal_price_for()` is a direct, one-line implementation of this formula. This is the one piece of real, citable economic theory in the whole subsystem — everything else (the elasticity value, the marginal cost, the reference demand) is a labeled simulation input the formula is applied to.

---

## 4. Dynamic / Algorithmic Pricing in Practice

**Explanation.** Real-world dynamic pricing systems (airlines, ride-hailing, e-commerce) combine demand estimation (often from real historical transaction data, sometimes with machine-learned demand models rather than a single hand-set elasticity) with optimization to set or adjust prices, frequently layering in inventory constraints, competitor pricing, and business rules on top of the pure economic optimum.

**Citations.**
- Talluri, K. T., & van Ryzin, G. J. (2004). *The Theory and Practice of Revenue Management*. Springer. https://doi.org/10.1007/b139000 — comprehensive treatment of demand-based pricing/revenue management as practiced in industries like airlines and hospitality.
- den Boer, A. V. (2015). *Dynamic Pricing and Learning: Historical Origins, Current Research, and New Directions*. Surveys in Operations Research and Management Science, 20(1), 1–18. https://doi.org/10.1016/j.sorms.2015.03.001 — survey connecting classical elasticity-based pricing theory to modern learned/adaptive pricing systems.

**Used in GlassCart:** cited to be explicit about the gap between this subsystem and a real dynamic-pricing system: real systems estimate elasticity/demand from actual transaction data (often continuously, via online learning — den Boer's survey is specifically about that), which GlassCart cannot do without transaction history it doesn't have. This subsystem implements the *optimization* half of that pipeline (given an elasticity and a cost, what price maximizes profit) honestly, while being explicit that the *estimation* half (where does the elasticity number actually come from) is entirely simulated here rather than pretended away.
