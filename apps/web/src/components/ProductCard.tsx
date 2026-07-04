import type { SearchResultItem } from '../lib/search/types'
import { GlassScoreBreakdown } from './GlassScoreBreakdown'

export function ProductCard({ item, glassMode, alpha }: { item: SearchResultItem; glassMode: boolean; alpha: number }) {
  const { product, rank } = item

  return (
    <div className="flex flex-col rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="mb-1 flex items-start justify-between gap-2">
        <span className="text-xs font-medium uppercase tracking-wide text-slate-400">{product.category}</span>
        <span className="text-xs text-slate-400">#{rank}</span>
      </div>
      <h3 className="mb-1 font-medium leading-snug">{product.title}</h3>
      <p className="mb-3 line-clamp-2 text-sm text-slate-500 dark:text-slate-400">{product.description}</p>
      <div className="mt-auto flex items-center justify-between text-sm">
        <span className="font-semibold">${product.price.toFixed(2)}</span>
        <span className="text-slate-500 dark:text-slate-400">
          ★ {product.rating.toFixed(1)} ({product.rating_count})
        </span>
      </div>
      <div className="mt-1 text-xs text-slate-400">{product.brand}</div>
      {glassMode && <GlassScoreBreakdown score={item.score} alpha={alpha} />}
    </div>
  )
}
