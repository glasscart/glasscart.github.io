export interface Product {
  id: string
  title: string
  description: string
  category: string
  brand: string
  seller_id: string
  price: number
  currency: string
  rating: number
  rating_count: number
  tags: string[]
  material: string
  created_at: string
}

export interface ScoreBreakdown {
  bm25Raw: number
  bm25Normalized: number
  semanticRawCosine: number
  semanticNormalized: number
  fused: number
}

export interface SearchResultItem {
  product: Product
  rank: number
  score: ScoreBreakdown
}

export interface GlassTiming {
  tokenizeQueryMs: number
  bm25ScoreMs: number
  embedQueryMs: number
  semanticScoreMs: number
  fusionMs: number
  totalMs: number
}

export interface GlassExplanation {
  provider: 'client' | 'api'
  whyAiWasUsed: string
  bm25K1: number
  bm25B: number
  fusionAlpha: number
  embeddingModel: string
  embeddingDim: number
  embeddingSource: string
  corpusSize: number
  artifactGeneratedAt: string | null
  timing: GlassTiming
  limitations: string[]
}

export interface SearchOutcome {
  query: string
  results: SearchResultItem[]
  glass: GlassExplanation
}

export interface SearchProvider {
  name: 'client' | 'api'
  search(query: string, opts?: { limit?: number; alpha?: number }): Promise<SearchOutcome>
}
