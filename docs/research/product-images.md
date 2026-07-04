# Research Notes: Product Placeholder Images

> Bibliography and design rationale for GlassCart's product-image subsystem: a quantized,
> CPU-only text-to-image pipeline that generates one deliberately low-fidelity placeholder photo
> per product, offline, with no GPU and no paid API. This document — like
> [`search-and-retrieval.md`](search-and-retrieval.md) — is written after the fact, from what
> actually drove the implementation, including two rounds of hands-on benchmarking: one that
> ruled out full-precision inference on the target hardware, and a second that ruled out the
> small distilled model chosen to work around the first problem, once its output turned out not
> to be recognizable as the product it was supposed to depict.

---

## 1. Knowledge Distillation for Smaller Diffusion Models — Tried First, Then Rejected

**Explanation.** Full-size Stable Diffusion models (~1B parameters, ~4GB in fp32) are trained to generate high-fidelity images but are correspondingly expensive to run on CPU. Knowledge distillation trains a smaller "student" U-Net to match a larger "teacher" model's outputs, trading some fidelity for a large reduction in size and inference cost. `segmind/tiny-sd`, one such distilled model, was the first candidate tried here specifically to keep the batch job fast.

**Citations.**
- Segmind. *segmind/tiny-sd* model card. https://huggingface.co/segmind/tiny-sd
- Kim, B. K., Song, H. K., Castells, T., & Choi, S. (2023). *BK-SDM: A Lightweight, Fast, and Cheap Version of Stable Diffusion*. arXiv:2305.15798. https://arxiv.org/abs/2305.15798 — the block-removal + distillation methodology this model family is built on.
- Hinton, G., Vinyals, O., & Dean, J. (2015). *Distilling the Knowledge in a Neural Network*. arXiv:1503.02531. https://arxiv.org/abs/1503.02531 — foundational distillation paper.

**Used in GlassCart, then reconsidered:** `tiny-sd`'s small weight footprint (~1GB) delivered on speed — combined with INT8 quantization, a ~35-40 minute batch job for the full catalog. But inspecting real output across categories (see §4) showed it rendering a generic circular blob almost regardless of the actual product: a spiral-bound book prompt and a wireless-headphones prompt produced near-identical shapes. Distillation had traded away more capacity than this catalog's category diversity could tolerate. The pipeline now uses the full, non-distilled `stable-diffusion-v1-5/stable-diffusion-v1-5` instead (see §4b) — this section is kept as a record of what was tried and why it didn't survive contact with real output, not as the current architecture.

---

## 2. Post-Training Dynamic Quantization

**Explanation.** Quantization reduces a model's numeric precision (typically fp32 → int8) after training, shrinking weight storage roughly 4x and often speeding up CPU inference, since integer matrix multiplication has faster code paths than floating point on most CPUs. *Dynamic* quantization (as opposed to *static*) quantizes weights ahead of time but computes activation ranges on the fly during inference, requiring no calibration dataset — a good fit here, since there is no representative "product image" dataset to calibrate against.

**Citations.**
- ONNX Runtime. *Quantize ONNX Models*. https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html
- Jacob, B., Kligys, S., Chen, B., Zhu, M., Tang, M., Howard, A., Adam, H., & Kalenichenko, D. (2018). *Quantization and Training of Neural Networks for Efficient Integer-Arithmetic-Only Inference*. CVPR 2018. https://arxiv.org/abs/1712.05877 — the underlying integer-quantization scheme ONNX Runtime's implementation follows.

**Used in GlassCart:** `training/product_images/export_onnx.py` applies `onnxruntime.quantization.quantize_dynamic` (`QuantType.QUInt8`) to every sub-model (UNet, text encoder, VAE encoder/decoder) after ONNX export, for both models tried. The *size* win was consistent — roughly 4x smaller weights in both cases (tiny-sd: 2.1GB → 533MB; SD1.5: 4.1GB → ~1.1GB). The *speed* win was not: for tiny-sd, combined with a smaller image size and fewer steps, it was part of a ~50x wall-clock reduction; for full SD1.5 at its native settings, it was only ~30-35% (see §4c) — because dynamic quantization mainly accelerates matrix multiplies, and SD1.5's UNet, unlike the smaller model's proportionally more attention-heavy design, spends most of its compute in convolutions.

---

## 3. ONNX as the CPU-Inference Interop Layer

