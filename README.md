# GlassCart

**AI-first. AI-transparent.**

An open-source, educational, AI-native commerce platform where every AI-assisted decision is explainable, inspectable, reproducible, and replaceable. GlassCart is not a copy of any real marketplace's branding, assets, or proprietary implementation — it recreates the *concepts, architecture, and technical challenges* of building a modern AI-powered commerce platform, as a teaching reference.

**Live app:** https://glasscart.github.io/ · **Docs:** https://glasscart.github.io/docs/ (source in [`docs/`](docs/index.md), built with MkDocs Material — see [Docs site](#docs-site) below).

This repo is named `glasscart.github.io` deliberately — GitHub only serves a Pages site at the bare root domain (`glasscart.github.io/`, no subpath) when the repo has that exact name; any other repo name would publish under `glasscart.github.io/<repo-name>/` instead. The [`glasscart/glasscart`](https://github.com/glasscart/glasscart) repo is a separate, minimal one — just the GitHub profile card.

## Current state

This project is young and deliberately scoped. Rather than stub out every subsystem in the long-term vision, the first milestone builds **one subsystem completely, end to end, as a reference pattern**: [hybrid product search](docs/subsystems/search.md) — real BM25 keyword search and real sentence-embedding semantic search, fused into one transparent score, running entirely client-side (works unmodified on GitHub Pages, no backend required).

See [`docs/roadmap.md`](docs/roadmap.md) for what's next and why nothing else is stubbed out yet.

## Glass Mode

Flip the **Glass Mode** toggle in the app header and every AI-assisted result exposes its own diagnostics: model name/version/architecture, the exact parameters used, a per-phase latency breakdown, a per-result score breakdown, and known limitations — instead of just rendering an opaque ranked list. See [`docs/glass-mode.md`](docs/glass-mode.md).

## Quickstart (Workflow A — no training required)

The web app works immediately after cloning; the dataset and model artifacts it needs are committed to the repository.

```bash
cd apps/web
npm install
npm run dev
```

Open the printed local URL, type a search query, and toggle Glass Mode.

## Reproducing everything from scratch (Workflow B)

No paid APIs or GPU required — the whole pipeline runs on CPU with open-source, locally-run models.

```bash
# Python: dataset + embeddings + optional backend
uv sync
uv run datasets/products/generate.py            # regenerate the synthetic product catalog
uv run training/search_embeddings/build_index.py  # rebuild the semantic search index
uv run scripts/sync_web_data.py                 # publish artifacts into apps/web/public/data

# Tests
uv run pytest tests services/search/tests -v

# Web app (re-syncs data automatically via predev/prebuild)
cd apps/web && npm install && npm run dev

# Optional: run the reference FastAPI search backend
uv run uvicorn services.search.app.main:app --reload --port 8000
# then build the web app with VITE_SEARCH_API_URL=http://localhost:8000 to use it instead of client-side search
```

## Automated retraining (Workflow C)

`.github/workflows/retrain.yml` runs the same pipeline on a schedule (and on manual dispatch) and opens a pull request with any resulting diff for review — it never pushes directly to `main`.

## Docs site

```bash
uv sync --group docs
uv run mkdocs serve   # http://127.0.0.1:8000
```

Deployed automatically to GitHub Pages by `.github/workflows/pages.yml` alongside the web app (docs live under `/docs/` on the deployed site).

## Repository layout

```
glasscart/
├── apps/web/                  # React + TypeScript + Vite + Tailwind SPA
├── packages/glass-core/        # (reserved) shared TS types across future apps
├── services/search/            # Optional FastAPI reference backend for hybrid search
├── training/search_embeddings/ # Offline embedding-index build pipeline
├── datasets/products/          # Synthetic dataset generator, data, and dataset card
├── models/search-embeddings/   # Generated embedding artifacts and model card
├── docs/                       # MkDocs site, including docs/research/ bibliographies
├── scripts/                    # Cross-cutting automation (data sync, etc.)
└── .github/workflows/          # CI, scheduled retraining, GitHub Pages deploy
```

See [`docs/architecture/overview.md`](docs/architecture/overview.md) for the full architecture writeup, including why the app uses hash-based routing, why embeddings are computed offline but queries embedded client-side, and how the optional FastAPI backend fits in.

## Tech stack

- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, React Router, Zustand, TanStack Query, [`@huggingface/transformers`](https://huggingface.co/docs/transformers.js) (client-side ONNX inference)
- **Python**: 3.12+, managed with [`uv`](https://docs.astral.sh/uv/); [`fastembed`](https://github.com/qdrant/fastembed) (ONNX Runtime, no PyTorch) for offline embeddings, `rank-bm25`, FastAPI for the optional backend
- **Docs**: MkDocs + Material theme
- **CI/CD**: GitHub Actions — lint/test/build, scheduled retraining via PR, GitHub Pages deployment

## License

[MIT](LICENSE).
