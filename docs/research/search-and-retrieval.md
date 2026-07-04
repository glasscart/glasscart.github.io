# Research Notes: Hybrid Search & Retrieval

> Bibliography and design rationale for GlassCart's first vertical slice: **hybrid product
> search**, combining a pure-TypeScript BM25 keyword ranker running in the browser with
> client-side semantic search over sentence embeddings (`all-MiniLM-L6-v2`, precomputed offline
> with `fastembed` and queried live via `transformers.js`), fused into a single transparent
> score under "Glass Mode". This document exists so that every parameter choice, model choice,
> and transparency-metadata field in the implementation can be traced back to a primary source.

---

## 1. BM25 / The Probabilistic Relevance Framework

**Explanation.** BM25 ("Best Match 25") is the term-weighting and document-scoring function that grew out of the probabilistic relevance model developed at City University London (the "Okapi" system) through the late 1980s and 1990s. It scores a document against a query by summing, over each query term, a saturating function of term frequency (controlled by `k1`) normalized by document length relative to the average document length in the collection (controlled by `b`), multiplied by an inverse-document-frequency weight. It remains the strongest simple, unsupervised sparse-retrieval baseline in IR — hard to beat without learned re-ranking, and cheap enough to run entirely client-side with no index server.

**Citations.**
- Robertson, S. E., & Zaragoza, H. (2009). *The Probabilistic Relevance Framework: BM25 and Beyond*. Foundations and Trends in Information Retrieval, 3(4), 333–389. https://doi.org/10.1561/1500000019
- Robertson, S. E., Walker, S., Jones, S., Hancock-Beaulieu, M. M., & Gatford, M. (1995). *Okapi at TREC-3*. In Proceedings of the Third Text REtrieval Conference (TREC-3), NIST Special Publication 500-225. https://trec.nist.gov/pubs/trec3/t3_proceedings.html
- Robertson, S. E., & Walker, S. (1994). *Some Simple Effective Approximations to the 2-Poisson Model for Probabilistic Weighted Retrieval*. In Proceedings of SIGIR '94, 232–241. https://doi.org/10.1007/978-1-4471-2099-5_24

**Used in GlassCart:** This is the direct source for the pure-TypeScript BM25 implementation that runs in the browser (no server round-trip, consistent with the static-site constraint). The `k1` (term-frequency saturation, typically tuned in `[1.2, 2.0]`) and `b` (length-normalization strength, typically `0.75`) parameters named in Robertson & Zaragoza (2009), §4, are surfaced verbatim as the "BM25 params" shown in Glass Mode's per-result score breakdown, so a user (or reviewer) can see exactly which formula and coefficients produced the keyword-relevance component of the fused score, rather than treating "keyword match" as a black box.

---

## 2. Sentence Embeddings for Semantic Search

**Explanation.** Prior to Sentence-BERT, getting a single fixed-length vector for a sentence out of BERT-style models required either the (poor-quality) `[CLS]` token embedding or averaging token embeddings, and comparing two sentences meant an expensive cross-encoder forward pass over the *pair*. Reimers & Gurevych's Sentence-BERT (SBERT) fine-tunes BERT/RoBERTa with siamese and triplet network structures so that cosine similarity between independently-computed sentence embeddings is meaningful, cutting the cost of finding the most similar pair among 10,000 sentences from ~65 hours (BERT cross-encoder) to ~5 seconds — and, crucially, allows embeddings to be precomputed once and compared to a query embedding with a single dot product at query time.

**Citation.**
- Reimers, N., & Gurevych, I. (2019). *Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks*. In Proceedings of EMNLP-IJCNLP 2019, 3982–3992. https://doi.org/10.18653/v1/D19-1410 (arXiv: https://arxiv.org/abs/1908.10084)

**Used in GlassCart:** This is the architectural basis for the entire semantic-search half of the hybrid pipeline. Product catalog embeddings are computed *once, offline*, in Python (`fastembed`) and stored alongside the catalog; a query embedding is computed *once, live*, in the browser (`transformers.js`); relevance is then just cosine/dot-product similarity between the two — exactly the bi-encoder pattern SBERT introduced, and the only pattern that makes client-side semantic search over a whole catalog computationally feasible (a cross-encoder would require one forward pass per product per query).

---

## 3. `all-MiniLM-L6-v2`: model choice rationale

