import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ProductCard } from '../components/ProductCard'
import { CATEGORIES } from '../lib/categories'
import { loadProducts } from '../lib/search/loadData'

export function HomePage() {
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: loadProducts })

  const featured = [...(products ?? [])].sort((a, b) => b.rating * b.rating_count - a.rating * a.rating_count).slice(0, 8)

  return (
    <main>
      <section className="border-b border-slate-200 bg-gradient-to-br from-glass-50 to-white dark:border-slate-800 dark:from-glass-900/20 dark:to-slate-950">
        <div className="mx-auto max-w-6xl px-4 py-16 text-center">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Everything you need, all in one cart.
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-slate-600 dark:text-slate-400">
            Thousands of products across electronics, home, fashion, and more — find exactly what
            you're looking for in seconds.
          </p>
          <Link
            to="/search"
            className="mt-6 inline-block rounded-full bg-slate-900 px-6 py-2.5 text-sm font-medium text-white hover:bg-slate-700 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
          >
            Shop now
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-10">
        <h2 className="mb-4 text-lg font-semibold">Shop by category</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-5">
          {CATEGORIES.map((c) => (
            <Link
              key={c.slug}
              to={`/category/${c.slug}`}
              className={`flex flex-col items-center gap-2 rounded-xl bg-gradient-to-br ${c.gradient} px-3 py-5 text-center text-white shadow-sm transition-transform hover:scale-[1.03]`}
            >
              <span className="text-2xl" role="img" aria-hidden>
                {c.icon}
              </span>
              <span className="text-xs font-medium leading-tight">{c.label}</span>
            </Link>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-16">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Top rated right now</h2>
          <Link to="/search" className="text-sm text-glass-600 hover:underline dark:text-glass-300">
            View all
          </Link>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {featured.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>
    </main>
  )
}
