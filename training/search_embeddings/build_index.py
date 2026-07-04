"""Build the semantic search embedding index for the GlassCart product catalog.

Embeds each product's `title + description` with a small ONNX sentence
embedding model (`sentence-transformers/all-MiniLM-L6-v2`, served through
`fastembed` — no PyTorch, no GPU, ~90MB model, CPU-only). The *same* base
model, exported for the browser as `Xenova/all-MiniLM-L6-v2`, is used by
`transformers.js` at query time (see `apps/web/src/lib/search/semantic.ts`),
so the two sets of vectors live in the same space and cosine similarity
between them is meaningful.

This script is the "offline half" of GlassCart's search pipeline: it does
the expensive part (embedding the whole catalog) once, ahead of time, and
ships the resulting vectors as a static JSON artifact — so the deployed
site never needs a server to run semantic search over the catalog. Only the
user's query is embedded live, in their own browser.

Usage:
    uv run training/search_embeddings/build_index.py
"""

from __future__ import annotations

import json
import platform
from datetime import datetime, timezone
from importlib.metadata import version as pkg_version
from pathlib import Path

from fastembed import TextEmbedding

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BROWSER_MODEL_NAME = "Xenova/all-MiniLM-L6-v2"

PRODUCTS_PATH = Path(__file__).parents[2] / "datasets" / "products" / "products.json"
OUTPUT_DIR = Path(__file__).parents[2] / "models" / "search-embeddings"
EMBEDDINGS_PATH = OUTPUT_DIR / "product_embeddings.json"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"


def _document_text(product: dict) -> str:
    return f"{product['title']}. {product['description']}"


def build() -> None:
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    started_at = datetime.now(timezone.utc)

    model = TextEmbedding(model_name=MODEL_NAME)
    texts = [_document_text(p) for p in products]

    vectors = []
    for embedding in model.embed(texts):
        vectors.append([round(float(x), 6) for x in embedding.tolist()])

    dim = len(vectors[0]) if vectors else 0
    finished_at = datetime.now(timezone.utc)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    EMBEDDINGS_PATH.write_text(
        json.dumps(
            {
                "model": MODEL_NAME,
                "dim": dim,
                "ids": [p["id"] for p in products],
                "vectors": vectors,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    manifest = {
        "model": MODEL_NAME,
        "browser_model": BROWSER_MODEL_NAME,
        "dim": dim,
        "num_products": len(products),
        "embedded_fields": ["title", "description"],
        "normalization": "fastembed default (mean-pooled, L2-normalized)",
        "generated_at": started_at.isoformat(),
        "build_duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "runtime": {
            "python": platform.python_version(),
            "fastembed": pkg_version("fastembed"),
            "onnxruntime": pkg_version("onnxruntime"),
        },
        "dataset_seed": 20260704,
        "artifact": EMBEDDINGS_PATH.name,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Embedded {len(products)} products -> {EMBEDDINGS_PATH} (dim={dim})")
    print(f"Manifest -> {MANIFEST_PATH}")


if __name__ == "__main__":
    build()