**Explanation.** As in the search subsystem (see `search-and-retrieval.md` §6), ONNX lets a model authored in PyTorch be exported once and then executed by ONNX Runtime with no PyTorch dependency at inference time. `optimum` (Hugging Face's hardware/runtime-acceleration library) provides the diffusion-pipeline-aware export (`optimum.exporters.onnx`, handling the multi-sub-model structure of a Stable Diffusion pipeline: text encoder, UNet, VAE encoder, VAE decoder, each exported and quantized independently) and a drop-in `ORTStableDiffusionPipeline` that mirrors `diffusers`' pipeline API but runs every sub-model through ONNX Runtime sessions. At full SD1.5 size, the UNet's exported weights exceed ONNX's 2GB inline-protobuf limit and are written to an external `model.onnx_data` file instead — both the exporter and `quantize_dynamic` handle this transparently once told to (`use_external_data_format=True`), but it's a real difference from the smaller model, whose every sub-model stayed under the limit.

**Citations.**
- Hugging Face. *Optimum ONNX Runtime — Stable Diffusion*. https://huggingface.co/docs/optimum/onnxruntime/usage_guides/models#stable-diffusion
- ONNX Runtime documentation. https://onnxruntime.ai/docs/
- ONNX. *Large model support (>2GB) via external data*. https://onnx.ai/onnx/repo-docs/ExternalData.html

**Used in GlassCart:** this is why the project can honestly say the *repeated* cost of this pipeline (`generate.py`, run every time the catalog changes) needs no PyTorch and no GPU — only the *one-time* export step (`export_onnx.py`) does, and only to trace the model graph. This mirrors the project's existing pattern in the search subsystem of keeping PyTorch out of the default dependency set entirely (`fastembed` wraps ONNX Runtime directly), extended here to a case where the upstream model is only distributed in PyTorch format.

---

## 4. Why the Distilled Model Was Rejected (A Negative Result)

**Explanation.** Before settling on the final pipeline, `segmind/tiny-sd` was tested across a range of resolutions (128×128, 192×192, 256×256) and step counts (4 through 20), on three prompts spanning different catalog categories (headphones, a book, a stand mixer). At 128×128, output was an unrecognizable blob regardless of step count, and *more* steps made it worse (20 steps converged toward an almost-blank frame — see §4a below). At 256×256, output became recognizable as *an* object, but not reliably the *correct* one: inspecting real batch output showed a spiral-bound book rendered as a shiny circular lens, the same generic shape produced for an unrelated headphones prompt. This is documented in detail because it's a genuinely counter-intuitive finding — the natural assumption is that a smaller model just needs more steps or resolution to "catch up," and for this model at this scale, neither fixed the actual problem.

**Citations.** (methodology, not a specific paper)
- Internal benchmark, this repository: raw timing/memory logs and sample images retained during development; summarized in `models/product-images/MODEL_CARD.md`'s "Metrics" section.

**Used in GlassCart:** this negative result is why the pipeline does not use a distilled model at all, despite the large speed advantage one would offer — a fast pipeline that renders the wrong object is not a placeholder-image pipeline, it's a random-shape generator with a product catalog attached.

---

## 4a. Step Count Isn't a Substitute for Resolution (A Second Negative Result, Distilled Model)

**Explanation.** A first pass at the (later-rejected) distilled pipeline used 128×128 images, reasoning that image size and step count trade off fidelity for speed roughly interchangeably. That reasoning was wrong for this model at this size: 128×128 output was an unrecognizable blob at 8-12 steps, and *more* steps did not fix it — 20 steps produced an almost-blank frame, worse than fewer steps. Below some resolution threshold, this model's UNet and VAE decoder don't have the spatial capacity to represent product detail at all; additional denoising iterations just converge more thoroughly toward a flat, low-information image rather than adding detail that was never representable in the first place.

**Citations.**
- Internal benchmark, this repository: same raw logs as §4, covering the 128×128 (8/12/20-step), 192×192 (12-step), and 256×256 (8/15-step) comparisons; summarized in `models/product-images/MODEL_CARD.md`'s "Metrics" table.

**Used in GlassCart:** documented as a caution against the intuitive-but-wrong assumption (which this project itself made, briefly) that step count and resolution are interchangeable dials — for a given model, there can be a hard resolution floor below which no amount of extra compute helps.

---

## 4b. Model Capacity, Not Precision or Resolution, Was the Real Constraint

**Explanation.** The distilled-model failures in §4/§4a could look like a precision or resolution problem, but switching to the full, non-distilled `stable-diffusion-v1-5` — at the same INT8 quantization, and without needing any resolution/step shrinkage — immediately produced correctly-shaped, recognizable output on the exact prompts that failed before (a real stand mixer, real over-ear headphones, a real spiral-bound book). This isolates the variable: it was the model's parameter count/architecture capacity that mattered, not numeric precision (both configurations were INT8) and not resolution (the full model was tested at *larger*, not smaller, resolution and still ran successfully).

**Citations.** (methodology, not a specific paper)
- Internal benchmark, this repository: side-by-side comparison images for the same three prompts (headphones/book/mixer) under tiny-sd and under SD1.5, both INT8-quantized.

**Used in GlassCart:** this is the direct justification for accepting a ~32-hour batch job (§4c) instead of continuing to tune the fast model — no combination of resolution/steps/scheduler tried on the distilled model fixed the category-confusion problem, because it was never a tuning problem.

---

## 4c. Quantization Gains Depend on Where a Model Spends Its Compute

**Explanation.** ONNX Runtime's dynamic quantization primarily accelerates operators like MatMul and Gemm (matrix multiplication) by using faster integer code paths; it does not meaningfully accelerate Conv2d (convolution) in dynamic mode. Small, attention-heavy models get a large speedup from this because a bigger fraction of their compute is matrix multiplication. Stable Diffusion 1.5's UNet is a much more convolution-heavy architecture at its full size, so the same quantization technique that gave the distilled model roughly a 50x combined speedup (with resolution/step reductions) gave the full model only a ~30-35% speedup at unchanged settings.

**Citations.**
- ONNX Runtime. *Quantize ONNX Models — Dynamic Quantization*. https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html#dynamic-quantization
- Ronneberger, O., Fischer, P., & Brox, T. (2015). *U-Net: Convolutional Networks for Biomedical Image Segmentation*. MICCAI 2015. https://arxiv.org/abs/1505.04597 — the convolutional encoder-decoder architecture Stable Diffusion's UNet descends from, for background on why it's Conv-dominated.

**Used in GlassCart:** sets the expectation correctly for anyone tuning this pipeline further — quantizing a bigger model is not a free repeat of the win seen on a smaller one, and squeezing more speed out of `generate.py` would need a different lever (static/QDQ quantization with calibration data, a smaller-but-not-fatally-distilled model, or fewer steps with a carefully chosen fast scheduler — a DPM++/Karras attempt at 15 steps was tried and rejected here for over-abstracting the composition, see `models/product-images/MODEL_CARD.md`'s Metrics table).

---

## 5. Deterministic Generation and Reproducibility

**Explanation.** Diffusion models sample from a Gaussian noise seed; fixing that seed (and every other source of randomness) makes generation fully deterministic — the same prompt and seed reproduce the same image bit-for-bit on the same hardware/software stack. This is a standard, well-documented property of these models' public APIs (`diffusers`' `generator` argument), not something GlassCart had to build.

**Citations.**
- Hugging Face. *Diffusers — Reproducibility*. https://huggingface.co/docs/diffusers/using-diffusers/reproducibility

**Used in GlassCart:** `training/product_images/generate.py` derives each product's seed from `sha256(product_id)`, so regenerating the catalog's images (e.g. after `datasets/products/generate.py` changes) reproduces byte-identical output for any product whose id and prompt didn't change — the same reproducibility bar the project's other artifacts (embeddings, BM25 index) already hold themselves to.

---

## 6. Model Transparency Applied to Generative, Not Just Predictive, Models

**Explanation.** Model cards (see `search-and-retrieval.md` §7) were originally proposed for predictive/classification models, but the same structure — intended use, training data, metrics, limitations, ethical considerations — applies just as well to a generative model, with "metrics" reinterpreted as *operational* benchmarks (speed, memory) rather than accuracy, since there is no ground truth to score generated images against in this synthetic-catalog context.

**Citations.**
- Mitchell, M. et al. (2019). *Model Cards for Model Reporting* (as cited in `search-and-retrieval.md` §7).

**Used in GlassCart:** `models/product-images/MODEL_CARD.md` follows the exact same section headings as `models/search-embeddings/MODEL_CARD.md`, substituting an operational speed/memory table (including the rejected distilled-model configuration, not just the one shipped) for the search model's similarity-score discussion — and, per the project's Glass Mode invariant, the UI discloses the image's AI-generated nature directly on the product card/detail page rather than only in a docs file a user is unlikely to read.
