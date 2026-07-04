"""Hybrid search constants.

These are the *canonical* values for GlassCart's hybrid search — the same
numbers are mirrored in `apps/web/src/lib/search/config.ts` for the
client-side implementation. Keeping them named constants (rather than
buried magic numbers) is what lets Glass Mode display them verbatim as part
of each search result's transparency panel.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PRODUCTS_PATH = REPO_ROOT / "datasets" / "products" / "products.json"
EMBEDDINGS_PATH = REPO_ROOT / "models" / "search-embeddings" / "product_embeddings.json"
MANIFEST_PATH = REPO_ROOT / "models" / "search-embeddings" / "manifest.json"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# BM25 (Robertson & Zaragoza, 2009 — see docs/research/search-and-retrieval.md §1)
BM25_K1 = 1.5  # term-frequency saturation
BM25_B = 0.75  # document-length normalization strength

# Hybrid fusion (linear combination — see docs/research/search-and-retrieval.md §4)
FUSION_ALPHA = 0.5  # weight given to the (normalized) BM25 score; (1 - alpha) goes to semantic

DEFAULT_LIMIT = 12
MAX_LIMIT = 50
