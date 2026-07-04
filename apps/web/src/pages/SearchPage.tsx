import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { SearchBar } from '../components/SearchBar'
import { ProductCard } from '../components/ProductCard'
import { GlassSummaryPanel } from '../components/GlassSummaryPanel'
import { GlassRankingPanel } from '../components/GlassRankingPanel'
import { useGlassMode } from '../store/glassMode'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { getSearchProvider } from '../lib/search/provider'
import { FUSION_ALPHA } from '../lib/search/config'
import { rerank, SEARCH_RANKING_WEIGHTS } from '../lib/ranking/rerank'

const DEFAULT_QUERY = 'cozy running gear'
const RESULT_LIMIT = 12
// Fetch a wider candidate pool than we display so re-ranking (especially
// diversification) has real alternatives to promote, not just a reshuffle
// of a pool that was already truncated to near-duplicates.
const CANDIDATE_POOL_SIZE = 30

export function SearchPage() {
  const [searchParams] = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') || DEFAULT_QUERY)
  const debouncedQuery = useDebouncedValue(query, 250)
  const glassMode = useGlassMode((s) => s.enabled)
  const provider = useMemo(() => getSearchProvider(), [])

  const { data, isFetching, isError, error } = useQuery({
    queryKey: ['search', provider.name, debouncedQuery],
    queryFn: () => provider.search(debouncedQuery, { limit: CANDIDATE_POOL_SIZE, alpha: FUSION_ALPHA }),
    enabled: debouncedQuery.trim().length > 0,
    placeholderData: keepPreviousData,
  })

  const ranking = useMemo(() => {
    if (!data) return null
    const candidates = data.results.map((item) => ({ product: item.product, baseScore: item.score.fused }))
    return rerank(candidates, RESULT_LIMIT, SEARCH_RANKING_WEIGHTS)
  }, [data])

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-5 text-2xl font-semibold">Shop all products</h1>

      <div className="mb-6">
        <SearchBar value={query} onChange={setQuery} isLoading={isFetching} />
      </div>

      {isError && (
        <p className="mb-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          Search failed: {(error as Error).message}
        </p>
      )}

      {glassMode && data && <GlassSummaryPanel glass={data.glass} />}
      {glassMode && ranking && <GlassRankingPanel glass={ranking.glass} />}

      {data && data.results.length === 0 && (
        <p className="text-sm text-slate-500">No products matched “{data.query}”.</p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {ranking?.items.map((ranked, i) => {
          const original = data?.results.find((r) => r.product.id === ranked.product.id)
          return (
            <div key={ranked.product.id}>
              <ProductCard
                product={ranked.product}
                rank={i + 1}
                score={original?.score}
                alpha={data?.glass.fusionAlpha}
              />
              {glassMode && (
                <p className="mt-1.5 text-center font-mono text-[11px] text-glass-600 dark:text-glass-300">
                  base {ranked.baseScore.toFixed(2)} + rating {ranked.ratingBoost.toFixed(2)} + pop{' '}
                  {ranked.popularityBoost.toFixed(2)} − div {ranked.diversityPenalty.toFixed(2)} ={' '}
                  {(ranked.finalScore - ranked.diversityPenalty).toFixed(2)}
                </p>
              )}
            </div>
          )
        })}
      </div>
    </main>
  )
}
