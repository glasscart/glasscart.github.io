"""Hybrid (BM25 + semantic) search over the product corpus.

Mirrors `apps/web/src/lib/search/hybrid.ts` so the server-side and
client-side implementations are two independent renderings of the same
documented algorithm (see docs/research/search-and-retrieval.md §4),
not two different search engines that happen to agree by coincidence.
"""

from __future__ import annotations

import time
from functools import lru_cache

import numpy as np
from rank_bm25 import BM25Okapi

from .config import BM25_B, BM25_K1, EMBEDDING_MODEL_NAME, FUSION_ALPHA
from .corpus import Corpus, load_corpus, tokenize
from .schemas import GlassExplanation, GlassTiming, ScoreBreakdown, SearchResultItem


@lru_cache(maxsize=1)
def _bm25_index() -> BM25Okapi:
    corpus = load_corpus()
    return BM25Okapi(corpus.tokenized_docs, k1=BM25_K1, b=BM25_B)


@lru_cache(maxsize=1)
def _embedding_model():
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=EMBEDDING_MODEL_NAME)


def _min_max_normalize(values: np.ndarray) -> np.ndarray:
    lo, hi = float(values.min()), float(values.max())
    if hi - lo < 1e-9:
        return np.zeros_like(values)
    return (values - lo) / (hi - lo)


def search(query: str, limit: int, alpha: float = FUSION_ALPHA) -> tuple[list[SearchResultItem], GlassExplanation]:
    t_start = time.perf_counter()
    corpus: Corpus = load_corpus()

    t0 = time.perf_counter()
    query_tokens = tokenize(query)
    t_tokenize = time.perf_counter() - t0

    t0 = time.perf_counter()
    bm25_raw = np.asarray(_bm25_index().get_scores(query_tokens), dtype=np.float64)
    t_bm25 = time.perf_counter() - t0

    t0 = time.perf_counter()
    query_vector = next(_embedding_model().embed([query]))
    query_vector = np.asarray(query_vector, dtype=np.float32)
    t_embed = time.perf_counter() - t0

    t0 = time.perf_counter()
    # Embedding vectors are already L2-normalized, so the dot product is cosine similarity.
    semantic_raw = corpus.embedding_matrix @ query_vector
    t_semantic = time.perf_counter() - t0

    t0 = time.perf_counter()
    bm25_norm = _min_max_normalize(bm25_raw)
    semantic_norm = _min_max_normalize(semantic_raw)
    fused = alpha * bm25_norm + (1 - alpha) * semantic_norm
    order = np.argsort(-fused)[:limit]
    t_fusion = time.perf_counter() - t0

    results: list[SearchResultItem] = []
    for rank, idx in enumerate(order, start=1):
        product = corpus.products[idx]
        results.append(
            SearchResultItem(
                **{k: product[k] for k in ("id", "title", "description", "category", "brand",
                                            "price", "currency", "rating", "rating_count")},
                rank=rank,
                score=ScoreBreakdown(
                    bm25_raw=round(float(bm25_raw[idx]), 6),
                    bm25_normalized=round(float(bm25_norm[idx]), 6),
                    semantic_raw_cosine=round(float(semantic_raw[idx]), 6),
                    semantic_normalized=round(float(semantic_norm[idx]), 6),
                    fused=round(float(fused[idx]), 6),
                ),
            )
        )

    total = time.perf_counter() - t_start
    glass = GlassExplanation(
        bm25_k1=BM25_K1,
        bm25_b=BM25_B,
        fusion_alpha=alpha,
        embedding_model=EMBEDDING_MODEL_NAME,
        embedding_dim=int(corpus.embedding_matrix.shape[1]),
        embedding_source="precomputed offline artifact (models/search-embeddings/product_embeddings.json); query embedded live server-side",
        corpus_size=len(corpus.products),
        artifact_generated_at=corpus.embedding_manifest.get("generated_at"),
        timing=GlassTiming(
            tokenize_query_ms=round(t_tokenize * 1000, 3),
            bm25_score_ms=round(t_bm25 * 1000, 3),
            embed_query_ms=round(t_embed * 1000, 3),
            semantic_score_ms=round(t_semantic * 1000, 3),
            fusion_ms=round(t_fusion * 1000, 3),
            total_ms=round(total * 1000, 3),
        ),
    )
    return results, glass
