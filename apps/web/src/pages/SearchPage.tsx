import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { SearchBar } from '../components/SearchBar'
import { ProductCard } from '../components/ProductCard'
import { GlassSummaryPanel } from '../components/GlassSummaryPanel'
import { GlassRankingPanel } from '../components/GlassRankingPanel'
import { Breadcrumbs } from '../components/Breadcrumbs'
import { FilterSidebar } from '../components/FilterSidebar'
import { ResultsToolbar } from '../components/ResultsToolbar'
import { useProductFilters } from '../hooks/useProductFilters'
import { useGlassMode } from '../store/glassMode'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { getSearchProvider } from '../lib/search/provider'
import { FUSION_ALPHA } from '../lib/search/config'
import { rerank, SEARCH_RANKING_WEIGHTS } from '../lib/ranking/rerank'

type SortKey = 'relevance' | 'rating' | 'price-asc' | 'price-desc'

const SORT_OPTIONS = [
  { value: 'relevance' as const, label: 'Best match' },
  { value: 'rating' as const, label: 'Top rated' },
  { value: 'price-asc' as const, label: 'Price: low to high' },
  { value: 'price-desc' as const, label: 'Price: high to low' },
]

const DEFAULT_QUERY = 'cozy running gear'
const RESULT_LIMIT = 12
// Fetch a wider candidate pool than we display so re-ranking (especially
// diversification) has real alternatives to promote, not just a reshuffle
// of a pool that was already truncated to near-duplicates.
const CANDIDATE_POOL_SIZE = 30

export function SearchPage() {
  const [searchParams] = useSearchParams()
  const [query, setQuery] = useState(searchParams.get('q') || DEFAULT_QUERY)
  const [sort, setSort] = useState<SortKey>('relevance')
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

  // Ranked position is fixed at "best match" order — filters/sort narrow or
  // reorder the *display*, but the badge still reflects the search+rerank
  // pipeline's own verdict, not wherever a product lands after resorting.
  const rankedProducts = useMemo(() => ranking?.items.map((r) => r.product) ?? [], [ranking])
  const { filtered, filters, setFilters, facets } = useProductFilters(rankedProducts)

  const displayedItems = useMemo(() => {
    const withRank = filtered.map((product) => ({
      product,
      rank: rankedProducts.findIndex((p) => p.id === product.id) + 1,
    }))
    if (sort === 'price-asc') return [...withRank].sort((a, b) => a.product.price - b.product.price)
    if (sort === 'price-desc') return [...withRank].sort((a, b) => b.product.price - a.product.price)
    if (sort === 'rating') return [...withRank].sort((a, b) => b.product.rating - a.product.rating)
    return withRank.sort((a, b) => a.rank - b.rank)
  }, [filtered, rankedProducts, sort])

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: 'Shop all' }]} />
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

      {data && data.results.length > 0 && (
        <div className="flex flex-col gap-6 md:flex-row">
          <FilterSidebar facets={facets} filters={filters} onChange={setFilters} />

          <div className="min-w-0 flex-1">
            <ResultsToolbar
              count={displayedItems.length}
              totalCount={rankedProducts.length}
              sort={sort}
              sortOptions={SORT_OPTIONS}
              onSortChange={setSort}
            />

            {displayedItems.length === 0 && (
              <p className="text-sm text-slate-500">No products match the selected filters.</p>
            )}

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {displayedItems.map(({ product, rank }) => {
                const original = data?.results.find((r) => r.product.id === product.id)
                const ranked = ranking?.items.find((r) => r.product.id === product.id)
                return (
                  <div key={product.id}>
                    <ProductCard product={product} rank={rank} score={original?.score} alpha={data?.glass.fusionAlpha} />
                    {glassMode && ranked && (
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
          </div>
        </div>
      )}
    </main>
  )
}
