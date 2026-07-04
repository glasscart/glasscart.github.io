import { useMemo, useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { SearchBar } from '../components/SearchBar'
import { ProductCard } from '../components/ProductCard'
import { GlassSummaryPanel } from '../components/GlassSummaryPanel'
import { useGlassMode } from '../store/glassMode'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { getSearchProvider } from '../lib/search/provider'
import { FUSION_ALPHA } from '../lib/search/config'

const DEFAULT_QUERY = 'cozy running gear'

export function SearchPage() {
  const [query, setQuery] = useState(DEFAULT_QUERY)
  const debouncedQuery = useDebouncedValue(query, 250)
  const glassMode = useGlassMode((s) => s.enabled)
  const provider = useMemo(() => getSearchProvider(), [])

  const { data, isFetching, isError, error } = useQuery({
    queryKey: ['search', provider.name, debouncedQuery],
    queryFn: () => provider.search(debouncedQuery, { limit: 12, alpha: FUSION_ALPHA }),
    enabled: debouncedQuery.trim().length > 0,
    placeholderData: keepPreviousData,
  })

  return (
    <main className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-semibold">Product search</h1>
      <p className="mb-5 text-sm text-slate-500 dark:text-slate-400">
        Hybrid keyword + semantic search over a synthetic catalog — runs entirely in your browser.
        Turn on <span className="font-medium text-glass-600 dark:text-glass-300">Glass Mode</span> above to see
        exactly how each result was scored.
      </p>

      <div className="mb-6">
        <SearchBar value={query} onChange={setQuery} isLoading={isFetching} />
      </div>

      {isError && (
        <p className="mb-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300">
          Search failed: {(error as Error).message}
        </p>
      )}

      {glassMode && data && <GlassSummaryPanel glass={data.glass} />}

      {data && data.results.length === 0 && (
        <p className="text-sm text-slate-500">No products matched “{data.query}”.</p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data?.results.map((item) => (
          <ProductCard key={item.product.id} item={item} glassMode={glassMode} alpha={data.glass.fusionAlpha} />
        ))}
      </div>
    </main>
  )
}
