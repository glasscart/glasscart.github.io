# Research Notes: Business-Rule Ranking & Diversification

> Bibliography and design rationale for GlassCart's ranking subsystem: a transparent, hand-set
> re-ranking pass (business-rule boosts + diversification) layered on top of search and
> recommendation candidates, with no learned model. Like the other subsystem research notes,
> this is written from what actually drove the implementation.

---

## 1. Learning to Rank (and Why This Isn't One)

**Explanation.** Learning to Rank (LTR) trains a model — pointwise, pairwise, or listwise — to predict an optimal ranking from labeled relevance judgments or implicit feedback (clicks, dwell time, purchases). It's the standard production approach for ranking at scale precisely because hand-set business rules don't capture the many weak, interacting signals real usage data reveals.

**Citations.**
- Liu, T.-Y. (2009). *Learning to Rank for Information Retrieval*. Foundations and Trends in Information Retrieval, 3(3), 225–331. https://doi.org/10.1561/1500000016
- Burges, C. J. C. (2010). *From RankNet to LambdaRank to LambdaMART: An Overview*. Microsoft Research Technical Report MSR-TR-2010-82.

**Used in GlassCart:** cited specifically to name what this subsystem deliberately is *not*. GlassCart has no click-through, dwell-time, or purchase data — a from-scratch synthetic catalog with a handful of AI-generated pages has never had a real visitor. Training an LTR model on synthetic interaction data would validate a real technique against fabricated evidence and misrepresent what it can actually do, which is precisely the trap [docs/research/recommendations.md](recommendations.md) §3 also identifies for collaborative filtering. See §2 for what's used instead.

---

## 2. Business-Rule / Multi-Objective Ranking

**Explanation.** Before (and alongside) learned rankers, production search/recommendation systems commonly re-score by a small number of explicit, named business objectives — freshness, margin, inventory, popularity, rating — combined as a weighted sum or a cascade of filters. This approach trades ranking quality (it can't discover interaction patterns a learned model would find) for total transparency: every score is traceable to a named rule.

**Citations.**
- Agarwal, D., Chen, B.-C., Elango, P., & Ramakrishnan, R. (2012). *Content Recommendation on Web Portals*. Communications of the ACM, 56(6), 92–101. https://doi.org/10.1145/2461256.2461277 — a real production system's account of layering business objectives on top of a relevance model.
- Su, Y., Erfani, S. M., & Bailey, J. (2018). *Rank Aggregation via Heterogeneous Thurstone Preference Models* — background on combining multiple ranking signals; representative of the broader multi-objective ranking literature.

**Used in GlassCart:** `apps/web/src/lib/ranking/rerank.ts` implements exactly this pattern — a base relevance score (from search or recommendations) plus two named, weighted boosts (rating, popularity), each a plain additive term a user can verify by hand. This is the direct justification for choosing business-rule ranking as the *first* ranking subsystem, matching search's own precedent of favoring an explainable linear combination over a harder-to-interpret alternative (see [search-and-retrieval.md](search-and-retrieval.md) §4).

---

## 3. Result Diversification and Maximal Marginal Relevance

**Explanation.** Pure relevance ranking can produce a result page dominated by near-duplicate items, which is bad for the user (no real choice) even when each individual item is highly relevant. Maximal Marginal Relevance (MMR) addresses this by iteratively selecting the next result that maximizes relevance *minus* similarity to what's already been selected, trading a small amount of top-line relevance for a more useful, varied page.

**Citations.**
- Carbonell, J., & Goldstein, J. (1998). *The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries*. In Proceedings of SIGIR '98, 335–336. https://doi.org/10.1145/290941.291025 — the original MMR formulation.
- Santos, R. L. T., Macdonald, C., & Ounis, I. (2015). *Search Result Diversification*. Foundations and Trends in Information Retrieval, 9(1), 1–90. https://doi.org/10.1561/1500000040 — survey of diversification approaches and their trade-offs.

**Used in GlassCart:** `rerank()`'s greedy loop is a simplified MMR: instead of computing pairwise similarity between every candidate pair (true MMR), it uses a cheap heuristic diversity key (`category + first word of title`) chosen specifically because it mirrors how [`datasets/products/generate.py`](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/products/generate.py) itself constructs near-duplicate variants (same noun, different adjective/material — see the [dataset card](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/products/DATASET_CARD.md)). This is a deliberate simplification, documented as a limitation in [docs/subsystems/ranking.md](../subsystems/ranking.md), not an oversight — full pairwise MMR was judged not worth its O(n²) cost for what this specific, known duplicate-generation pattern needs.

---

## 4. Reusing One Mechanism Across Two Subsystems

**Explanation.** Search and recommendations produce structurally similar candidate lists (a product plus a scalar relevance score) even though the underlying relevance computation is completely different (hybrid BM25+semantic fusion vs. embedding cosine similarity). A re-ranking layer that only needs `{product, baseScore}` as input can sit on top of either without knowing anything about how the base score was computed.

**Citations.** (methodology, not a specific paper — but see Agarwal et al. 2012, cited in §2, for a real system doing the same layering)

**Used in GlassCart:** `rerank()` takes a generic `RankableCandidate[]` and a `RankingWeights` config, so `apps/web/src/pages/SearchPage.tsx` and `apps/web/src/components/RecommendedProducts.tsx` both call the same function with different weight profiles (search uses rating + popularity + diversity; recommendations use diversity only, since boosting "similar products" by generic popularity would work against the point of that list). This is the direct implementation of the roadmap's framing of ranking as "layered on top of search **and recommendation** candidates," not a search-only feature.
