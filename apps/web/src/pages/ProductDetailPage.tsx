import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ProductImage } from '../components/ProductImage'
import { PricingInsightsPanel } from '../components/PricingInsightsPanel'
import { ReviewsSection } from '../components/ReviewsSection'
import { RecommendedProducts } from '../components/RecommendedProducts'
import { Breadcrumbs } from '../components/Breadcrumbs'
import { StarRating } from '../components/StarRating'
import { categoryByLabel } from '../lib/categories'
import { loadProducts } from '../lib/search/loadData'
import { loadInventoryForecasts } from '../lib/inventory/loadInventory'
import { useCart } from '../store/cart'
import { useGlassMode } from '../store/glassMode'

export function ProductDetailPage() {
  const { id } = useParams()
  const [quantity, setQuantity] = useState(1)
  const addItem = useCart((s) => s.addItem)
  const glassMode = useGlassMode((s) => s.enabled)
  const { data: products, isLoading } = useQuery({ queryKey: ['products'], queryFn: loadProducts })
  const { data: forecasts } = useQuery({
    queryKey: ['inventory-forecasts'],
    queryFn: loadInventoryForecasts,
    enabled: glassMode,
  })

  const product = products?.find((p) => p.id === id)
  const meta = product ? categoryByLabel(product.category) : undefined
  const forecast = forecasts?.find((f) => f.product_id === id)

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
        <Breadcrumbs
          items={[
            { label: 'Home', to: '/' },
            ...(meta ? [{ label: meta.label, to: `/category/${meta.slug}` }] : []),
            { label: product.title },
          ]}
        />

        <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
          <ProductImage product={product} className="aspect-square w-full rounded-2xl" />

          <div className="flex flex-col">
            <span className="text-xs font-medium uppercase tracking-wide text-slate-400">{product.category}</span>
            <h1 className="mt-1 text-2xl font-semibold leading-snug">{product.title}</h1>
            <div className="mt-2">
              <StarRating rating={product.rating} count={product.rating_count} />
            </div>

            <p className="mt-4 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{product.description}</p>

            <dl className="mt-4 grid grid-cols-2 gap-2 text-sm">
              <dt className="text-slate-400">Material</dt>
              <dd>{product.material}</dd>
              <dt className="text-slate-400">Tags</dt>
              <dd>{product.tags.join(', ')}</dd>
            </dl>

            {/* Buy box: price/seller/stock/qty grouped as their own visually
                distinct unit, separate from the descriptive content above —
                the standard e-commerce pattern of isolating "what will
                happen if I click Add to cart" from "what is this product." */}
            <div className="mt-6 rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
              <p className="text-2xl font-semibold">${product.price.toFixed(2)}</p>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Sold by {product.brand}</p>

              {glassMode && forecast && (
                <p className="mt-2 text-sm">
                  {forecast.current_stock > 0 ? (
                    <span className="text-emerald-600 dark:text-emerald-400">
                      {forecast.current_stock} in stock
                    </span>
                  ) : (
                    <span className="text-red-600 dark:text-red-400">Out of stock</span>
                  )}
                  <span className="ml-1.5 text-xs text-slate-400">
                    (simulated forecast, Glass Mode only — see{' '}
                    <Link to="/inventory" className="hover:underline">
                      Inventory
                    </Link>
                    )
                  </span>
                </p>
              )}

              <div className="mt-4 flex items-center gap-3">
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
        </div>
      </main>
      <div className="mx-auto max-w-5xl px-4 pb-6">
        <PricingInsightsPanel productId={product.id} />
      </div>
      <ReviewsSection productId={product.id} />
      <RecommendedProducts productId={product.id} />
    </>
  )
}
