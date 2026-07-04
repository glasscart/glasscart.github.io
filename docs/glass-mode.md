# Glass Mode

Glass Mode is GlassCart's single defining feature: a global toggle that turns every AI-assisted UI element from "just a result" into "a result plus its full diagnostic trail."

## Why it exists

Academic and industry work on AI transparency converges on a few recurring ideas: that models should ship with structured disclosure documents ([Model Cards for Model Reporting](research/search-and-retrieval.md#7-model-transparency-model-cards-datasheets), Mitchell et al., 2019), that datasets need the same treatment ([Datasheets for Datasets](research/search-and-retrieval.md#7-model-transparency-model-cards-datasheets), Gebru et al.), and that this information is most useful when it is available *at the point of decision*, not buried in a separate wiki page nobody reads. Glass Mode is that idea applied directly to the UI: the model card's content, live, next to the result it describes.

## What every AI-assisted feature must expose

Per the project's core specification, when Glass Mode is on, every AI-assisted decision should surface:

| Field | Example (search) |
|---|---|
| Why AI was used | "Keyword matching alone misses paraphrases; hybrid search covers both." |
| Model name, version, architecture | `sentence-transformers/all-MiniLM-L6-v2`, 6-layer MiniLM, 384-dim |
| Training dataset + version | Base model's public training corpus (not GlassCart-specific — see the [model card](https://github.com/glasscart/glasscart.github.io/blob/main/models/search-embeddings/MODEL_CARD.md)) |
| Evaluation metrics | Deliberately *not* a single leaderboard number for this feature — see the model card's rationale |
| Confidence / uncertainty | Raw similarity/BM25 scores shown, not a fabricated "confidence %" |
| Latency | Per-phase breakdown: tokenize, BM25 score, embed, fuse |
| Inference pipeline | Client-side (transformers.js/WASM) vs. optional server-side (FastAPI) |
| Feature importance / explanation | Per-result BM25 vs. semantic score contribution |
| Limitations & known failure cases | e.g. English-only model, synthetic catalog, static index |
| Ethical & privacy considerations | e.g. query text never leaves the browser in the default client-side path |
| Reproducibility instructions | Exact commands to regenerate every artifact |

Not every field is meaningful for every feature (a rule-based system has no "training dataset"), but the goal is to answer "why did I see this?" as completely as the underlying system allows — including honestly saying "this part is deterministic, not AI" when that's true. See [dataviz and glass-mode UI conventions](https://github.com/glasscart/glasscart.github.io/blob/main/apps/web/src/components/GlassSummaryPanel.tsx) for how this is currently rendered.

## What "simulated" means, and why we avoid it where we can

Some AI-commerce features (e.g. large-scale demand forecasting, fraud graphs) are genuinely hard to run for real inside an educational, offline-first, GitHub-Pages-deployable project. GlassCart's policy is:

1. **Prefer a real, working implementation** — even a small or lightweight one — over a fake one. The search subsystem is real end-to-end: real BM25, real sentence embeddings, real ONNX inference, running in an actual browser.
2. **When a real implementation genuinely isn't practical**, the UI and docs must say so explicitly — labeled as a simulation, not presented as if it were live inference — and point to a real-world reference implementation or paper so a learner can see what the production version would look like.
3. **Never quietly fake it.** A hard-coded score dressed up as a "model output" is the exact failure mode Glass Mode exists to prevent.

## Implementation today

The only feature Glass Mode currently instruments is [hybrid product search](subsystems/search.md). The toggle itself is a small persisted Zustand store (`apps/web/src/store/glassMode.ts`); each AI-assisted component reads it and conditionally renders its diagnostics rather than maintaining two separate code paths. As more subsystems (recommendations, pricing, etc.) are built, each is expected to plug into the same store and the same `GlassExplanation`-shaped contract established by search — see `apps/web/src/lib/search/types.ts` for the current shape.