**Explanation.** `all-MiniLM-L6-v2` is a sentence-embedding model distilled down to 6 transformer layers with a 384-dimensional output space, trained by the `sentence-transformers` project on over 1 billion sentence pairs using a contrastive objective. It descends from Microsoft's MiniLM line of general-purpose small transformers, which uses deep self-attention distillation to compress a large teacher model into a much smaller student while retaining most of its task performance. The combination — 6 layers, 384 dims, ~22M parameters, ~90 MB in fp32 (and much smaller quantized) — makes it one of the best speed/quality tradeoffs among open sentence encoders: it is roughly 5x smaller and faster than `all-mpnet-base-v2` while retaining strong performance on the Massive Text Embedding Benchmark (MTEB) sentence-similarity and retrieval tasks, and it is small enough to run inference in-browser via WebAssembly/WebGPU in well under a second.

**Citations.**
- Wang, W., Wei, F., Dong, L., Bao, H., Yang, N., & Zhou, M. (2020). *MiniLM: Deep Self-Attention Distillation for Task-Agnostic Compression of Pre-Trained Transformers*. In Advances in Neural Information Processing Systems (NeurIPS) 33. https://arxiv.org/abs/2002.10957
- Reimers, N., & Gurevych, I. (2019). *Sentence-BERT* (as above) — the training framework `all-MiniLM-L6-v2` is trained under.
- Sentence-Transformers model card: `sentence-transformers/all-MiniLM-L6-v2`. https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- ONNX port used client-side: `Xenova/all-MiniLM-L6-v2`. https://huggingface.co/Xenova/all-MiniLM-L6-v2

**Used in GlassCart:** This is the exact model named in the brief — used twice, in two different runtimes, on purpose: (1) offline in Python via `fastembed` (which itself wraps ONNX Runtime, no PyTorch dependency) to precompute one embedding per product in the catalog at build time, and (2) live in-browser via `transformers.js`'s `Xenova/all-MiniLM-L6-v2` ONNX export to embed the user's query on every keystroke/search. Using the *same* base model/weights (modulo export format) on both ends is what keeps the two embedding spaces comparable — a different model on either side would silently break cosine-similarity ranking. The 384-dim output also directly sizes the stored catalog-embedding matrix that ships as a static asset with the site.

---

## 4. Hybrid Search: Sparse + Dense Fusion

**Explanation.** Neither BM25 nor dense embeddings dominate the other: BM25 wins on exact keyword/SKU/brand-name matches and out-of-domain queries; dense embeddings win on paraphrase, synonymy, and conceptual/"vibe" queries the catalog's own vocabulary never uses. Production search systems increasingly combine both rather than picking one. The two dominant fusion strategies are (a) **linear/weighted score combination** — normalize each signal (e.g., min-max or z-score) and combine as `score = α · normalize(BM25) + (1-α) · normalize(cosine_sim)` — and (b) **Reciprocal Rank Fusion (RRF)**, which combines *ranks* rather than raw scores (`score = Σ 1/(k + rank_i)`), avoiding the need to make incomparable score distributions commensurable at all.

**Citations.**
- Cormack, G. V., Clarke, C. L. A., & Buettcher, S. (2009). *Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods*. In Proceedings of SIGIR '09, 758–759. https://doi.org/10.1145/1571941.1572114
- Pinecone. *Hybrid Search Explained*. Pinecone Learning Center. https://www.pinecone.io/learn/hybrid-search-intro/
- Elastic. *The Practical Effect of BM25 and Semantic (Hybrid) Ranking with RRF*, and Elastic's reciprocal rank fusion documentation. Elasticsearch Guide — Reciprocal rank fusion. https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html
- Weaviate. *Hybrid Search Explained*. Weaviate Blog. https://weaviate.io/blog/hybrid-search-explained

**Used in GlassCart:** GlassCart deliberately uses the simpler **weighted linear fusion** approach (α-weighted combination of normalized BM25 and cosine-similarity scores) rather than RRF, precisely *because* Glass Mode's transparency requirement makes a per-result score **breakdown** a first-class UI element — a user should be able to see "BM25 contributed X, semantic similarity contributed Y, combined with weight α" for each result, which is a natural, human-readable consequence of linear score combination but is much harder to explain intuitively under rank-based fusion (RRF scores have no direct interpretation as "how relevant"). The fusion weight α, along with the BM25 `k1`/`b` params (§1), is exposed as an explicit, inspectable constant in Glass Mode rather than hidden inside a ranking service — directly following the production hybrid-search patterns documented by Pinecone/Weaviate/Elastic, adapted for full-stack transparency instead of opacity.

