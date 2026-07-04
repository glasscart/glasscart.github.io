import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ProductCard } from '../components/ProductCard'
import { Breadcrumbs } from '../components/Breadcrumbs'
import { FilterSidebar } from '../components/FilterSidebar'
import { ResultsToolbar } from '../components/ResultsToolbar'
import { useProductFilters } from '../hooks/useProductFilters'
import { categoryBySlug } from '../lib/categories'
import { loadProducts } from '../lib/search/loadData'

type SortKey = 'rating' | 'price-asc' | 'price-desc'

const SORT_OPTIONS = [
  { value: 'rating' as const, label: 'Top rated' },
  { value: 'price-asc' as const, label: 'Price: low to high' },
  { value: 'price-desc' as const, label: 'Price: high to low' },
]

export function CategoryPage() {
  const { slug = '' } = useParams()
  const [sort, setSort] = useState<SortKey>('rating')
  const meta = categoryBySlug(slug)
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: loadProducts })

  const categoryItems = (products ?? []).filter((p) => p.category === meta?.label)
  const { filtered, filters, setFilters, facets } = useProductFilters(categoryItems)

  const items = [...filtered].sort((a, b) => {
    if (sort === 'price-asc') return a.price - b.price
    if (sort === 'price-desc') return b.price - a.price
    return b.rating - a.rating
  })

  if (products && !meta) {
    return (
      <main className="mx-auto max-w-6xl px-4 py-8">
        <p className="text-sm text-slate-500">
          Unknown category. <Link to="/" className="text-glass-600 hover:underline dark:text-glass-300">Back home</Link>.
        </p>
      </main>
    )
  }

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: meta?.label ?? '' }]} />
      <h1 className="mb-6 flex items-center gap-2 text-2xl font-semibold">
        <span aria-hidden>{meta?.icon}</span> {meta?.label}
      </h1>

      <div className="flex flex-col gap-6 md:flex-row">
        <FilterSidebar facets={facets} filters={filters} onChange={setFilters} />

        <div className="min-w-0 flex-1">
          <ResultsToolbar
            count={items.length}
            totalCount={categoryItems.length}
            sort={sort}
            sortOptions={SORT_OPTIONS}
            onSortChange={setSort}
          />

          {products && items.length === 0 && (
            <p className="text-sm text-slate-500">No products match the selected filters.</p>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </div>
      </div>
    </main>
  )
}
