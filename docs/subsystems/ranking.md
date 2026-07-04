# Subsystem: Business-Rule Ranking & Diversification

## What problem does this solve?

Raw relevance (search's fused BM25 + semantic score, or recommendations' cosine similarity) is not the same thing as a good result *page*. Two problems show up once you look at raw-relevance-ordered results: some good-but-unpopular products never surface because nothing boosts them, and — specific to GlassCart's synthetic catalog — a handful of near-duplicate variants of the same base product (see the [dataset card](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/products/DATASET_CARD.md)'s intentionally-generated near-duplicates) can crowd out everything else. Ranking is the second stage that fixes both, layered on top of whatever candidates search or recommendations already produced.

## Why does it exist (in this form)?

The [roadmap](../roadmap.md) describes this as "business-rule and diversification logic layered on top of search/recommendation candidates" — deliberately not a learned ranking model. GlassCart has no click-through or purchase logs to train a learned ranker on (the same reason recommendations are content-based rather than collaborative — see [docs/research/recommendations.md](../research/recommendations.md) §3), so a hand-set, fully-transparent set of business rules is the only kind of ranker that can be built honestly right now.

## How does it work?

`apps/web/src/lib/ranking/rerank.ts` takes a pool of candidates (each just a product + a base relevance score from whatever upstream subsystem produced it) and:

1. **Adds two business-rule boosts** to the base score:
   - a **rating boost**, scaled from the product's 1–5 rating,
   - a **popularity boost**, log-scaled from `rating_count` (so a handful of extremely popular items don't saturate the boost for everyone else).
2. **Diversifies greedily**: repeatedly picks the current best-scoring remaining candidate, then penalizes every other candidate that shares its *diversity key* (`category + first word of title` — a cheap proxy for "near-duplicate variant of the same base product") before picking the next one. This is a simplified form of Maximal Marginal Relevance (MMR): instead of computing pairwise similarity between every candidate, it uses the same coarse key the dataset generator itself uses to create variants in the first place.

Both call sites fetch a **wider candidate pool** than they display (search: 30 candidates → top 12 shown; recommendations: 12 candidates → top 4 shown) specifically so diversification has real alternatives to promote — re-ranking a pool that's already been truncated to near-duplicates can only reorder them, not replace them.

Search uses all three signals (rating, popularity, diversity); recommendations use diversity only — boosting "similar products" by general popularity would trade away genuine similarity for generically-popular items, which isn't the point of that list.

## Why this implementation was chosen (vs. alternatives)

| Alternative | Why not (yet) |
|---|---|
| Learning to Rank (e.g. LambdaMART, a learned re-ranker) | Needs labeled relevance judgments or click data GlassCart doesn't have; would also stop being explainable as a literal per-item formula. |
| Reciprocal Rank Fusion between "relevance rank" and "popularity rank" | Same transparency trade-off search already rejected RRF for (see [search-and-retrieval.md](../research/search-and-retrieval.md) §4) — ranks alone don't explain "how much" popularity mattered. |
| True MMR with pairwise embedding similarity for diversification | More principled, but requires an O(n²) similarity comparison per re-rank and doesn't obviously outperform the cheap category+noun key for *this* dataset's specific near-duplicate generation pattern (see the dataset card). |

## Strengths

- Every adjustment is a named constant (`ratingWeight`, `popularityWeight`, `diversityWeight`) and every result's final score is a literal sum a user can verify with a calculator, not an opaque model output.
- Reused across two subsystems (search and recommendations) with different weight profiles, rather than duplicated logic.
- Directly measurable effect on a real, documented dataset property (near-duplicate variants) rather than a hypothetical concern.

## Weaknesses & known failure cases

- Diversity key is a heuristic, not a true duplicate detector: two genuinely distinct products that happen to share a first word and category get penalized against each other unnecessarily, and true near-duplicates that don't share a first word slip through.
- Weights (`0.05`, `0.05`, `0.15`) are hand-picked to look reasonable, not fit against any measured outcome — there is no offline evaluation set (see the same limitation search's fusion `α` has).
- Popularity normalization assumes the dataset generator's own `rating_count` ceiling (4200) rather than a measured real-world distribution.
- Greedy diversification is not globally optimal — it can occasionally produce a lower-total-relevance page than a smarter search would, in exchange for simplicity and speed.

## How it could be improved

- Build an offline evaluation harness (as search's own "how it could be improved" section already proposes) to tune all three weights against a measurable objective instead of hand-picked defaults.
- Replace the coarse diversity key with real pairwise embedding similarity once performance at catalog scale justifies the O(n²) cost.
- Once real interaction data exists, replace the rating/popularity business rules with a learned re-ranker trained on it, keeping diversification as a final deterministic pass for explainability.

## Where to look in the code

| Concern | Client (TypeScript) |
|---|---|
| Re-ranking + Glass explanation | `apps/web/src/lib/ranking/rerank.ts` |
| UI | `apps/web/src/components/GlassRankingPanel.tsx` |
| Wired into | `apps/web/src/pages/SearchPage.tsx`, `apps/web/src/components/RecommendedProducts.tsx` |

## Further reading

See the full [research bibliography for ranking](../research/ranking.md) for primary sources on learning to rank, business-rule/multi-objective ranking, and Maximal Marginal Relevance.
