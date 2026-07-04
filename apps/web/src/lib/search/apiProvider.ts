/**
 * Optional server-backed search provider — talks to the reference FastAPI
 * service in `services/search`. Only used if `VITE_SEARCH_API_URL` is set;
 * the site works fully without it (see `provider.ts`).
 */
import type { GlassExplanation, Product, SearchOutcome, SearchProvider } from './types'

interface ApiScoreBreakdown {
  bm25_raw: number
  bm25_normalized: number
  semantic_raw_cosine: number
  semantic_normalized: number
  fused: number
}

interface ApiResultItem extends Product {
  rank: number
  score: ApiScoreBreakdown
}

interface ApiResponse {
  query: string
  results: ApiResultItem[]
  glass: {
    why_ai_was_used: string
    bm25_k1: number
    bm25_b: number
    fusion_alpha: number
    embedding_model: string
    embedding_dim: number
    embedding_source: string
    corpus_size: number
    artifact_generated_at: string | null
    timing: {
      tokenize_query_ms: number
      bm25_score_ms: number
      embed_query_ms: number
      semantic_score_ms: number
      fusion_ms: number
      total_ms: number
    }
    limitations: string[]
  }
}

export function createApiSearchProvider(baseUrl: string): SearchProvider {
  return {
    name: 'api',
    async search(query, opts) {
      const url = new URL('/search', baseUrl)
      url.searchParams.set('q', query)
      if (opts?.limit) url.searchParams.set('limit', String(opts.limit))
      if (opts?.alpha !== undefined) url.searchParams.set('alpha', String(opts.alpha))

      const res = await fetch(url.toString())
      if (!res.ok) throw new Error(`Search API error: ${res.status}`)
      const data: ApiResponse = await res.json()

      const glass: GlassExplanation = {
        provider: 'api',
        whyAiWasUsed: data.glass.why_ai_was_used,
        bm25K1: data.glass.bm25_k1,
        bm25B: data.glass.bm25_b,
        fusionAlpha: data.glass.fusion_alpha,
        embeddingModel: data.glass.embedding_model,
        embeddingDim: data.glass.embedding_dim,
        embeddingSource: data.glass.embedding_source,
        corpusSize: data.glass.corpus_size,
        artifactGeneratedAt: data.glass.artifact_generated_at,
        timing: {
          tokenizeQueryMs: data.glass.timing.tokenize_query_ms,
          bm25ScoreMs: data.glass.timing.bm25_score_ms,
          embedQueryMs: data.glass.timing.embed_query_ms,
          semanticScoreMs: data.glass.timing.semantic_score_ms,
          fusionMs: data.glass.timing.fusion_ms,
          totalMs: data.glass.timing.total_ms,
        },
        limitations: data.glass.limitations,
      }

      const outcome: SearchOutcome = {
        query: data.query,
        results: data.results.map((r) => ({
          product: r,
          rank: r.rank,
          score: {
            bm25Raw: r.score.bm25_raw,
            bm25Normalized: r.score.bm25_normalized,
            semanticRawCosine: r.score.semantic_raw_cosine,
            semanticNormalized: r.score.semantic_normalized,
            fused: r.score.fused,
          },
        })),
        glass,
      }
      return outcome
    },
  }
}
