/** Renders a 1–5 star rating as five glyphs with a partial-fill gradient clip, rather than plain "★ 4.3" text. */
export function StarRating({
  rating,
  count,
  size = 'sm',
}: {
  rating: number
  count?: number
  size?: 'sm' | 'md'
}) {
  const pct = Math.max(0, Math.min(100, (rating / 5) * 100))
  const textSize = size === 'md' ? 'text-lg' : 'text-sm'

  return (
    <span className="inline-flex items-center gap-1.5" title={`${rating.toFixed(1)} out of 5`}>
      <span className={`relative inline-block leading-none ${textSize}`} aria-hidden>
        <span className="text-slate-300 dark:text-slate-700">★★★★★</span>
        <span
          className="absolute inset-0 overflow-hidden whitespace-nowrap text-amber-400"
          style={{ width: `${pct}%` }}
        >
          ★★★★★
        </span>
      </span>
      <span className="sr-only">{rating.toFixed(1)} out of 5 stars</span>
      {count !== undefined && (
        <span className="text-sm text-slate-500 dark:text-slate-400">
          {rating.toFixed(1)} ({count.toLocaleString()})
        </span>
      )}
    </span>
  )
}
