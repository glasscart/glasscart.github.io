"""GlassCart search service.

This is an *optional* backend. The web app's hybrid search runs entirely
client-side (BM25 in TypeScript, semantic search via transformers.js) so
the whole site works unmodified on GitHub Pages with no server at all. This
service exists as:

1. A reference server-side implementation of the exact same algorithm, for
   people who want to run search behind a real backend instead.
2. A demonstration of the "pluggable provider" pattern GlassCart uses
   elsewhere (e.g. optional LLM providers) — present, documented, and fully
   functional, but never required.

Run locally:
    uv run uvicorn services.search.app.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import DEFAULT_LIMIT, FUSION_ALPHA, MAX_LIMIT
from .corpus import load_corpus
from .hybrid import search
from .schemas import HealthResponse, SearchResponse

app = FastAPI(
    title="GlassCart Search Service",
    description="Reference server-side implementation of GlassCart's hybrid (BM25 + semantic) product search.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local reference service; tighten before any real deployment
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    corpus = load_corpus()
    return HealthResponse(status="ok", corpus_size=len(corpus.products))


@app.get("/search", response_model=SearchResponse)
def search_endpoint(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    alpha: float = Query(FUSION_ALPHA, ge=0.0, le=1.0, description="BM25 weight in [0, 1]; (1 - alpha) goes to semantic"),
) -> SearchResponse:
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty")
    results, glass = search(q, limit=limit, alpha=alpha)
    return SearchResponse(query=q, results=results, glass=glass)
