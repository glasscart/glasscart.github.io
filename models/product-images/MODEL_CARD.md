# Model Card: `product-images` (Stable Diffusion 1.5, INT8-quantized ONNX)

Following the structure proposed by [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993) (Mitchell et al., 2019).

> **Status: built and benchmarked, not shipped.** This pipeline runs successfully and produces correctly-shaped, recognizable products (see "Metrics"), but its output quality wasn't judged good enough for the live site. `apps/web/src/components/ProductImage.tsx` currently renders a procedural (non-AI) placeholder instead, and no generated images are checked into the repo. This card is kept as an accurate record of a real, working, honestly-benchmarked attempt — including the model choice this pipeline rejected along the way — for anyone who wants to revisit it with a different model or approach. See [docs/roadmap.md](../../docs/roadmap.md).

## Purpose

Give every product in the synthetic catalog a picture, without any real product photography to draw from and without a paid image-generation API. The result is deliberately a **low-fidelity placeholder**, not catalog-quality photography — see "Known Limitations" below. This is a real, local text-to-image model, not a hard-coded image dressed up as one.

## Architecture

- **Base model**: [`stable-diffusion-v1-5/stable-diffusion-v1-5`](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5), the full (non-distilled) Stable Diffusion 1.5 checkpoint, licensed `creativeml-openrail-m`.
- **Runtime**: exported to ONNX (`optimum.exporters.onnx`) and quantized with ONNX Runtime's dynamic INT8 quantization (`onnxruntime.quantization.quantize_dynamic`, `QuantType.QUInt8`) — run entirely offline in `training/product_images/`, never in the browser and never at request time. The UNet's weights exceed ONNX's 2GB inline-data limit and are stored in an external `model.onnx_data` file; both export and quantization handle this explicitly (`use_external_data_format=True`).
- **Resolution / steps**: 512×512, 25 sampling steps, default (PNDM) scheduler — the base model's standard settings, not shrunk. See "Metrics" for why: a distilled model tried first (see "A smaller model was tried and rejected" below) needed no such shrinking to be fast, but couldn't render recognizable output at any size; the full model needed no fidelity trade-off to render correctly, only a time budget.
- **Why quantized ONNX and not PyTorch**: quantization still helps here — INT8 shrinks every sub-model to ~25% of its fp32 size (the UNet: 3.4GB → 863MB) and gives a real, if modest, inference speedup (see "Metrics"). PyTorch/diffusers are used only transiently, to trace the ONNX export; `generate.py`'s actual runtime dependency is `onnxruntime` + `optimum`, matching the project's ONNX-only house style for the *repeated* cost of this pipeline.

### A smaller model was tried and rejected

