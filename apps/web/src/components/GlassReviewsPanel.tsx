import type { ReviewsManifest } from '../lib/reviews/types'

/** Explains the reviews subsystem's methodology and its (honestly-caveated) fake-review evaluation. */
export function GlassReviewsPanel({ manifest }: { manifest: ReviewsManifest }) {
  const evaluation = manifest.fake_heuristic_evaluation

  return (
    <div className="mb-4 rounded-xl border border-glass-500/40 bg-glass-50 p-4 text-sm dark:bg-glass-900/20">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-glass-900 dark:text-glass-100">How reviews are analyzed</h3>
        <span className="rounded-full bg-glass-500/15 px-2 py-0.5 text-xs font-medium text-glass-700 dark:text-glass-300">
          precomputed offline
        </span>
      </div>

      <dl className="space-y-1.5 text-xs">
        <div>
          <dt className="font-medium text-slate-500 dark:text-slate-400">sentiment</dt>
          <dd className="font-mono text-slate-700 dark:text-slate-300">{manifest.methodology.sentiment}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500 dark:text-slate-400">aspect extraction</dt>
          <dd className="font-mono text-slate-700 dark:text-slate-300">{manifest.methodology.aspect_extraction}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500 dark:text-slate-400">fake-review heuristic</dt>
          <dd className="font-mono text-slate-700 dark:text-slate-300">{manifest.methodology.fake_review_heuristic}</dd>
        </div>
      </dl>

      <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 border-t border-glass-500/20 pt-3 font-mono text-xs sm:grid-cols-4">
        <Field label="lexicon size" value={`${manifest.lexicon_size} words`} />
        <Field label="fake threshold" value={String(manifest.fake_score_threshold)} />
        <Field label="reviews analyzed" value={String(manifest.num_reviews)} />
        <Field label="products covered" value={String(manifest.num_products)} />
      </div>

      <div className="mt-3 border-t border-glass-500/20 pt-3">
        <p className="mb-1 text-xs font-medium text-slate-500 dark:text-slate-400">
          fake-review heuristic evaluation (vs. this dataset's synthetic labels)
        </p>
        <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs text-slate-600 dark:text-slate-300">
          <span>precision {evaluation.precision}</span>
          <span>recall {evaluation.recall}</span>
          <span>f1 {evaluation.f1}</span>
        </div>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{evaluation.caveat}</p>
      </div>

      <p className="mt-3 text-[11px] text-slate-400 dark:text-slate-500">
        Full write-up: docs/subsystems/reviews.md · docs/research/reviews.md · models/reviews/MODEL_CARD.md
      </p>
    </div>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-slate-400 dark:text-slate-500">{label}</dt>
      <dd className="truncate text-slate-700 dark:text-slate-200" title={value}>
        {value}
      </dd>
    </div>
  )
}