---

## 5. transformers.js and Client-Side Transformer Inference

**Explanation.** `transformers.js` (by Xenova, now maintained under the Hugging Face organization) is a JavaScript port of the Python `transformers` library's pipeline API, built on top of ONNX Runtime Web. It lets a browser download a quantized ONNX export of a Hugging Face model and run inference locally via WebAssembly (with optional WebGPU acceleration), with no Python runtime, no server, and no network call after the model is cached — matching Hugging Face models 1:1 in API shape (`pipeline('feature-extraction', ...)`, etc.) so that porting an offline pipeline to the browser requires minimal code change.

**Citations.**
- Hugging Face. *Transformers.js documentation*. https://huggingface.co/docs/transformers.js
- Hugging Face. *Transformers.js v3: WebGPU Support, New Models & Tasks, and More* — the release blog documenting the package's move from the community `@xenova/transformers` package to the official `huggingface/transformers.js` org/package. https://huggingface.co/blog/transformersjs-v3
- `huggingface/transformers.js` GitHub repository (originally `Xenova/transformers.js`), *"Run 🤗 Transformers directly in your browser, with no need for a server!"* https://github.com/huggingface/transformers.js

**Used in GlassCart:** This is the library that computes the live query embedding in the browser at search time (`Xenova/all-MiniLM-L6-v2`, §3) — the component that makes semantic search possible on a static, serverless deployment. Because `transformers.js` downloads and caches the ONNX model client-side (typically via the browser cache / IndexedDB after first load), the model weights become just another static asset served by GitHub Pages (§8), rather than a live inference endpoint GlassCart would otherwise have to host and pay for. Model load latency and device (WASM vs. WebGPU) are exactly the kind of runtime facts Glass Mode surfaces in its "latency" and "architecture" transparency fields for the semantic-search component.

---

## 6. ONNX and ONNX Runtime

**Explanation.** ONNX (Open Neural Network Exchange) is an open, framework-agnostic format for representing trained ML models as a computation graph, letting a model trained in one framework (e.g., PyTorch, used to originally train `all-MiniLM-L6-v2`) be exported once and then executed by any ONNX-compliant runtime, on any target (server, mobile, browser), without carrying the original training framework as a runtime dependency. ONNX Runtime is Microsoft's cross-platform inference engine for ONNX graphs, with builds targeting CPU, GPU, mobile, and — via `onnxruntime-web` — WebAssembly/WebGPU in-browser execution.

**Citations.**
- ONNX. *Open Neural Network Exchange* — official site and format specification. https://onnx.ai/
- ONNX Runtime documentation. https://onnxruntime.ai/docs/
- ONNX Runtime Web documentation (in-browser inference via WebAssembly/WebGPU). https://onnxruntime.ai/docs/tutorials/web/

**Used in GlassCart:** ONNX is the load-bearing interoperability layer of the whole semantic pipeline: `fastembed` runs `sentence-transformers/all-MiniLM-L6-v2` **offline in Python without PyTorch**, specifically because `fastembed` is built on ONNX Runtime rather than the native `sentence-transformers`/PyTorch stack — cutting the offline embedding-generation dependency footprint and matching the artifact format (`Xenova/all-MiniLM-L6-v2` ONNX export) that `transformers.js` needs to run the *same* model in-browser via `onnxruntime-web`. Without ONNX as a shared format, the offline (Python) and online (browser) halves of the embedding pipeline could not use verifiably-the-same model weights.

---

## 7. Model Transparency: Model Cards & Datasheets

**Explanation.** Model Cards, proposed by Mitchell et al., are short structured documents shipped alongside a trained model that report its intended use, evaluation metrics broken out across relevant population/use-case slices, ethical considerations, and known limitations, analogous to datasheets accompanying electronic components. Datasheets for Datasets, proposed by Gebru et al., apply the same idea one step upstream, asking dataset creators to document motivation, composition, collection process, recommended uses, and — importantly — the dataset's own limitations and distributional biases, so downstream model builders can reason about what a dataset does and does not represent before training on it.