The first version of this pipeline used [`segmind/tiny-sd`](https://huggingface.co/segmind/tiny-sd), a distilled Stable Diffusion variant, specifically to keep the batch job fast (the same INT8-quantization trick gave that model a ~50x speedup, turning a ~33-hour job into ~35-40 minutes). It was rejected after inspecting real output: at every resolution and step count tried (128×128 through 256×256, 4 through 20 steps), it rendered a generic circular blob largely regardless of the actual product — a spiral-bound book prompt and a wireless-headphones prompt produced near-identical shapes. This was a *capacity* problem (the distilled model doesn't have enough parameters to represent GlassCart's category diversity), not a resolution or step-count problem — more steps at small sizes made output *worse*, converging toward an almost-blank frame rather than more detail. Full-size, non-distilled SD1.5 produced a correctly-shaped, recognizable object (a real stand mixer, real over-ear headphones, a real spiral-bound book) on every one of the same test prompts. See [docs/research/product-images.md](../../docs/research/product-images.md) for the full comparison.

## Training Data (of the base model)

We did not train this model. `stable-diffusion-v1-5` is a publicly released checkpoint trained by Runway/CompVis/Stability AI on subsets of LAION-5B; see its [model card](https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5) for training details. We did not fine-tune it on GlassCart's catalog or on any product imagery.

## What GlassCart Does With It

`training/product_images/export_onnx.py` performs the one-time ONNX export + quantization (requires the optional `imagegen` dependency group, including a transient PyTorch install used only to trace the export — see its docstring for why). `training/product_images/generate.py` then loads the quantized pipeline and, for every product in [`products.json`](../../datasets/products/DATASET_CARD.md), builds a prompt from its title, category, and material and a seed derived from its id, and writes `datasets/products/images/<id>.png`. Both scripts are deterministic and reproducible; neither needs a GPU or a paid API — only time.

`apps/web/src/components/ProductImage.tsx` renders the generated image where one exists, with a graceful fallback to a procedural placeholder (a category-tinted gradient) where it doesn't. When Glass Mode is on, a caption identifies the image as AI-generated and links back to this card.

## Metrics

We do not report standard image-generation quality metrics (FID, CLIP score, etc.) — this is a placeholder-art generator for a synthetic demo catalog, not a benchmarked text-to-image system, and such scores would not be meaningful here. What we do report is the operational benchmark that drove every design choice in this pipeline (measured on a 12-core CPU-only machine, no GPU):

| Config | Model | Inference time/image | Peak RSS | Extrapolated to 312 images | Output |
|---|---|---|---|---|---|
| INT8 ONNX, 256×256, 15 steps | tiny-sd (rejected) | ~40–46s | ~1.5GB | ~3.5–4 hours | generic blob, wrong for many categories |
| fp32 PyTorch, 512×512, 25 steps | SD1.5 | ~538–664s | not measured | ~51 hours | **recognizable, correct category** |
| INT8 ONNX, 512×512, 15 steps, DPM++/Karras | SD1.5 | ~240s | ~5.2GB | ~20.8 hours | recognizable but over-abstracted (tried to cut time, cost too much composition) |
| **INT8 ONNX, 512×512, 25 steps, default scheduler (used)** | **SD1.5** | **~370s** | **~5.2GB** | **~32 hours** | **recognizable, correct category, grainier texture than fp32** |

Unlike the distilled model, quantization here is a modest win, not a dramatic one: SD1.5's UNet is dominated by convolutions, and ONNX Runtime's *dynamic* quantization mainly accelerates matrix multiplies, so it cuts weight size ~4x but inference time only ~30-35% versus fp32 at the same settings.

## Confidence & Uncertainty

Not applicable — this is a generative model producing an image, not a classifier or scorer producing a confidence value. There is nothing to calibrate.

## Hardware Used

Built and benchmarked on CPU only (no GPU required or used, no PyTorch at generation time — only during the one-time export). Exact runtime versions are recorded in `models/product-images/manifest.json`, regenerated on every run.

## Known Limitations & Failure Cases

- **Deliberately low fidelity**: quantization introduces a visibly grainier, more painterly texture than the fp32 baseline, and the model can still misinterpret an unusual title/material combination. This is disclosed in the UI rather than hidden.
- **Prompt is templated, not curated**: the prompt is mechanically built from `title` + `category` + `material`; it is not hand-tuned per product, so quality still varies across products even with a capable base model.
- **No text/logo rendering**: like all diffusion models at this scale, it cannot render legible text, so no product ever shows real branding or labels (arguably a feature for a synthetic catalog).
- **Slow, sequential batch job**: ~370s/image means the full catalog takes on the order of a day; this is an accepted, deliberate trade-off (see "A smaller model was tried and rejected"), not an oversight. `generate.py` skips products that already have an image so the job is safe to interrupt and resume.
- **Static, batch-generated**: images are precomputed for the current catalog. Adding a product requires re-running `generate.py`; there's no on-demand generation path.
- **License terms carry over**: `stable-diffusion-v1-5` is `creativeml-openrail-m`, which permits redistribution and reuse (including the generated images) subject to the license's use-based restrictions (see the [license text](https://huggingface.co/spaces/CompVis/stable-diffusion-license)) — this pipeline does not add any further restriction, but doesn't relax that one either.

## Ethical & Privacy Considerations

- No user data is used anywhere in this pipeline; all inputs are synthetic catalog fields.
- Generation happens entirely offline, ahead of time — no user action ever triggers a generation call, and no user data reaches the model.
- Unlike the rejected distilled-model version, this model's output can be photorealistic-adjacent rather than obviously abstract — the UI's Glass Mode caption explicitly disclosing "AI-generated, not real product photography" is doing real work here, not just documenting an already-obvious limitation.

## Intended Use

Generating an offline, license-clean batch of placeholder product images for GlassCart's synthetic catalog, and as a teaching example of making a real generative pipeline work within a CPU-only, no-paid-API, static-first project — including the honest negative result of trying a smaller model first and rejecting it on measured grounds.

## Non-Intended Use

Not intended to produce photography-grade product images, to represent any real product, or to be used interactively/at request time. Not validated at any resolution, step count, scheduler, or prompt style beyond what's described above.

## Reproducibility

```bash
uv sync --group imagegen
uv run --group imagegen training/product_images/export_onnx.py   # one-time: export + quantize
uv run --group imagegen training/product_images/generate.py      # ~32 hours for the full catalog; safe to interrupt/resume
uv run scripts/sync_web_data.py                                   # publish images to apps/web/public/data
```

Re-running `generate.py` against an unchanged `products.json` and the same pinned `imagegen` dependency versions produces byte-identical images (fixed per-product seed, no randomness left unseeded).
