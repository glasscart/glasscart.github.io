import type { Product } from './types'

export interface EmbeddingsArtifact {
  model: string
  dim: number
  ids: string[]
  vectors: number[][]
}

export interface EmbeddingsManifest {
  model: string
  browser_model: string
  dim: number
  num_products: number
  generated_at: string
  build_duration_seconds: number
  runtime: Record<string, string>
  dataset_seed: number
}

let productsPromise: Promise<Product[]> | null = null
let embeddingsPromise: Promise<EmbeddingsArtifact> | null = null
let manifestPromise: Promise<EmbeddingsManifest | null> | null = null

const dataUrl = (path: string) => `${import.meta.env.BASE_URL}data/${path}`

export function loadProducts(): Promise<Product[]> {
  if (!productsPromise) {
    productsPromise = fetch(dataUrl('products.json')).then((r) => {
      if (!r.ok) throw new Error(`Failed to load products.json: ${r.status}`)
      return r.json()
    })
  }
  return productsPromise
}

export function loadProductEmbeddings(): Promise<EmbeddingsArtifact> {
  if (!embeddingsPromise) {
    embeddingsPromise = fetch(dataUrl('product_embeddings.json')).then((r) => {
      if (!r.ok) throw new Error(`Failed to load product_embeddings.json: ${r.status}`)
      return r.json()
    })
  }
  return embeddingsPromise
}

export function loadEmbeddingsManifest(): Promise<EmbeddingsManifest | null> {
  if (!manifestPromise) {
    manifestPromise = fetch(dataUrl('manifest.json'))
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null)
  }
  return manifestPromise
}
