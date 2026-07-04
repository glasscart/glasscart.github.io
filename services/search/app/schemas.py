from __future__ import annotations

from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    bm25_raw: float
    bm25_normalized: float
    semantic_raw_cosine: float
    semantic_normalized: float
    fused: float


class SearchResultItem(BaseModel):
    id: str
    title: str
    description: str
    category: str
    brand: str
    price: float
    currency: str
    rating: float
    rating_count: int
    rank: int
    score: ScoreBreakdown


class GlassTiming(BaseModel):
    tokenize_query_ms: float
    bm25_score_ms: float
    embed_query_ms: float
    semantic_score_ms: float
    fusion_ms: float
    total_ms: float


class GlassExplanation(BaseModel):
    why_ai_was_used: str = (
        "Keyword matching alone misses paraphrases and synonyms; a pure embedding "
        "search misses exact brand/SKU matches. Hybrid search covers both."
    )
    bm25_k1: float
    bm25_b: float
    fusion_alpha: float
    embedding_model: str
    embedding_dim: int
    embedding_source: str
    corpus_size: int
    artifact_generated_at: str | None
    timing: GlassTiming
    limitations: list[str] = Field(
        default_factory=lambda: [
            "Synthetic, templated catalog — lexical diversity is lower than a real marketplace.",
            "all-MiniLM-L6-v2 is English-only and not fine-tuned on e-commerce data.",
            "Static index: newly added products require rebuilding the embedding artifact.",
        ]
    )


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResultItem]
    glass: GlassExplanation


class HealthResponse(BaseModel):
    status: str
    corpus_size: int
