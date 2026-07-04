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

SOURCES = [
    REPO_ROOT / "datasets" / "products" / "products.json",
    REPO_ROOT / "models" / "search-embeddings" / "product_embeddings.json",
    REPO_ROOT / "models" / "search-embeddings" / "manifest.json",
]


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    for src in SOURCES:
        if not src.exists():
            raise FileNotFoundError(
                f"{src} does not exist — run the dataset/training scripts first."
            )
        shutil.copyfile(src, DEST / src.name)
        print(f"{src} -> {DEST / src.name}")


if __name__ == "__main__":
    main()
