import { useQuery } from '@tanstack/react-query'
import { getSimilarProducts } from '../lib/recommendations/similar'
import { useGlassMode } from '../store/glassMode'
import { ProductCard } from './ProductCard'
import { GlassRecommendationPanel } from './GlassRecommendationPanel'

export function RecommendedProducts({ productId }: { productId: string }) {
  const glassMode = useGlassMode((s) => s.enabled)
  const { data } = useQuery({
    queryKey: ['similar-products', productId],
    queryFn: () => getSimilarProducts(productId, 4),
  })

  if (!data || data.results.length === 0) return null

  return (
    <section className="mx-auto max-w-5xl px-4 pb-16">
      <h2 className="mb-4 text-lg font-semibold">You might also like</h2>

      {glassMode && <GlassRecommendationPanel glass={data.glass} />}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {data.results.map((r) => (
          <div key={r.product.id}>
            <ProductCard product={r.product} />
            {glassMode && (
              <p className="mt-1.5 text-center text-[11px] font-medium text-glass-600 dark:text-glass-300">
                {(r.score * 100).toFixed(0)}% similar
              </p>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
