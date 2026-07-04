"""Generate a placeholder product photo for every product in the catalog.

GlassCart's catalog has no real product photography (see the dataset card's
"No images" limitation). This script runs the quantized pipeline produced by
`export_onnx.py` — full Stable Diffusion 1.5, not a distilled model — over
every product.

A distilled model (`segmind/tiny-sd`) was tried first, at several
resolutions and step counts, specifically to keep this fast. It was
rejected: it rendered the same generic circular blob regardless of the
actual product — a spiral-bound book and a pair of headphones produced
near-identical shapes — because a heavily distilled model at this size
doesn't have the capacity to represent GlassCart's category diversity, not
because of resolution or step count. Full SD1.5 produced recognizable,
category-appropriate output (a real stand mixer, real headphones, a real
book) on every prompt tried. See docs/research/product-images.md for the
comparison and models/product-images/MODEL_CARD.md for the full benchmark
table.

That capacity costs real time: this UNet's compute is dominated by
convolutions, which ONNX Runtime's dynamic INT8 quantization doesn't
accelerate much (it mainly speeds up matrix multiplies), so quantization
here buys ~4x smaller weights and a real but modest speedup — not the ~50x
the same technique gave the (rejected) distilled model. Measured: ~370s and
~5.2GB peak RAM per image at 512x512/25 steps, extrapolating to roughly a
day and a half for the full catalog. That is a genuinely long batch job,
accepted deliberately in exchange for output that actually looks like the
product it's supposed to represent.

The output is still intentionally rough — a soft, occasionally surreal
rendering, not catalog-quality photography — and is always labeled that way
in the UI (see apps/web's ProductImage Glass Mode caption). That's a
deliberate choice, not an oversight: GlassCart would rather show a real (if
imperfect) model output than fake a photo or hide the limitation.

Every image is generated with a seed derived only from the product id, so
re-running this script against an unchanged catalog reproduces byte-identical
images.

Given how long a full run takes, this script skips products that already
have an image on disk by default, so it's safe to interrupt and resume.
Pass `--force` to regenerate everything (e.g. after changing the model or
the prompt template).

Usage (see export_onnx.py's docstring for why this uses a standalone venv
instead of the project's main `uv`-managed dependencies):
    python3 -m venv .venv-imagegen
    .venv-imagegen/bin/pip install -r training/product_images/requirements.txt
    .venv-imagegen/bin/python training/product_images/export_onnx.py   # one-time
    .venv-imagegen/bin/python training/product_images/generate.py
    .venv-imagegen/bin/python training/product_images/generate.py --force
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from importlib.metadata import version as pkg_version
from pathlib import Path

import torch
from optimum.onnxruntime import ORTStableDiffusionPipeline

MODEL_ID = "stable-diffusion-v1-5/stable-diffusion-v1-5"
WIDTH = 512
HEIGHT = 512
STEPS = 25

HERE = Path(__file__).parent
QUANTIZED_DIR = HERE / "onnx_quantized"

PRODUCTS_PATH = Path(__file__).parents[2] / "datasets" / "products" / "products.json"
IMAGES_DIR = PRODUCTS_PATH.parent / "images"
MANIFEST_PATH = Path(__file__).parents[2] / "models" / "product-images" / "manifest.json"


def _seed_for(product_id: str) -> int:
    digest = hashlib.sha256(product_id.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def _prompt_for(product: dict) -> str:
    # Category is included explicitly, not just implied by the title's noun —
    # some templated titles (e.g. "Comprehensive Beginner's Guide") don't
    # contain an obvious object noun on their own, and category grounding
    # costs nothing when it's redundant with the title.
    return (
        f"product photo of {product['title'].lower()}, a {product['category'].lower()} item, "
        f"{product['material'].lower()}, white background, studio lighting"
    )


def generate(force: bool = False) -> None:
    if not QUANTIZED_DIR.exists():
        raise SystemExit(
            f"{QUANTIZED_DIR} not found — run "
            "`python training/product_images/export_onnx.py` (from the .venv-imagegen environment) first."
        )

    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    pending = products if force else [p for p in products if not (IMAGES_DIR / f"{p['id']}.png").exists()]
    skipped = len(products) - len(pending)
    if skipped:
        print(f"Skipping {skipped} products with an existing image (use --force to regenerate everything).")
    if not pending:
        print("Nothing to do — every product already has an image.")
        return

    pipe = ORTStableDiffusionPipeline.from_pretrained(QUANTIZED_DIR, export=False)

    started_at = datetime.now(timezone.utc)
    t0 = time.time()
    for i, product in enumerate(pending, 1):
        generator = torch.Generator(device="cpu").manual_seed(_seed_for(product["id"]))
        image = pipe(
            _prompt_for(product),
            num_inference_steps=STEPS,
            height=HEIGHT,
            width=WIDTH,
            generator=generator,
        ).images[0]
        image.save(IMAGES_DIR / f"{product['id']}.png")
        elapsed = time.time() - t0
        eta_hours = (elapsed / i) * (len(pending) - i) / 3600
        print(f"{i}/{len(pending)} images generated ({elapsed:.0f}s elapsed, ~{eta_hours:.1f}h remaining)", flush=True)
    finished_at = datetime.now(timezone.utc)

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "model": MODEL_ID,
        "quantization": "onnxruntime dynamic INT8 (QUInt8)",
        "width": WIDTH,
        "height": HEIGHT,
        "steps": STEPS,
        "num_images_total": len(products),
        "num_images_generated_this_run": len(pending),
        "seed_scheme": "int(sha256(product_id).hexdigest()[:8], 16)",
        "generated_at": started_at.isoformat(),
        "build_duration_seconds": round((finished_at - started_at).total_seconds(), 1),
        "runtime": {
            "python": platform.python_version(),
            "onnxruntime": pkg_version("onnxruntime"),
            "optimum": pkg_version("optimum"),
        },
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {len(pending)} images to {IMAGES_DIR} ({len(products)} total in catalog)")
    print(f"Manifest -> {MANIFEST_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Regenerate every image, including ones that already exist.")
    args = parser.parse_args()
    generate(force=args.force)


if __name__ == "__main__":
    main()
