/**
 * Client-side "similar products" recommender: cosine similarity over the
 * exact same catalog embeddings the search subsystem already computed
 * offline (see models/search-embeddings/MODEL_CARD.md). There is no
 * separate recommendation model and no new training step — this is a
 * deliberately simple, fully-explainable content-based recommender.
 *
 * Collaborative filtering (recommend based on what similar *users* liked)
 * isn't possible yet: GlassCart has no click/purchase history to learn
 * from. Content-based similarity over product text embeddings is the
 * right starting point for that reason, not just a simpler default — see
 * docs/research/recommendations.md.
 */
import { loadEmbeddingsManifest, loadProductEmbeddings, loadProducts } from '../search/loadData'
import type { Product } from '../search/types'

export interface SimilarProduct {
  product: Product
  score: number
}

export interface RecommendationExplanation {
  provider: 'client'
  whyAiWasUsed: string
  method: string
  embeddingModel: string
  embeddingDim: number
  corpusSize: number
  artifactGeneratedAt: string | null
  timingMs: number
  limitations: string[]
}

export interface RecommendationOutcome {
  productId: string
  results: SimilarProduct[]
  glass: RecommendationExplanation
}

const WHY_AI_WAS_USED =
  "Products are ranked by embedding similarity, not manually curated or randomly chosen — the same semantic vectors that power search stand in for \"how alike two products are\" here."

const LIMITATIONS = [
  'Content-based only: similarity is based on title/description text, not on what other shoppers actually bought or viewed together — GlassCart has no interaction data yet.',
  'Reuses the search embedding model as-is; it was never tuned for "these two products pair well" the way a real recommender would be.',
  'Static: recommendations for a product only change when the catalog is regenerated and embeddings are rebuilt.',
]

let corpusPromise: Promise<{ ids: string[]; vectors: number[][]; productById: Map<string, Product> }> | null = null

function getCorpus() {
  if (!corpusPromise) {
    corpusPromise = Promise.all([loadProducts(), loadProductEmbeddings()]).then(([products, artifact]) => ({
      ids: artifact.ids,
      vectors: artifact.vectors,
      productById: new Map(products.map((p) => [p.id, p])),
    }))
  }
  return corpusPromise
}

/**
 * Top-`limit` most similar products to `productId` by cosine similarity
 * (a plain dot product, since catalog vectors are already L2-normalized).
 */
export async function getSimilarProducts(productId: string, limit = 4): Promise<RecommendationOutcome> {
  const t0 = performance.now()
  const [{ ids, vectors, productById }, manifest] = await Promise.all([getCorpus(), loadEmbeddingsManifest()])

  const glassBase = {
    provider: 'client' as const,
    whyAiWasUsed: WHY_AI_WAS_USED,
    method: 'cosine similarity (dot product of L2-normalized vectors) over precomputed catalog embeddings',
    embeddingModel: manifest?.model ?? 'sentence-transformers/all-MiniLM-L6-v2',
    embeddingDim: manifest?.dim ?? (vectors[0]?.length ?? 0),
    corpusSize: productById.size,
    artifactGeneratedAt: manifest?.generated_at ?? null,
    limitations: LIMITATIONS,
  }

  const targetIdx = ids.indexOf(productId)
  if (targetIdx === -1) {
    return { productId, results: [], glass: { ...glassBase, timingMs: performance.now() - t0 } }
  }

  const target = vectors[targetIdx]
  const scored: SimilarProduct[] = []
  for (let i = 0; i < vectors.length; i++) {
    if (i === targetIdx) continue
    const product = productById.get(ids[i])
    if (!product) continue
    const vec = vectors[i]
    let dot = 0
    for (let d = 0; d < vec.length; d++) dot += vec[d] * target[d]
    scored.push({ product, score: dot })
  }
  scored.sort((a, b) => b.score - a.score)

  return {
    productId,
    results: scored.slice(0, limit),
    glass: { ...glassBase, timingMs: performance.now() - t0 },
  }
}
