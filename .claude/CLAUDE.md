# GlassCart

An open-source, educational, AI-transparent commerce platform. Full founding vision and scope: [`docs/PROMPT.md`](../docs/PROMPT.md) — read it once for *why*, don't expect this file to repeat it.

## Status (keep this section honest — update it as subsystems land)

Only **search** is built end to end: synthetic product catalog → BM25 + semantic hybrid search, running entirely client-side, with a model card, dataset card, and Glass Mode diagnostics. Everything else in PROMPT.md's scope (recommendation, ranking, pricing, inventory, fraud, reviews, vision, NLP, analytics, CI/CD, GitHub Pages deploy) is **intentionally not started**, not forgotten. `scripts/`, `.github/`, `packages/`, `docs/architecture/`, `docs/subsystems/` exist as empty scaffolding for this reason.

Treat search as the **reference pattern** for every subsystem that follows, not a one-off. See "Adding a new subsystem" below before building the next one from scratch.

## Non-negotiable invariants

These are easy to violate by accident because they cut against normal instincts ("just call the backend", "add a required API key"). They are the whole point of the project — do not trade them away for convenience.

- **Static-first.** The site must keep working with zero backend, deployable as-is to GitHub Pages. Anything under `services/` is an optional reference mirror of logic that already runs client-side (see `services/search/app/main.py`'s module docstring) — never a hard dependency. Build new AI features client-side first; a server-side twin is optional bonus content, not step one.
- **Every AI artifact is a card.** New model or dataset → `MODEL_CARD.md` / `DATASET_CARD.md` next to it, following the format in `models/search-embeddings/` and `datasets/products/`. Diagnostics (latency, scores, model version, limitations) surface in the UI through Glass Mode — nothing AI-driven is allowed to be a black box.
- **Reproducible, deterministic.** Generation is seeded, builds don't drift, and every card's "Reproducibility" section lists exact regen commands that actually work if run in order.
- **No paid APIs required, ever.** Optional LLM providers (Ollama, LM Studio, OpenAI, Anthropic) are pluggable adapters, never a hard import or a required env var for the core experience to function.

## Repo map

| Path | What | Stack |
|---|---|---|
| `apps/web` | The static site | React 19, Vite 8, Tailwind 4, Zustand, TanStack Query, `@xenova/transformers` for in-browser ONNX inference |
| `services/` | Optional reference backends (mirror client-side logic) | FastAPI, Pydantic |
| `training/` | Offline pipelines that produce versioned artifacts | Python, `fastembed`/`onnxruntime` (CPU-only, no PyTorch/GPU) |
| `models/` | Versioned model artifacts + `MODEL_CARD.md` per model | — |
| `datasets/` | Seeded synthetic data generators + `DATASET_CARD.md` per dataset | Python |
| `docs/research/` | Per-subsystem bibliography: cite sources *and* explain how each shaped the implementation — never a bare link dump | — |
| `docs/PROMPT.md` | Founding vision / full scope | — |

## Commands

```bash
# Python workspace (uv-managed, Python >=3.11)
uv sync
uv run datasets/products/generate.py                    # regenerate the product catalog
uv run training/search_embeddings/build_index.py        # rebuild the embedding index
uv run uvicorn services.search.app.main:app --reload --port 8000   # optional reference backend

# Web app (apps/web)
npm run dev       # local dev server
npm run build     # tsc -b && vite build
npm run lint      # oxlint (not eslint)
npm run preview
```

No test suite exists yet (`services/search/tests/` is an empty scaffold — don't assume tests are missing by accident, but don't be surprised if you're the one asked to write the first ones). No CI is wired up yet.

## Conventions

- Module-level docstrings explain **why an architectural choice was made**, not just what the module does — see `training/search_embeddings/build_index.py` and `services/search/app/main.py` for the standard. Match this depth for new subsystems; it's the project's substitute for tribal knowledge.
- `docs/research/<subsystem>.md` bibliographies are written *after* the subsystem is built, explaining which sources actually influenced decisions — not compiled speculatively before writing code.
- Card sections are fixed vocabulary — don't invent new headings ad hoc, add to the existing structure in `models/search-embeddings/MODEL_CARD.md` / `datasets/products/DATASET_CARD.md` instead.

## Adding a new subsystem

Before writing a new recommendation/ranking/pricing/fraud/etc. subsystem, mirror the search subsystem's shape unless there's a documented reason not to:

1. Research first, write `docs/research/<subsystem>.md` as you go (bibliography + rationale, not before code).
2. Synthetic data generator in `datasets/` with a seeded RNG + `DATASET_CARD.md`.
3. Offline training/build step in `training/` that writes a versioned, deterministic artifact to `models/<name>/` + `MODEL_CARD.md`.
4. Client-side inference path in `apps/web` first; an optional FastAPI mirror in `services/` second, if at all.
5. Glass Mode diagnostics wired into the UI for anything AI-assisted.
6. No new required env vars, API keys, or paid services.
