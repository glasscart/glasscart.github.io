# Architecture Overview

## Monorepo layout

```
glasscart/
├── apps/
│   └── web/                  # React + TypeScript + Vite + Tailwind SPA (the only deployed app today)
├── packages/
│   └── glass-core/           # (reserved) shared TS types/utilities across future apps
├── services/
│   └── search/                # Optional FastAPI reference backend for hybrid search
├── training/
│   └── search_embeddings/     # Offline embedding-index build pipeline
├── datasets/
│   └── products/              # Synthetic dataset generator + generated data + dataset card
├── models/
│   └── search-embeddings/     # Generated embedding artifacts + model card
├── docs/                      # This MkDocs site, including docs/research/ bibliographies
├── scripts/                   # Cross-cutting automation (data sync, etc.)
└── .github/workflows/         # CI: lint/test/build, retrain, GitHub Pages deploy
```

This mirrors the long-term structure described in the project brief, but only the directories needed by the current vertical slice (search) are populated with real code. Empty categories from the brief (recommendation, ranking, pricing, fraud, vision, …) are intentionally *not* stubbed out — see the [roadmap](../roadmap.md) for what's planned instead of faked.

## The static-first constraint

GlassCart must be fully deployable to **GitHub Pages** — a static file host with no server-side execution, database, or long-running process, and published-size/bandwidth limits (see [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)). Every architectural decision in the search slice traces back to this constraint:

- **No search index server.** BM25 is implemented in pure TypeScript (`apps/web/src/lib/search/bm25.ts`) and runs in the visitor's browser over a catalog shipped as a static JSON asset.
- **No inference server for embeddings.** The product catalog is embedded *offline*, once, in Python (`training/search_embeddings/build_index.py`), and the resulting vectors are shipped as a static asset. Only the user's *query* needs to be embedded live — and that happens **in the browser**, via [transformers.js](https://huggingface.co/docs/transformers.js) running the same model through ONNX Runtime Web (WebAssembly). No network call is made with the query text.
- **Hash-based routing.** `apps/web` uses `HashRouter`, not `BrowserRouter` — GitHub Pages has no server-side rewrite rule to redirect a deep link like `https://glasscart.github.io/search` back to `index.html` on a hard refresh, but a hash route (`/#/search`) always resolves correctly because the part after `#` is never sent to the server at all.
- **Optional backend, never required.** `services/search` is a real, working FastAPI implementation of the exact same hybrid-search algorithm, useful if someone wants to run search behind an actual server — but the deployed static site never depends on it. `apps/web` picks between the client-side and API-backed implementations via a small provider abstraction (`apps/web/src/lib/search/provider.ts`), controlled by an optional `VITE_SEARCH_API_URL` build-time env var. This is the same "pluggable provider" pattern the project intends to use for optional LLM backends (Ollama, LM Studio, OpenAI, Anthropic) elsewhere.

## Two implementations, one algorithm

Search is implemented **twice** — once in TypeScript (client-side, `apps/web/src/lib/search/`) and once in Python (`services/search/app/`) — deliberately, not out of duplication. Both:

- use the same BM25 `k1`/`b` constants and the same linear fusion weight `alpha` (see `apps/web/src/lib/search/config.ts` and `services/search/app/config.py`)
- embed with the same underlying model weights (`sentence-transformers/all-MiniLM-L6-v2` offline / `Xenova/all-MiniLM-L6-v2` in-browser — two export formats of the same checkpoint)
- produce the same `GlassExplanation` shape, so Glass Mode's UI doesn't need to know which provider answered the query

This is intentional redundancy: a reference implementation for people who want a "real backend" version, kept honest by sharing named constants and a shared research doc rather than by code-sharing across languages.

## Reproducibility pipeline

```
datasets/products/generate.py          (seeded, deterministic)
        │
        ▼
datasets/products/products.json  ──────────────┐
        │                                       │
        ▼                                       │
training/search_embeddings/build_index.py       │  (services/search reads
        │                                       │   both files directly)
        ▼                                       │
models/search-embeddings/product_embeddings.json│
models/search-embeddings/manifest.json          │
        │                                       │
        ▼                                       ▼
apps/web/scripts/sync-data.mjs  →  apps/web/public/data/*.json
        │
        ▼
apps/web (Vite dev server / static build)
```

Everything left of `apps/web/public/data/` is committed to the repository (Workflow A from the brief: clone and run immediately, no training required). `apps/web/public/data/` itself is *not* committed — it's regenerated automatically by `npm run dev` / `npm run build` via a small Node script, so the web app never needs Python installed just to run.
