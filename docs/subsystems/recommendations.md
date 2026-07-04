# Subsystem: "Similar Products" Recommendations

## What problem does this solve?

A shopper looking at one product often wants to compare it against a handful of close alternatives — other headphones, other stand mixers — without re-typing a search. GlassCart's product detail page shows a "You might also like" section for exactly this: a short list of products similar to the one being viewed.

## Why does it exist (in this form)?

The [roadmap](../roadmap.md) deliberately orders recommendations as the subsystem to build right after search, for a specific reason: it can reuse search's biggest investment — the precomputed catalog embeddings — instead of needing its own model, its own training step, or any new data. GlassCart also has no click-stream or purchase history yet, so collaborative filtering ("people who bought X also bought Y") isn't an honest option; a content-based recommender over product text is the only kind that can be built truthfully today. See [docs/research/recommendations.md](../research/recommendations.md) for the sources behind that choice.

## How does it work?

Every product already has a 384-dimensional embedding vector, computed offline by the search subsystem (`training/search_embeddings/build_index.py`, documented in [`models/search-embeddings/MODEL_CARD.md`](../../models/search-embeddings/MODEL_CARD.md)). "Similar products" is just cosine similarity between one product's vector and every other product's vector, sorted descending, top-4 kept:

```
similarity(A, B) = A · B        (a plain dot product — vectors are already L2-normalized)
```

This runs entirely client-side in `apps/web/src/lib/recommendations/similar.ts`, over the same `product_embeddings.json` artifact the search page already fetches — no new network request, no new offline artifact, no new model. When Glass Mode is on, the product detail page shows a panel explaining the method plus a per-item "N% similar" score next to each recommended card, using the same visual language as search's score breakdown.

## Why this implementation was chosen (vs. alternatives)

| Alternative | Why not (yet) |
|---|---|
| Collaborative filtering (user-item interaction matrix) | GlassCart has no click/purchase/session data to learn from — building this on fabricated interaction data would misrepresent a real technique as working on data it was never actually validated against. |
| A separate recommendation-specific embedding model | Would mean maintaining two embedding spaces and two training pipelines for one small catalog; reusing search's embeddings is simpler and keeps one model doing (part of) two jobs, transparently. |
| Session-based / sequence models (e.g. GRU4Rec-style "next item" prediction) | Needs session sequences GlassCart doesn't record; also a much bigger modeling investment than the catalog's size or this milestone justifies. |
| A hosted recommendation API | Requires a server and, usually, a paid account — violates the "no paid APIs, works on GitHub Pages" constraint, same reasoning as search. |

## Strengths

- Zero marginal cost: no new model to train, download, or version — it rides on an artifact that already exists for another reason.
- Fully offline-capable, same as search, for the same reason (static catalog embeddings + client-side computation).
- Every recommended item comes with an inspectable similarity score, not a black-box "recommended for you."

## Weaknesses & known failure cases

- Purely content-based: two products can be "similar" by this measure (similar words in title/description) without actually being good pairings for a shopper (a phone case and a phone are related in a way this method can't see, since it only compares *products to themselves*, not co-purchase patterns).
- Inherits every limitation of the underlying embedding model (English-only, general-purpose, not e-commerce-tuned) — see the [search embeddings model card](../../models/search-embeddings/MODEL_CARD.md#known-limitations--failure-cases).
- The synthetic catalog's templated descriptions (see the [dataset card](../../datasets/products/DATASET_CARD.md)) mean many products in the same category are lexically very close to begin with, which can make recommendations look artificially strong or repetitive compared to a real catalog.
- Static, like search's index: a newly added product isn't recommendable (or a recommendation target) until the embeddings artifact is rebuilt.
- No exclusion logic beyond "not itself" — a shopper could see near-duplicate variants (same product, different color/material) as all four recommendations, which a production recommender would usually diversify against.

## How it could be improved

- Diversification: penalize recommending multiple near-duplicate variants of the same base product.
- Once real interaction data exists, add a second, genuinely collaborative signal and blend it with this content-based one — the same linear-fusion-for-transparency approach search uses for BM25 + semantic score would generalize naturally.
- Extract a shared base `GlassExplanation` type once a third subsystem needs one — right now search and recommendations each define their own explanation shape (see `apps/web/src/lib/search/types.ts` vs. `apps/web/src/lib/recommendations/similar.ts`); they're similar in spirit (provider, why AI was used, model metadata, timing, limitations) but not identical, and forcing one shared interface for two data points would have been premature.

## Where to look in the code

| Concern | Client (TypeScript) |
|---|---|
| Similarity computation + Glass explanation | `apps/web/src/lib/recommendations/similar.ts` |
| UI | `apps/web/src/components/RecommendedProducts.tsx`, `GlassRecommendationPanel.tsx` |
| Wired into | `apps/web/src/pages/ProductDetailPage.tsx` |

## Further reading

See the full [research bibliography for recommendations](../research/recommendations.md) for primary sources on content-based filtering, cosine-similarity nearest-neighbor recommenders, and the cold-start problem this subsystem's design deliberately sidesteps rather than fakes a solution for.
