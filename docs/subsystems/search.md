# Subsystem: Hybrid Product Search

## What problem does this solve?

A shopper's query rarely matches a product's exact words. Someone searching "cozy running gear" should find a listing titled "Breathable Fleece Hoodie" even though no word overlaps. Conversely, someone searching a specific brand or material ("Aluminum Wireless Headphones") wants an exact keyword match to win, even if a dozen semantically-similar products exist. No single technique handles both cases well — which is why GlassCart implements **hybrid search**: classic keyword ranking (BM25) combined with neural semantic similarity (sentence embeddings), fused into one score.

## Why does it exist (in this form)?

This is GlassCart's first vertical slice, chosen specifically because it exercises the platform's two hardest constraints at once:

1. It's a genuinely useful, realistic commerce feature (every marketplace needs search).
2. It forces every architectural question the "AI-transparent, static-first, offline-first" philosophy raises: where does inference run if there's no server? How do you keep two independent implementations (browser and backend) honest? What, exactly, should Glass Mode show for a hybrid score that no single number fully explains?

## How does it work?

### 1. Keyword search: BM25

BM25 (Robertson & Zaragoza, 2009) scores a document for a query by summing, over each query term present in the document, a saturating function of term frequency divided by document-length normalization, weighted by inverse document frequency:

```
score(D, Q) = Σ IDF(qᵢ) · f(qᵢ, D)·(k1+1) / (f(qᵢ, D) + k1·(1 - b + b·|D|/avgdl))
```

- `k1` (GlassCart uses `1.5`) controls how quickly additional occurrences of a term stop adding score (diminishing returns on repetition).
- `b` (GlassCart uses `0.75`) controls how much longer documents are penalized relative to the collection average.

GlassCart implements this from scratch in ~50 lines of TypeScript (`apps/web/src/lib/search/bm25.ts`) — no library — because it's simple enough to be worth reading end-to-end, and because a pure-JS implementation is what makes running it in the browser with zero dependencies possible.

### 2. Semantic search: sentence embeddings

BM25 only ever matches literal tokens. To catch paraphrase and synonymy, GlassCart also embeds every product (title + description) into a 384-dimensional vector using `all-MiniLM-L6-v2` — a small, distilled sentence-embedding transformer — and embeds the user's query into the same vector space. Cosine similarity between the two then stands in for "semantic relevance."

The key architectural trick: **catalog embeddings are computed once, offline**, in Python, using [`fastembed`](https://github.com/qdrant/fastembed) (an ONNX-Runtime-based library — no PyTorch dependency). The **query** embedding is computed **live, in the visitor's own browser**, using [`transformers.js`](https://huggingface.co/docs/transformers.js) running the *same model weights*, exported to ONNX, via WebAssembly. Because both sides use the same underlying checkpoint, their vectors live in the same space and cosine similarity between them is meaningful — this is exactly the bi-encoder pattern introduced by Sentence-BERT (Reimers & Gurevych, 2019).

### 3. Fusion

Both signals are min-max normalized to `[0, 1]` (independently, per query) and combined linearly:

```
fused = α · normalize(BM25) + (1 - α) · normalize(cosine_similarity)
```

GlassCart uses `α = 0.5` (equal weight). The alternative — Reciprocal Rank Fusion (RRF), which combines *ranks* rather than raw scores — is arguably more robust when the two score distributions are wildly different, but was deliberately not chosen here: RRF scores have no intuitive "how relevant" interpretation, whereas linear fusion lets Glass Mode show "BM25 contributed X, semantic similarity contributed Y" as a literal, human-readable weighted sum. Transparency was prioritized over the marginal ranking-quality difference between the two fusion strategies.

## Why this implementation was chosen (vs. alternatives)

| Alternative | Why not (for this slice) |
|---|---|
| A hosted vector database (Pinecone, Weaviate, Qdrant) | Requires a server and, usually, a paid account — violates the "no paid APIs, works on GitHub Pages" constraint. |
| Cross-encoder re-ranking | Requires one forward pass *per candidate per query* — computationally infeasible client-side over hundreds of products; bi-encoders (this design) require only one query-side forward pass. |
| Reciprocal Rank Fusion instead of linear fusion | More common in production, but harder to explain as a per-result breakdown — see above. |
| A single embedding-only search (no BM25) | Loses exact brand/SKU/keyword matches, which real shoppers rely on. |
| A single keyword-only search (no embeddings) | Loses every paraphrase/synonym match — the classic "0 results" problem. |

## Strengths

- Fully offline-capable after first load; the only network calls are one-time model/catalog downloads, cached by the browser.
- No server required for the deployed site — works unmodified on GitHub Pages.
- Every parameter (`k1`, `b`, `α`) is a named, documented constant, not a buried magic number.
- Two independent implementations (TS + Python) validate each other and give a reference "server mode" for people who want one.

## Weaknesses & known failure cases

- The synthetic, templated catalog (see the [dataset card](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/products/DATASET_CARD.md)) has much lower lexical diversity than a real marketplace, which makes BM25 look artificially strong relative to semantic search — a real catalog would show a different balance.
- `all-MiniLM-L6-v2` is English-only and was never fine-tuned on e-commerce text (see the [model card](https://github.com/glasscart/glasscart.github.io/blob/main/models/search-embeddings/MODEL_CARD.md)).
- The embedding index is static: adding a product requires re-running the training pipeline and rebuilding the site. There's no incremental/online update path.
- The first search in a session pays a one-time cost to download and initialize the ONNX model in the browser (tens of MB); subsequent searches are fast (see the latency breakdown Glass Mode shows).
- Fixed `α = 0.5` is a reasonable default, not a tuned optimum — there's no offline evaluation set (real relevance judgments) to tune it against yet.

## How it could be improved

- Add an offline evaluation harness with synthetic relevance judgments to tune `α`, `k1`, and `b` against a measurable metric (e.g. NDCG) instead of defaults.
- Support incremental index updates (append a single product's embedding without recomputing the whole catalog).
- Add learned re-ranking as a second stage over the top-K hybrid results, once there's real interaction data to train on.
- Extend the same `GlassExplanation` contract to future subsystems (recommendations, ranking) so Glass Mode's UI is reusable rather than search-specific.

## Where to look in the code

| Concern | Client (TypeScript) | Server (Python, optional) |
|---|---|---|
| Shared constants | `apps/web/src/lib/search/config.ts` | `services/search/app/config.py` |
| BM25 | `apps/web/src/lib/search/bm25.ts` | `rank_bm25` in `services/search/app/hybrid.py` |
| Semantic embedding | `apps/web/src/lib/search/semantic.ts` (transformers.js) | `fastembed` in `services/search/app/hybrid.py` |
| Fusion + Glass explanation | `apps/web/src/lib/search/hybrid.ts` | `services/search/app/hybrid.py` |
| UI | `apps/web/src/pages/SearchPage.tsx`, `GlassSummaryPanel.tsx`, `GlassScoreBreakdown.tsx` | — |

## Further reading

See the full [research bibliography for search & retrieval](../research/search-and-retrieval.md) for primary sources on BM25, Sentence-BERT, `all-MiniLM-L6-v2`, hybrid fusion strategies, transformers.js, ONNX Runtime, and the model/dataset transparency literature this feature's Glass Mode panel is built on.
