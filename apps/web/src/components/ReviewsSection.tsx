import { useQuery } from '@tanstack/react-query'
import { loadProductReviewSummaries, loadReviewAnalysis, loadReviews, loadReviewsManifest } from '../lib/reviews/loadReviews'
import { useGlassMode } from '../store/glassMode'
import { GlassReviewsPanel } from './GlassReviewsPanel'

function aspectBadgeClass(sentiment: number): string {
  if (sentiment > 0.3) {
    return 'border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
  }
  if (sentiment < -0.3) {
    return 'border-red-300 bg-red-50 text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300'
  }
  return 'border-slate-300 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300'
}

export function ReviewsSection({ productId }: { productId: string }) {
  const glassMode = useGlassMode((s) => s.enabled)
  const { data } = useQuery({
    queryKey: ['reviews', productId],
    queryFn: async () => {
      const [reviews, analysis, summaries, manifest] = await Promise.all([
        loadReviews(),
        loadReviewAnalysis(),
        loadProductReviewSummaries(),
        loadReviewsManifest(),
      ])
      const analysisById = new Map(analysis.map((a) => [a.review_id, a]))
      const productReviews = reviews
        .filter((r) => r.product_id === productId)
        .map((r) => ({ review: r, analysis: analysisById.get(r.id) }))
        .sort((a, b) => b.review.helpful_votes - a.review.helpful_votes)
      const summary = summaries.find((s) => s.product_id === productId) ?? null
      return { productReviews, summary, manifest }
    },
  })

  if (!data || data.productReviews.length === 0) return null
  const { productReviews, summary, manifest } = data

  return (
    <section className="mx-auto max-w-5xl px-4 pb-16">
      <h2 className="mb-4 text-lg font-semibold">Reviews</h2>

      {glassMode && manifest && <GlassReviewsPanel manifest={manifest} />}

      {summary && summary.aspects.length > 0 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {summary.aspects.map((a) => (
            <span
              key={a.aspect}
              className={['rounded-full border px-3 py-1 text-xs font-medium', aspectBadgeClass(a.avg_sentiment)].join(' ')}
            >
              {a.aspect} {a.avg_sentiment > 0.3 ? '👍' : a.avg_sentiment < -0.3 ? '👎' : '·'} ({a.mentions})
            </span>
          ))}
        </div>
      )}

      <div className="space-y-4">
        {productReviews.map(({ review, analysis }) => (
          <article
            key={review.id}
            className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900"
          >
            <div className="mb-1 flex items-center justify-between">
              <span className="text-sm font-medium">{review.title}</span>
              <span className="text-xs text-slate-400">★ {review.rating}</span>
            </div>
            <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <span>{review.author}</span>
              {review.verified_purchase && (
                <span className="text-emerald-600 dark:text-emerald-400">Verified purchase</span>
              )}
              <span>{review.created_at}</span>
              {review.helpful_votes > 0 && <span>{review.helpful_votes} found this helpful</span>}
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-300">{review.body}</p>

            {glassMode && analysis && (
              <div className="mt-3 rounded-lg border border-glass-500/30 bg-glass-50 p-2.5 font-mono text-[11px] text-slate-600 dark:bg-glass-900/20 dark:text-slate-300">
                <div className="flex flex-wrap gap-x-3 gap-y-1">
                  <span>sentiment {analysis.sentiment_score.toFixed(2)}</span>
                  <span>
                    fake score {analysis.fake_score.toFixed(2)}
                    {analysis.likely_fake ? ' (flagged)' : ''}
                  </span>
                  {review.is_fake_synthetic && (
                    <span className="text-glass-600 dark:text-glass-300">ground truth: synthetic fake</span>
                  )}
                </div>
                {Object.keys(analysis.aspects).length > 0 && (
                  <div className="mt-1">
                    aspects:{' '}
                    {Object.entries(analysis.aspects)
                      .map(([a, s]) => `${a} ${s.toFixed(2)}`)
                      .join(', ')}
                  </div>
                )}
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  )
}