**Citations.**
- Mitchell, M., Wu, S., Zaldivar, A., Barnes, E., Vasserman, L., Hutchinson, B., Spitzer, E., Raji, I. D., & Gebru, T. (2019). *Model Cards for Model Reporting*. In Proceedings of the Conference on Fairness, Accountability, and Transparency (FAT* '19), 220–229. https://doi.org/10.1145/3287560.3287596 (arXiv: https://arxiv.org/abs/1810.03993)
- Gebru, T., Morgenstern, J., Vecchione, B., Vaughan, J. W., Wallach, H., Daumé III, H., & Crawford, K. (2021). *Datasheets for Datasets*. Communications of the ACM, 64(12), 86–92. https://doi.org/10.1145/3458723 (arXiv: https://arxiv.org/abs/1803.09010)

**Used in GlassCart:** These two papers are the direct academic basis for "Glass Mode" as a product concept. GlassCart's per-feature **model cards** (model version, architecture, training data, metrics, confidence, latency, feature importance, limitations, and ethical/privacy considerations) are structured as a UI-native rendering of Mitchell et al.'s recommended model card sections (model details, intended use, factors, metrics, ethical considerations, caveats and recommendations), applied here to the hybrid search feature specifically: e.g., the `all-MiniLM-L6-v2` semantic component's card documents its training data provenance and known limitations (e.g., 256-token truncation, English-centric training data, general-purpose rather than e-commerce-domain fine-tuning), while the catalog itself — and any synthetic product data used to train/evaluate the search feature — should get an accompanying **dataset card** following Gebru et al.'s datasheet questionnaire (motivation, composition, collection, preprocessing, distribution, maintenance).

---

## 8. Static-First / Offline-First Architecture and GitHub Pages Constraints

**Explanation.** GitHub Pages serves purely static files (HTML/CSS/JS/binary assets) with no server-side code execution, no databases, and published size/traffic limits (recommended repository size under 1 GB, published site under 1 GB, and soft bandwidth/build-frequency limits) — meaning any feature that would normally rely on a backend (an index server, a model inference endpoint, an API) must be re-architected to run entirely client-side or be precomputed at build time and shipped as a static asset.

**Citations.**
- GitHub Docs. *About GitHub Pages*. https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages
- GitHub Docs. *GitHub Pages limits* (source repo/published-site size capped at 1 GB, ~100 GB/month soft bandwidth limit, ~10 builds/hour soft limit, 10-minute build timeout). https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits

**Used in GlassCart:** This constraint is *the* reason the whole feature is architected the way it is: BM25 must run in pure TypeScript in the browser (no search server); embeddings must be *precomputed offline* in Python and shipped as a static JSON/binary asset rather than served from a vector database; and query-time semantic embedding must run client-side via `transformers.js`/ONNX Runtime Web rather than calling a hosted inference API. Every "why is this running in the browser instead of a server" design decision in this slice traces back to the static-hosting constraint documented here.

---

## Further Reading

- Karpukhin, V., Oğuz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D., & Yih, W. (2020). *Dense Passage Retrieval for Open-Domain Question Answering*. EMNLP 2020. https://arxiv.org/abs/2004.04906 — foundational dense-retrieval (bi-encoder) paper, background for why dense retrieval is a credible complement to BM25 beyond sentence similarity specifically.
- Thakur, N., Reimers, N., Rücklé, A., Srivastava, A., & Gurevych, I. (2021). *BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of Information Retrieval Models*. NeurIPS 2021 Datasets and Benchmarks Track. https://arxiv.org/abs/2104.08663 — benchmark suite showing BM25 remains a strong zero-shot baseline relative to many neural retrievers, motivating hybrid rather than dense-only retrieval.
- Muennighoff, N., Tazi, N., Magne, L., & Reimers, N. (2023). *MTEB: Massive Text Embedding Benchmark*. In Proceedings of EACL 2023. https://arxiv.org/abs/2210.07316 — the benchmark `all-MiniLM-L6-v2`'s quality/speed tradeoff is generally reported against.
- Hugging Face. *Sentence Transformers documentation* (the library used by `fastembed`'s underlying model family and training methodology). https://www.sbert.net/
- Qdrant. *Hybrid Search Revamped — Building with Qdrant's Query API*. Qdrant Blog/Docs on combining sparse and dense vectors. https://qdrant.tech/articles/hybrid-search/
- MDN Web Docs. *WebAssembly* — background on the browser execution target ONNX Runtime Web and transformers.js compile to. https://developer.mozilla.org/en-US/docs/WebAssembly
