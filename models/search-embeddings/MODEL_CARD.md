# Model Card: `search-embeddings` (all-MiniLM-L6-v2)

Following the structure proposed by [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993) (Mitchell et al., 2019). This is the model that powers **semantic search** in GlassCart, and everything on this page is surfaced directly in the product UI whenever [Glass Mode](../../docs/glass-mode.md) is switched on.

## Purpose

Turn each product's `title + description` into a 384-dimensional embedding vector, and the user's search query into a vector in the same space, so that "nearby" vectors (by cosine similarity) represent semantically related products — even when they don't share any keywords. This is combined with BM25 keyword search in `apps/web/src/lib/search/hybrid.ts` to form GlassCart's hybrid search.

## Architecture

- **Base model**: `sentence-transformers/all-MiniLM-L6-v2` — a 6-layer MiniLM transformer distilled from a larger sentence-embedding teacher model, fine-tuned by the original authors on ~1B sentence pairs for general-purpose semantic similarity. See [Reimers & Gurevych, 2019](https://arxiv.org/abs/1908.10084) for the Sentence-BERT training approach it descends from.
- **Runtime**: exported to ONNX and served two different ways, from the *same* weights, so query and document vectors are directly comparable:
  - **Offline (this artifact)**: [`fastembed`](https://github.com/qdrant/fastembed) (`qdrant/all-MiniLM-L6-v2-onnx`), run once in Python via `onnxruntime` (CPU) over the entire product catalog. No PyTorch, no GPU, no server needed at query time.
  - **Live, in the browser**: [`transformers.js`](https://huggingface.co/docs/transformers.js) (`Xenova/all-MiniLM-L6-v2`), running the same architecture via ONNX Runtime Web (WebAssembly), to embed the user's query on their own device.
- **Output**: 384-dim float vector, mean-pooled over token embeddings and L2-normalized, so cosine similarity reduces to a dot product.
- **Input limit**: 256 tokens (longer text is truncated).

## Training Data (of the base model)

We did not train this model — we use the publicly released `sentence-transformers/all-MiniLM-L6-v2` checkpoint as-is. Per its model card, it was trained on a 1-billion-sentence-pairs corpus aggregated from sources including Reddit comments, S2ORC, WikiAnswers, PAQ, MS MARCO, and others. See the [upstream model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) for the full list and training procedure.

## What GlassCart Does With It

`training/search_embeddings/build_index.py` embeds `products.json` (see the [products dataset card](../../datasets/products/DATASET_CARD.md)) and writes:

- `product_embeddings.json` — one 384-dim vector per product id.
- `manifest.json` — the exact runtime versions, model name, corpus size, and build duration used to produce the artifact above (regenerated every run, so it never drifts from the actual artifact).

Both are copied into `apps/web/public/data/` for the static site to fetch.

## Metrics

We do not report retrieval-quality benchmarks (e.g. MTEB scores) here, because GlassCart's catalog is a small, templated synthetic dataset — not a benchmark corpus — and a number computed against it would not be meaningful or comparable to anything. For the base model's general-purpose benchmark performance, see the [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard) and the model's own card. What Glass Mode *does* show, per query, is operationally meaningful instead: embedding latency, vector dimensionality, and the raw similarity score for each result, so you can judge the model's behavior on your own queries directly rather than trusting a single reported number.

## Confidence & Uncertainty

Cosine similarity is not a calibrated probability. Glass Mode displays the raw similarity score (typically in the 0.2–0.8 range for this model on short product text) alongside the BM25 score and the fused hybrid score, rather than presenting either as a "confidence percentage" — doing so would imply a precision the model does not have.

## Hardware Used

Built on CPU only (no GPU required or used) — see `manifest.json` for the exact machine-independent runtime metadata (Python/fastembed/onnxruntime versions) recorded at build time. Client-side inference likewise runs entirely on the visitor's CPU via WebAssembly.

## Known Limitations & Failure Cases

- **Short-text bias**: the model was trained mostly on sentence-length text; product titles are short and formulaic, so embeddings for near-duplicate synthetic products (same noun, different adjective — see the [dataset card](../../datasets/products/DATASET_CARD.md#limitations--bias-discussion)) can end up very close together, which is realistic but can look like the model "isn't discriminating."
- **English-only**: this checkpoint is not multilingual. Non-English queries will embed but the results are not meaningful.
- **No domain fine-tuning**: the model has never seen GlassCart's specific catalog or category vocabulary; all semantic understanding is general-purpose.
- **Truncation**: descriptions longer than 256 tokens are silently truncated before embedding (not a concern for the current synthetic dataset, but relevant if this pipeline is pointed at real product copy).
- **Static index**: embeddings are precomputed. A newly added product will not be searchable semantically until `build_index.py` is re-run and the site is rebuilt — there is no online/incremental update path yet.

## Ethical & Privacy Considerations

- No user data is used to train or fine-tune this model.
- Query embedding happens **entirely client-side** — a user's search text never leaves their browser to power semantic search (there is no network call to compute the query vector). This is a deliberate privacy property of the architecture, not an accident, and is worth preserving in any future change to this subsystem.
- The base model's training corpus (Reddit, web Q&A, etc.) carries the general biases of web text; we have not audited it further for this narrow, short-text product-search use case.

## Intended Use

Semantic component of hybrid product search within GlassCart, and as a teaching example of shipping real (not simulated) transformer inference in a fully static, offline-capable web app.

## Non-Intended Use

Not intended for open-domain question answering, long-document retrieval, multilingual search, or any use case requiring calibrated relevance scores. Not fine-tuned or validated for any domain outside this synthetic catalog.

## Reproducibility

```bash
uv sync
uv run datasets/products/generate.py        # regenerate the catalog (optional)
uv run training/search_embeddings/build_index.py   # rebuild this artifact
uv run scripts/sync_web_data.py             # publish artifacts to apps/web/public/data
```

Re-running with the same `datasets/products/products.json` and the same `fastembed` version produces bit-identical vectors (the model and inference are both deterministic; there is no sampling involved).
