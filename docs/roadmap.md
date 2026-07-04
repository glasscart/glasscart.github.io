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

## Next candidates (not yet started)

Roughly in the order they'd naturally build on what search already established (a product corpus, an embedding pipeline, a Glass Mode contract):

1. **Recommendations** — starting with a simple, fully-explainable content-based recommender ("similar products," reusing the search embeddings already computed) before attempting collaborative filtering or session-based models, which need interaction data GlassCart doesn't have yet.
2. **Ranking** — business-rule and diversification logic layered on top of search/recommendation candidates.
3. **Reviews** — sentiment/aspect extraction and fake-review heuristics over a synthetic review dataset (which doesn't exist yet — products currently only have aggregate `rating`/`rating_count`, no review text).
4. **Pricing** — elasticity/demand-driven pricing simulation, explicitly labeled as simulation where there's no real transaction data to model against.
5. **Fraud, inventory forecasting, vision, NLP assistants (RAG), experimentation/analytics** — later; each needs foundational data (transactions, images, click logs) that doesn't exist in the catalog yet.

## Explicitly deferred, not abandoned

Anything in the original project brief not listed above (dynamic pricing simulations, seller tooling, warehouse optimization, voice/visual search, etc.) is deferred rather than rejected — it simply doesn't have a milestone yet. If you want to pick one up, open an issue proposing which piece of foundational data or infrastructure it needs first.
