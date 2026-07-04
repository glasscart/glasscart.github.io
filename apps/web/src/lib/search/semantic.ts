/**
 * Client-side semantic search: embeds the user's query, in their own
 * browser, with the ONNX export of the same model used offline to embed
 * the catalog (see models/search-embeddings/MODEL_CARD.md). No network
 * call is made with the query text itself — only the (cacheable,
 * content-free) model weights are fetched, once, from the Hugging Face Hub.
 *
 * See docs/research/search-and-retrieval.md §2, §3, §5 for why this
 * bi-encoder / transformers.js architecture is what makes client-side
 * semantic search over a whole catalog feasible on a static site.
 */
import { pipeline, env, type FeatureExtractionPipeline } from '@huggingface/transformers'
import { EMBEDDING_MODEL_NAME } from './config'
import { loadProductEmbeddings } from './loadData'

// Never look for model weights on the same origin as the app — always
// fetch from the Hugging Face Hub (and let the browser HTTP cache handle
// repeat visits).
env.allowLocalModels = false

let embedderPromise: Promise<FeatureExtractionPipeline> | null = null

function getEmbedder(): Promise<FeatureExtractionPipeline> {
  if (!embedderPromise) {
    embedderPromise = pipeline('feature-extraction', EMBEDDING_MODEL_NAME) as Promise<FeatureExtractionPipeline>
  }
  return embedderPromise
}

/** Embeds `text` into a mean-pooled, L2-normalized vector. */
export async function embedText(text: string): Promise<Float32Array> {
  const embedder = await getEmbedder()
  const output = await embedder(text, { pooling: 'mean', normalize: true })
  return output.data as Float32Array
}

/**
 * Cosine similarity between the query vector and every product vector.
 * Both sides are already L2-normalized, so this reduces to a dot product.
 */
export async function semanticScores(query: string): Promise<{ ids: string[]; scores: Float64Array; dim: number }> {
  const [queryVector, artifact] = await Promise.all([embedText(query), loadProductEmbeddings()])
  const scores = new Float64Array(artifact.vectors.length)
  for (let i = 0; i < artifact.vectors.length; i++) {
    const vec = artifact.vectors[i]
    let dot = 0
    for (let d = 0; d < vec.length; d++) dot += vec[d] * queryVector[d]
    scores[i] = dot
  }
  return { ids: artifact.ids, scores, dim: artifact.dim }
}
