/**
 * Client-side hybrid search: fuses the pure-TS BM25 index with client-side
 * semantic similarity (transformers.js). This is the browser twin of
 * `services/search/app/hybrid.py` — same formula, same constants, two
 * independent implementations so the optional backend is never required.
 *
 * See docs/research/search-and-retrieval.md §4 for why a weighted linear
 * combination (rather than e.g. reciprocal rank fusion) was chosen: it
 * keeps the per-result score breakdown human-readable for Glass Mode.
 */
import { buildBm25Index, tokenize, type Bm25Index } from './bm25'
import { semanticScores } from './semantic'
import { loadEmbeddingsManifest, loadProducts } from './loadData'
import { BM25_B, BM25_K1, EMBEDDING_MODEL_NAME_OFFLINE, FUSION_ALPHA, LIMITATIONS, WHY_AI_WAS_USED } from './config'
import type { GlassExplanation, Product, SearchOutcome, SearchResultItem } from './types'

let indexPromise: Promise<{ index: Bm25Index; products: Product[] }> | null = null

function getIndex() {
  if (!indexPromise) {
    indexPromise = loadProducts().then((products) => {
      const docs = products.map((p) => tokenize(`${p.title} ${p.description}`))
      return { index: buildBm25Index(docs, BM25_K1, BM25_B), products }
    })
  }
  return indexPromise
}

function minMaxNormalize(values: ArrayLike<number>): Float64Array {
  let lo = Infinity
  let hi = -Infinity
  for (let i = 0; i < values.length; i++) {
    if (values[i] < lo) lo = values[i]
    if (values[i] > hi) hi = values[i]
  }
  const out = new Float64Array(values.length)
  const range = hi - lo
  for (let i = 0; i < values.length; i++) {
    out[i] = range < 1e-9 ? 0 : (values[i] - lo) / range
  }
  return out
}

export async function hybridSearch(query: string, limit = 12, alpha = FUSION_ALPHA): Promise<SearchOutcome> {
  const totalStart = performance.now()

  let t = performance.now()
  const queryTokens = tokenize(query)
  const tokenizeQueryMs = performance.now() - t

  t = performance.now()
  const { index, products } = await getIndex()
  const bm25Raw = index.score(queryTokens)
  const bm25ScoreMs = performance.now() - t

  t = performance.now()
  const { scores: semanticRaw } = await semanticScores(query)
  const embedAndScoreMs = performance.now() - t

  t = performance.now()
  const bm25Norm = minMaxNormalize(bm25Raw)
  const semanticNorm = minMaxNormalize(semanticRaw)
  const fused = new Float64Array(products.length)
  for (let i = 0; i < products.length; i++) {
    fused[i] = alpha * bm25Norm[i] + (1 - alpha) * semanticNorm[i]
  }
  const order = Array.from(fused.keys()).sort((a, b) => fused[b] - fused[a]).slice(0, limit)
  const fusionMs = performance.now() - t

  const results: SearchResultItem[] = order.map((idx, i) => ({
    product: products[idx],
    rank: i + 1,
    score: {
      bm25Raw: bm25Raw[idx],
      bm25Normalized: bm25Norm[idx],
      semanticRawCosine: semanticRaw[idx],
      semanticNormalized: semanticNorm[idx],
      fused: fused[idx],
    },
  }))

  const totalMs = performance.now() - totalStart
  const manifest = await loadEmbeddingsManifest()

  const glass: GlassExplanation = {
    provider: 'client',
    whyAiWasUsed: WHY_AI_WAS_USED,
    bm25K1: BM25_K1,
    bm25B: BM25_B,
    fusionAlpha: alpha,
    embeddingModel: EMBEDDING_MODEL_NAME_OFFLINE,
    embeddingDim: manifest?.dim ?? 384,
    embeddingSource: 'catalog vectors: precomputed offline artifact; query vector: embedded live in your browser via transformers.js (WebAssembly), never sent to a server',
    corpusSize: products.length,
    artifactGeneratedAt: manifest?.generated_at ?? null,
    timing: {
      tokenizeQueryMs,
      bm25ScoreMs,
      embedQueryMs: embedAndScoreMs,
      semanticScoreMs: 0,
      fusionMs,
      totalMs,
    },
    limitations: LIMITATIONS,
  }

  return { query, results, glass }
}
