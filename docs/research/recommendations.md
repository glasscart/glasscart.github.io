# Research Notes: "Similar Products" Recommendations

> Bibliography and design rationale for GlassCart's recommendations subsystem: a content-based,
> embedding-similarity recommender that reuses the search subsystem's precomputed catalog
> vectors with no new model or training step. Like `search-and-retrieval.md`, this is written
> from what actually drove the implementation, not compiled speculatively before writing code.

---

## 1. Content-Based Filtering

**Explanation.** Recommender systems broadly split into content-based approaches (recommend items similar to ones a user liked, based on item *attributes*) and collaborative approaches (recommend items that *other similar users* liked, based on interaction patterns, without needing to understand item content at all). Content-based filtering only needs item representations and one anchor item — no interaction history — which makes it the natural starting point for any catalog that doesn't have purchase/click data yet.

**Citations.**
- Pazzani, M. J., & Billsus, D. (2007). *Content-Based Recommendation Systems*. In The Adaptive Web (LNCS 4321), 325–341. Springer. https://doi.org/10.1007/978-3-540-72079-9_10
- Lops, P., de Gemmis, M., & Semeraro, G. (2011). *Content-based Recommender Systems: State of the Art and Trends*. In Recommender Systems Handbook, 73–105. Springer. https://doi.org/10.1007/978-0-387-85820-3_3

**Used in GlassCart:** this is the direct justification for building a content-based recommender first, rather than any form of collaborative filtering — see §3 for why collaborative approaches specifically aren't viable yet, not just less convenient.

---

## 2. Nearest-Neighbor Recommendation via Embedding Similarity

**Explanation.** Once items have vector representations, "similar items" reduces to a nearest-neighbor search in vector space — the same computation underlying dense retrieval (see `search-and-retrieval.md` §2), just with an item vector as the query instead of a text query. This reuse is not a coincidence: a bi-encoder embedding space designed for semantic search (where "is this document relevant to this query" is approximated by vector closeness) supports "is this item like that item" for free, since both reduce to the same cosine-similarity operation over the same space.

**Citations.**
- Sarwar, B., Karypis, G., Konstan, J., & Riedl, J. (2001). *Item-Based Collaborative Filtering Recommendation Algorithms*. In Proceedings of WWW '01, 285–295. https://doi.org/10.1145/371920.372071 — the foundational item-similarity framing this approach borrows the *mechanism* of (nearest neighbors over item vectors), while substituting content embeddings for the interaction-based similarity the original paper computes.
- Reimers, N., & Gurevych, I. (2019). *Sentence-BERT* (as cited in `search-and-retrieval.md` §2) — the bi-encoder property (independently-computed, directly-comparable embeddings) that makes reusing search's vectors for this task valid.

**Used in GlassCart:** `apps/web/src/lib/recommendations/similar.ts` computes exactly this — a dot product between one product's embedding and every other product's embedding (vectors are pre-normalized, so dot product equals cosine similarity), sorted descending. No new embedding computation happens for this subsystem; it reads the exact same `product_embeddings.json` the search page already fetches.

---

## 3. The Cold-Start Problem (and Why It's Sidestepped, Not Solved)

**Explanation.** Collaborative filtering's core weakness is the cold-start problem: it cannot recommend anything for a user or item with no interaction history, because it has nothing to compute similarity *from* except past interactions. A brand-new catalog (like GlassCart's, which has never had a real visitor) is cold-start for every single item simultaneously — there is no "people who viewed this also viewed" signal to mine, because nobody has ever viewed anything yet.

**Citations.**
- Schein, A. I., Popescul, A., Ungar, L. H., & Pennock, D. M. (2002). *Methods and Metrics for Cold-Start Recommendations*. In Proceedings of SIGIR '02, 253–260. https://doi.org/10.1145/564376.564421
- Lam, X. N., Vu, T., Le, T. D., & Duong, A. D. (2008). *Addressing Cold-Start Problem in Recommendation Systems*. In Proceedings of ICUIMC '08, 208–211. https://doi.org/10.1145/1352793.1352837 — surveys content-based and hybrid strategies specifically for the cold-start case.

**Used in GlassCart:** this is the honest reason recommendations here are content-based rather than collaborative — not a simplification for convenience, but the only technique that isn't cold-start-broken for a catalog with zero interaction history. The [subsystem doc](../subsystems/recommendations.md) and this pipeline's Glass Mode limitations both say so explicitly rather than presenting collaborative filtering as "not implemented yet" without explaining why it can't honestly be faked with synthetic interaction data (doing so would validate the technique against data manufactured to make it work, not against anything real).

---

## 4. Model Transparency for a Reused, Not New, Model

**Explanation.** Model cards and dataset cards (see `search-and-retrieval.md` §7) are usually written per model or per dataset. This subsystem introduces neither — it's a new *application* of an existing, already-documented model (the search embedding model) to a second task. The transparency question this raises is slightly different: not "what is this model and how was it trained," but "is it valid to reuse this specific model for this specific second purpose, and what does that reuse cost in accuracy or applicability."

**Citations.**
- Mitchell, M. et al. (2019). *Model Cards for Model Reporting* (as cited in `search-and-retrieval.md` §7) — the "Intended Use" / "Non-Intended Use" sections this framework already asks for are exactly where a second, unplanned use case like this one should be evaluated.

**Used in GlassCart:** rather than duplicating `models/search-embeddings/MODEL_CARD.md`, the [recommendations subsystem doc](../subsystems/recommendations.md) explicitly cross-links it and calls out that every limitation of the base embedding model (English-only, general-purpose, not e-commerce-tuned, trained on unrelated web text) applies here too, since no new training happened — reuse doesn't launder away the original model's limitations, and documenting the reuse honestly means repeating them rather than letting them go unmentioned in the new context.
