import { Link } from 'react-router-dom'
import type { Product, ScoreBreakdown } from '../lib/search/types'
import { GlassScoreBreakdown } from './GlassScoreBreakdown'
import { ProductImage } from './ProductImage'
import { StarRating } from './StarRating'
import { useCart } from '../store/cart'
import { useGlassMode } from '../store/glassMode'

interface ProductCardProps {
  product: Product
  /** Search-result-only fields — omitted when the card is used for plain browsing (home, category). */
  rank?: number
  score?: ScoreBreakdown
  alpha?: number
}

export function ProductCard({ product, rank, score, alpha }: ProductCardProps) {
  const addItem = useCart((s) => s.addItem)
  const glassMode = useGlassMode((s) => s.enabled)

  return (
    <div className="group flex flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition-shadow hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
      <Link to={`/product/${product.id}`} className="block">
        <ProductImage product={product} className="aspect-square w-full" />
      </Link>
      <div className="flex flex-1 flex-col p-4">
        <div className="mb-1 flex items-start justify-between gap-2">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-400">{product.category}</span>
          {rank !== undefined && <span className="text-xs text-slate-400">#{rank}</span>}
        </div>
        <Link to={`/product/${product.id}`} className="mb-1 font-medium leading-snug hover:underline">
          {product.title}
        </Link>
        <p className="mb-3 line-clamp-2 text-sm text-slate-500 dark:text-slate-400">{product.description}</p>
        <div className="mb-1">
          <StarRating rating={product.rating} count={product.rating_count} />
        </div>
        <div className="mt-auto flex items-center justify-between text-sm">
          <span className="font-semibold">${product.price.toFixed(2)}</span>
          <span className="text-xs text-slate-400">{product.brand}</span>
        </div>

        <button
          type="button"
          onClick={() => addItem(product)}
          className="mt-3 w-full rounded-lg border border-slate-300 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:border-slate-900 hover:bg-slate-900 hover:text-white dark:border-slate-700 dark:text-slate-200 dark:hover:border-white dark:hover:bg-white dark:hover:text-slate-900"
        >
          Add to cart
        </button>

        {glassMode && score && alpha !== undefined && <GlassScoreBreakdown score={score} alpha={alpha} />}
      </div>
    </div>
  )
}
