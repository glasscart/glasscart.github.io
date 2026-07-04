"""One-time export + quantization step for the product-image generation pipeline.

`generate.py` needs a CPU-runnable diffusion pipeline. A hands-on benchmark
(see docs/research/product-images.md) first tried a small distilled model
(`segmind/tiny-sd`) to keep this fast — it wasn't usable at *any* resolution
or step count tried, rendering a generic circular blob regardless of what the
product actually was (a book prompt produced the same shape as a headphones
prompt). The distilled model's capacity, not its speed, was the problem, so
this pipeline uses the full, non-distilled `stable-diffusion-v1-5/stable-diffusion-v1-5`
instead — recognizable output across every category tested, at the cost of a
genuinely long batch job (see generate.py's docstring for the measured
per-image time). INT8 quantization here is a partial mitigation, not a full
fix: unlike the small model, this UNet's cost is dominated by convolutions,
which ONNX Runtime's *dynamic* quantization doesn't accelerate much (it
mainly speeds up matrix multiplies) — so quantization buys ~4x smaller
weights and a real but modest speedup, not an order of magnitude.

PyTorch/diffusers are needed here only to trace the model graph for export —
they are never a dependency of the deployed site or of `generate.py`'s normal
runtime, matching GlassCart's CPU-only, ONNX-preferred house style. This is
why these packages live in the opt-in `imagegen` dependency group instead of
the project's default dependencies (see pyproject.toml).

Usage:
    uv sync --group imagegen
    uv run --group imagegen training/product_images/export_onnx.py
    uv run --group imagegen training/product_images/generate.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

MODEL_ID = "stable-diffusion-v1-5/stable-diffusion-v1-5"

HERE = Path(__file__).parent
HF_CACHE_DIR = HERE / "hf_cache"
EXPORT_DIR = HERE / "onnx_fp32"  # transient, deleted at the end
QUANTIZED_DIR = HERE / "onnx_quantized"  # consumed by generate.py

SUBMODELS = ["unet", "text_encoder", "vae_decoder", "vae_encoder"]


def export_fp32() -> None:
    if EXPORT_DIR.exists():
        shutil.rmtree(EXPORT_DIR)
    env = {**os.environ, "HF_HOME": str(HF_CACHE_DIR), "HUGGINGFACE_HUB_CACHE": str(HF_CACHE_DIR)}
    print(f"Exporting {MODEL_ID} to ONNX (fp32) — downloads ~1GB, takes a few minutes...")
    subprocess.run(
        [sys.executable, "-m", "optimum.exporters.onnx", "--model", MODEL_ID, "--task", "stable-diffusion", str(EXPORT_DIR)],
        env=env,
        check=True,
    )


def quantize() -> None:
    from onnxruntime.quantization import QuantType, quantize_dynamic

    if QUANTIZED_DIR.exists():
        shutil.rmtree(QUANTIZED_DIR)
    shutil.copytree(EXPORT_DIR, QUANTIZED_DIR, ignore=shutil.ignore_patterns("*.onnx", "*.onnx_data"))

    for name in SUBMODELS:
        src = EXPORT_DIR / name / "model.onnx"
        dst = QUANTIZED_DIR / name / "model.onnx"
        if not src.exists():
            raise SystemExit(f"expected {src} after export — optimum's export layout may have changed")
        # Sub-models over ONNX's 2GB inline-data limit (the UNet, at this
        # model size) get their weights externalized into a sibling
        # `model.onnx_data` file by the exporter — quantize_dynamic needs to
        # be told that explicitly, both to read the input and to size its
        # own output correctly.
        external_data = src.with_suffix(".onnx_data")
        has_external = external_data.exists()
        print(f"Quantizing {name}{' (external data)' if has_external else ''}...")
        quantize_dynamic(str(src), str(dst), weight_type=QuantType.QUInt8, use_external_data_format=has_external)
        before = src.stat().st_size + (external_data.stat().st_size if has_external else 0)
        after = sum(f.stat().st_size for f in dst.parent.glob("model.onnx*"))
        print(f"  {name}: {before / 1e6:.0f}MB -> {after / 1e6:.0f}MB ({after / before * 100:.0f}%)")


def main() -> None:
    export_fp32()
    quantize()
    shutil.rmtree(EXPORT_DIR)
    print(f"\nQuantized pipeline ready at {QUANTIZED_DIR}")
    print("Next: uv run --group imagegen training/product_images/generate.py")


if __name__ == "__main__":
    main()
