import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ProductCard } from '../components/ProductCard'
import { categoryBySlug } from '../lib/categories'
import { loadProducts } from '../lib/search/loadData'

type SortKey = 'rating' | 'price-asc' | 'price-desc'

export function CategoryPage() {
  const { slug = '' } = useParams()
  const [sort, setSort] = useState<SortKey>('rating')
  const meta = categoryBySlug(slug)
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: loadProducts })

  const items = (products ?? [])
    .filter((p) => p.category === meta?.label)
    .sort((a, b) => {
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
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="flex items-center gap-2 text-2xl font-semibold">
          <span aria-hidden>{meta?.icon}</span> {meta?.label}
        </h1>
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value as SortKey)}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
        >
          <option value="rating">Top rated</option>
          <option value="price-asc">Price: low to high</option>
          <option value="price-desc">Price: high to low</option>
        </select>
      </div>

      {products && items.length === 0 && <p className="text-sm text-slate-500">No products in this category.</p>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </main>
  )
}
