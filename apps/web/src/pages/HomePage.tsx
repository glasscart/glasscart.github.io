import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ProductCard } from '../components/ProductCard'
import { CATEGORIES } from '../lib/categories'
import { loadProducts } from '../lib/search/loadData'
import type { Product } from '../lib/search/types'

function ProductRow({ title, products, viewAllTo }: { title: string; products: Product[]; viewAllTo: string }) {
  return (
    <section className="mx-auto max-w-6xl px-4 py-6">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold">{title}</h2>
        <Link to={viewAllTo} className="text-sm text-glass-600 hover:underline dark:text-glass-300">
          View all
        </Link>
      </div>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>
    </section>
  )
}

export function HomePage() {
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: loadProducts })

  const topRated = [...(products ?? [])]
    .sort((a, b) => b.rating * b.rating_count - a.rating * a.rating_count)
    .slice(0, 10)
  const newArrivals = [...(products ?? [])]
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .slice(0, 10)

  return (
    <main>
      <section className="border-b border-slate-200 bg-gradient-to-br from-glass-50 to-white dark:border-slate-800 dark:from-glass-900/20 dark:to-slate-950">
        <div className="mx-auto max-w-6xl px-4 py-8 text-center sm:py-9">
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            Everything you need, all in one cart.
          </h1>
          <p className="mx-auto mt-2 max-w-xl text-sm text-slate-600 dark:text-slate-400">
            Thousands of products across electronics, home, fashion, and more — find exactly what
            you're looking for in seconds.
          </p>
          <Link
            to="/search"
            className="mt-4 inline-block rounded-full bg-slate-900 px-6 py-2 text-sm font-medium text-white hover:bg-slate-700 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
          >
            Shop now
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-6">
        <h2 className="mb-3 text-base font-semibold">Shop by category</h2>
        <div className="grid grid-cols-3 gap-2 sm:grid-cols-5 md:grid-cols-10">
          {CATEGORIES.map((c) => (
            <Link
              key={c.slug}
              to={`/category/${c.slug}`}
              className="flex flex-col items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2 py-3 text-center transition-colors hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:hover:border-slate-700 dark:hover:bg-slate-800"
            >
              <span
                className={`flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br text-sm ${c.gradient}`}
                role="img"
                aria-hidden
              >
                {c.icon}
              </span>
              <span className="text-[11px] font-medium leading-tight text-slate-700 dark:text-slate-300">
                {c.label}
              </span>
            </Link>
          ))}
        </div>
      </section>

      <div className="divide-y divide-slate-200 dark:divide-slate-800">
        <ProductRow title="Top rated right now" products={topRated} viewAllTo="/search" />
        <ProductRow title="New arrivals" products={newArrivals} viewAllTo="/search" />
      </div>
    </main>
  )
}
