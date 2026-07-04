# GlassCart

**AI-first. AI-transparent.**

GlassCart is an open-source, educational, AI-native commerce platform where every AI-assisted decision is explainable, inspectable, reproducible, and replaceable. It is not a copy of any real marketplace's branding or proprietary implementation — it recreates the *concepts, architecture, workflows, and technical challenges* of building a modern AI-powered commerce platform, as a teaching reference.

## Why this exists

Most commerce sites that use AI — for search ranking, recommendations, pricing, fraud detection — treat the AI as a black box: a score appears, a ranking shifts, and the user has no way to ask "why." GlassCart inverts that. Every AI-assisted feature ships with:

- a **model card** (architecture, training data, metrics, limitations, ethics)
- a **dataset card** for anything it was trained or evaluated on
- a **Glass Mode** UI panel showing the live decision's inputs, scores, and latency
- a **research bibliography** tracing every design choice back to a primary source

## Current state: one vertical slice

This is a young, deliberately-scoped project. Rather than stub out every subsystem described in the long-term vision (search, recommendations, ranking, pricing, fraud, reviews, vision, NLP, analytics — see the [roadmap](roadmap.md)), the first milestone builds **one subsystem completely, as a reference pattern**: [hybrid product search](subsystems/search.md).

Everything else — recommendations, pricing, fraud detection, and so on — is documented as intent in the roadmap, not faked as empty scaffolding.

## Glass Mode

Glass Mode is the global transparency toggle. Turn it on anywhere in the app and every AI-assisted UI element exposes:

- why AI was used at all (vs. a simpler deterministic approach)
- model name, version, and architecture
- the exact inputs and parameters that produced this result
- a latency breakdown
- known limitations and failure cases

See [Glass Mode](glass-mode.md) for the full specification, and [the search subsystem](subsystems/search.md) for a concrete implementation.

## Running it locally

```bash
# Python side (dataset + embeddings + optional search API)
uv sync
uv run datasets/products/generate.py
uv run training/search_embeddings/build_index.py

# Web app (works standalone — no backend required)
cd apps/web
npm install
npm run dev
```

See the [root README](https://github.com/glasscart/glasscart.github.io#readme) for the full reproducibility instructions, including how to run the optional FastAPI search service and regenerate every artifact from scratch.

## Documentation map

- [Glass Mode specification](glass-mode.md)
- [Architecture overview](architecture/overview.md)
- [Search subsystem](subsystems/search.md)
- [Research bibliography: search & retrieval](research/search-and-retrieval.md)
- [Roadmap](roadmap.md)
