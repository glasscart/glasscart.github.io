import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ProductImage } from '../components/ProductImage'
import { RecommendedProducts } from '../components/RecommendedProducts'
import { categoryByLabel } from '../lib/categories'
import { loadProducts } from '../lib/search/loadData'
import { useCart } from '../store/cart'

export function ProductDetailPage() {
  const { id } = useParams()
  const [quantity, setQuantity] = useState(1)
  const addItem = useCart((s) => s.addItem)
  const { data: products, isLoading } = useQuery({ queryKey: ['products'], queryFn: loadProducts })

  const product = products?.find((p) => p.id === id)
  const meta = product ? categoryByLabel(product.category) : undefined

  if (isLoading) {
    return <main className="mx-auto max-w-5xl px-4 py-8 text-sm text-slate-500">Loading…</main>
  }

  if (!product) {
    return (
      <main className="mx-auto max-w-5xl px-4 py-8">
        <p className="text-sm text-slate-500">
          Product not found. <Link to="/" className="text-glass-600 hover:underline dark:text-glass-300">Back home</Link>.
        </p>
      </main>
    )
  }

  return (
    <>
      <main className="mx-auto max-w-5xl px-4 py-8">
        <nav className="mb-6 text-xs text-slate-500 dark:text-slate-400">
          <Link to="/" className="hover:underline">Home</Link>
          {meta && (
            <>
              {' / '}
              <Link to={`/category/${meta.slug}`} className="hover:underline">{meta.label}</Link>
            </>
          )}
          {' / '}
          <span className="text-slate-700 dark:text-slate-300">{product.title}</span>
        </nav>

        <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
          <ProductImage product={product} className="aspect-square w-full rounded-2xl" />

          <div className="flex flex-col">
            <span className="text-xs font-medium uppercase tracking-wide text-slate-400">{product.category}</span>
            <h1 className="mt-1 text-2xl font-semibold leading-snug">{product.title}</h1>
            <div className="mt-2 flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
              <span>★ {product.rating.toFixed(1)} ({product.rating_count} ratings)</span>
              <span>·</span>
              <span>{product.brand}</span>
            </div>

            <p className="mt-4 text-2xl font-semibold">${product.price.toFixed(2)}</p>

            <p className="mt-4 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{product.description}</p>

            <dl className="mt-4 grid grid-cols-2 gap-2 text-sm">
              <dt className="text-slate-400">Material</dt>
              <dd>{product.material}</dd>
              <dt className="text-slate-400">Tags</dt>
              <dd>{product.tags.join(', ')}</dd>
            </dl>

            <div className="mt-6 flex items-center gap-3">
              <select
                aria-label="Quantity"
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                className="rounded-lg border border-slate-300 bg-white px-2 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
              >
                {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => addItem(product, quantity)}
                className="flex-1 rounded-xl bg-slate-900 py-2.5 text-sm font-medium text-white hover:bg-slate-700 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
              >
                Add to cart
              </button>
            </div>
          </div>
        </div>
      </main>
      <RecommendedProducts productId={product.id} />
    </>
  )
}
