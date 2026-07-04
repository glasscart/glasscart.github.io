"""Publish generated data/model artifacts as static assets for the web app.

The web app is a static site (must work unmodified on GitHub Pages), so it
cannot reach into `datasets/` or `models/` at runtime — those artifacts need
to be copied into `apps/web/public/data/`, which Vite serves/bundles as-is.

Usage:
    uv run scripts/sync_web_data.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DEST = REPO_ROOT / "apps" / "web" / "public" / "data"

# (source, dest_name) pairs: dest_name is explicit because several
# subsystems each ship their own manifest.json, so basename alone would
# collide (search-embeddings/manifest.json vs. reviews/manifest.json).
SOURCES = [
    (REPO_ROOT / "datasets" / "products" / "products.json", "products.json"),
    (REPO_ROOT / "models" / "search-embeddings" / "product_embeddings.json", "product_embeddings.json"),
    (REPO_ROOT / "models" / "search-embeddings" / "manifest.json", "manifest.json"),
    (REPO_ROOT / "datasets" / "reviews" / "reviews.json", "reviews.json"),
    (REPO_ROOT / "models" / "reviews" / "review_analysis.json", "review_analysis.json"),
    (REPO_ROOT / "models" / "reviews" / "product_review_summary.json", "product_review_summary.json"),
    (REPO_ROOT / "models" / "reviews" / "manifest.json", "reviews_manifest.json"),
    (REPO_ROOT / "models" / "pricing" / "pricing_recommendations.json", "pricing_recommendations.json"),
    (REPO_ROOT / "models" / "pricing" / "manifest.json", "pricing_manifest.json"),
]


IMAGES_SRC_DIR = REPO_ROOT / "datasets" / "products" / "images"


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for src, dest_name in SOURCES:
        if not src.exists():
            raise FileNotFoundError(
                f"{src} does not exist — run the dataset/training scripts first."
            )
        shutil.copyfile(src, DEST / dest_name)
        print(f"{src} -> {DEST / dest_name}")

    # Product images are optional (see training/product_images/, gated behind
    # the `imagegen` dependency group) — copy them if generated, but don't
    # fail the build if they haven't been. ProductImage.tsx falls back to a
    # procedural placeholder for any product without a generated image.
    if IMAGES_SRC_DIR.exists():
        images_dest_dir = DEST / "images"
        images_dest_dir.mkdir(parents=True, exist_ok=True)
        images = list(IMAGES_SRC_DIR.glob("*.png"))
        for image in images:
            shutil.copyfile(image, images_dest_dir / image.name)
        print(f"{IMAGES_SRC_DIR} -> {images_dest_dir} ({len(images)} images)")
    else:
        print(f"{IMAGES_SRC_DIR} not found — skipping (run training/product_images/ to generate)")


if __name__ == "__main__":
    main()
