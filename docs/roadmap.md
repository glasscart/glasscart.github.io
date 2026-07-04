# Roadmap

GlassCart's long-term vision covers most of the AI systems found in a modern commerce platform: search, recommendations, ranking, pricing, inventory forecasting, fraud detection, review analysis, vision, NLP assistants, and experimentation/analytics infrastructure. That is a multi-year scope for a real team, and this project intentionally does not fake breadth by stubbing out empty directories for all of it.

## Guiding rule

Every subsystem, when it's built, must satisfy the same bar the search slice does:

- a **real** (or explicitly-labeled-simulated, with a pointer to a real reference) implementation — never a hard-coded number dressed up as a model output
- a **model card** and, if applicable, a **dataset card**
- a **Glass Mode** integration using the shared `GlassExplanation` contract
- a **research bibliography** entry in `docs/research/`
- **reproducibility**: regenerable from a committed script with no paid API required

## Done

- [x] **Search** — hybrid BM25 + semantic search, client-side and optional-server implementations. See [the subsystem doc](subsystems/search.md).
- [x] **Recommendations** — content-based "similar products," reusing the search embeddings already computed (no new model, no new data). See [the subsystem doc](subsystems/recommendations.md).
- [x] **Ranking** — transparent business-rule boosts (rating, popularity) plus near-duplicate diversification, layered on top of both search and recommendation candidates. See [the subsystem doc](subsystems/ranking.md).
- [x] **Reviews** — a new synthetic review dataset plus from-scratch lexicon sentiment scoring, keyword-based aspect extraction, and a fake-review heuristic evaluated (honestly, with caveats) against a synthetic benchmark. See [the subsystem doc](subsystems/reviews.md).
- [x] **Pricing** — a constant-elasticity demand simulation plus the classic monopoly markup pricing rule, applied to explicitly-synthetic inputs since there's no real transaction data — the "explicitly-labeled-simulated" branch of the guiding rule below, not the "real implementation" branch. Glass Mode-only (never shown to shoppers as a real recommendation). See [the subsystem doc](subsystems/pricing.md).
- [x] **Fraud detection** — a new synthetic transaction log (GlassCart has no real checkout) plus a rule-based velocity + region-mismatch heuristic, evaluated with an honestly-reported miss pattern rather than a suspiciously perfect score. Glass Mode-only, on its own `/transactions` ops-style page rather than the shopper storefront. See [the subsystem doc](subsystems/fraud.md).

## Built and evaluated, not shipped

- **Product images** — a CPU-only, INT8-quantized diffusion pipeline (`training/product_images/`) that generates one placeholder photo per product, offline, with no GPU and no paid API. Two models were benchmarked (see the [model card](https://github.com/glasscart/glasscart.github.io/blob/main/models/product-images/MODEL_CARD.md) and [research notes](research/product-images.md) for the full comparison, including a documented negative result on a smaller, faster model that turned out not to have enough capacity to render the catalog's category diversity correctly). The larger model that *did* render correctly-shaped, recognizable products still wasn't judged good enough to ship — the storefront currently uses the procedural (non-AI) placeholder in `apps/web/src/components/ProductImage.tsx` instead. The pipeline and its documentation are kept as-is (a real, reproducible, honestly-benchmarked attempt) for anyone who wants to pick this back up with a different model/approach; it does not currently produce any images checked into the repo.

## Next candidates (not yet started)

- **Inventory forecasting, vision, NLP assistants (RAG), experimentation/analytics** — each needs foundational data that doesn't exist in the catalog yet (inventory forecasting needs historical sales/stock time series; vision needs real or generated images — a product-image generation pipeline was built and evaluated, see "Built and evaluated, not shipped" above, but its output isn't currently part of the catalog; NLP/RAG needs a retrieval corpus, which GlassCart's own docs could arguably provide; analytics needs click/session logs). Fraud detection was in this same bucket until its foundational data (a synthetic transaction log) was built alongside the subsystem itself — the same move could unblock any of these.

## Explicitly deferred, not abandoned

Anything in the original project brief not listed above (dynamic pricing simulations, seller tooling, warehouse optimization, voice/visual search, etc.) is deferred rather than rejected — it simply doesn't have a milestone yet. If you want to pick one up, open an issue proposing which piece of foundational data or infrastructure it needs first.
