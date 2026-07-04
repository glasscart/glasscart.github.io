# Research Notes: Transaction Fraud Detection

> Bibliography and design rationale for GlassCart's fraud subsystem: a rule-based velocity and
> region-risk heuristic run over a purpose-built synthetic transaction log, since GlassCart has
> no real checkout or payment processor. Like the other subsystem research notes, this is
> written from what actually drove the implementation.

---

## 1. Rule-Based Fraud Detection as Real Production Practice

**Explanation.** Before (and often alongside) machine-learned fraud models, payment systems rely heavily on hand-set rules — velocity limits, blocklists, behavioral thresholds — precisely because they're fast, require no training data, and are fully auditable when a transaction is declined. Rule-based systems remain a standard first line of defense in real production fraud stacks, not a legacy approach fully superseded by ML.

**Citations.**
- Bolton, R. J., & Hand, D. J. (2002). *Statistical Fraud Detection: A Review*. Statistical Science, 17(3), 235–255. https://doi.org/10.1214/ss/1042727940 — foundational survey distinguishing rule-based/supervised/unsupervised fraud-detection approaches and their respective roles.
- Dal Pozzolo, A., Boracchi, G., Caelen, O., Alippi, C., & Bontempi, G. (2018). *Credit Card Fraud Detection: A Realistic Modeling and a Novel Learning Strategy*. IEEE Transactions on Neural Networks and Learning Systems, 29(8), 3784–3797. https://doi.org/10.1109/TNNLS.2017.2736643 — modern treatment of the practical constraints (extreme class imbalance, concept drift) that keep rule-based components relevant alongside learned models in real systems.

**Used in GlassCart:** directly justifies building the fraud subsystem as a rule-based heuristic rather than reaching for a trained classifier — this is not a simplification made only because GlassCart lacks training data (though it does), it's also representative of how real fraud systems are actually built.

---

## 2. Velocity Checks / Card Testing Detection

**Explanation.** "Card testing" is a well-documented fraud pattern where a stolen card number is validated by attempting several small transactions in rapid succession before a larger fraudulent purchase is attempted. Velocity checks — counting a buyer's (or card's, or device's) transactions within a short rolling time window — are a standard, widely-deployed countermeasure.

**Citations.**
- Delamaire, L., Abdou, H., & Pointon, J. (2009). *Credit Card Fraud and Detection Techniques: A Review*. Banks and Bank Systems, 4(2), 57–68. — surveys velocity-based and behavioral rule techniques used in real card-fraud detection.
- Stripe. *Radar: Detecting Card Testing Attacks* — industry documentation describing real-world card-testing patterns and velocity-based countermeasures. https://stripe.com/docs/radar/card-testing

**Used in GlassCart:** `datasets/transactions/generate.py`'s "card-testing ring" pattern (a fresh account making several small transactions within minutes) and `training/fraud/detect.py`'s velocity indicator (count of same-buyer transactions within a rolling 15-minute window) directly implement this well-documented pattern and its standard countermeasure.

---

## 3. Address/Region Mismatch as a Fraud Signal

**Explanation.** A mismatch between a payment instrument's billing address/region and a purchase's shipping destination is one of the oldest and most widely used fraud signals in card-not-present (e.g. online) transactions — a stolen card is frequently used to ship goods somewhere other than the cardholder's own address. It's also a signal with real false-positive cost (gifts, travel, multi-address households), which is why it's typically combined with other risk factors rather than used alone.

**Citations.**
- Delamaire, Abdou, & Pointon (2009) (as cited in §2) — covers address-verification and mismatch-based rules as part of the standard fraud-rule toolkit.
- Bhattacharyya, S., Jha, S., Tharakunnel, K., & Westland, J. C. (2011). *Data Mining for Credit Card Fraud: A Comparative Study*. Decision Support Systems, 50(3), 602–613. https://doi.org/10.1016/j.dss.2010.08.008 — discusses address/geographic features among standard fraud-detection feature sets.

**Used in GlassCart:** `training/fraud/detect.py`'s region-risk indicator scores a shipping/billing mismatch higher when combined with a newer account — directly modeling the "combine with other risk factors" practice these sources describe, rather than treating a mismatch alone as sufficient (which the dataset's 4% legitimate-mismatch rate would make a poor lone signal in any case — see [datasets/transactions/DATASET_CARD.md](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/transactions/DATASET_CARD.md)).

---

## 4. Evaluating a Fraud Heuristic Honestly (Including Its Misses)

**Explanation.** As with the reviews subsystem's fake-review heuristic (see [docs/research/reviews.md](reviews.md) §5), a detector evaluated against data built with the exact pattern it targets can look artificially strong. What makes an evaluation informative rather than circular is reporting *where the method actually fails*, not just an aggregate score.

**Citations.** (methodology, not a specific paper — same reasoning as `research/reviews.md` §5)

**Used in GlassCart:** unlike the reviews fake-review heuristic (which scores a suspicious 1.0/1.0/1.0 against its own benchmark), this fraud heuristic's evaluation surfaces a specific, reproducible miss: region-mismatch fraud under the $150 "high value" threshold isn't flagged, because region-risk alone (weight `0.30`) doesn't cross the `0.5` decision threshold. This is documented as a real finding in `models/fraud/MODEL_CARD.md`, not smoothed over — a threshold-driven blind spot is exactly the kind of thing a from-scratch reader of a rule-based system needs to know exists.
