import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getSimilarProducts } from '../lib/recommendations/similar'
import { rerank, RECOMMENDATION_RANKING_WEIGHTS } from '../lib/ranking/rerank'
import { useGlassMode } from '../store/glassMode'
import { ProductCard } from './ProductCard'
import { GlassRecommendationPanel } from './GlassRecommendationPanel'
import { GlassRankingPanel } from './GlassRankingPanel'

const RESULT_LIMIT = 4
// Fetch a wider similarity pool than we display so diversification (see
// lib/ranking/rerank.ts) has real alternatives to promote instead of just
// reshuffling four near-duplicate variants of the same base product.
const CANDIDATE_POOL_SIZE = 12

export function RecommendedProducts({ productId }: { productId: string }) {
  const glassMode = useGlassMode((s) => s.enabled)
  const { data } = useQuery({
    queryKey: ['similar-products', productId],
    queryFn: () => getSimilarProducts(productId, CANDIDATE_POOL_SIZE),
  })

  const ranking = useMemo(() => {
    if (!data) return null
    const candidates = data.results.map((r) => ({ product: r.product, baseScore: r.score }))
    return rerank(candidates, RESULT_LIMIT, RECOMMENDATION_RANKING_WEIGHTS)
  }, [data])

  if (!data || data.results.length === 0 || !ranking) return null

  return (
    <section className="mx-auto max-w-5xl px-4 pb-16">
      <h2 className="mb-4 text-lg font-semibold">You might also like</h2>

      {glassMode && <GlassRecommendationPanel glass={data.glass} />}
      {glassMode && <GlassRankingPanel glass={ranking.glass} />}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {ranking.items.map((ranked) => (
          <div key={ranked.product.id}>
            <ProductCard product={ranked.product} />
            {glassMode && (
              <p className="mt-1.5 text-center text-[11px] font-medium text-glass-600 dark:text-glass-300">
                {(ranked.baseScore * 100).toFixed(0)}% similar
                {ranked.diversityPenalty > 0 && ` (diversified, −${ranked.diversityPenalty.toFixed(2)})`}
              </p>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
