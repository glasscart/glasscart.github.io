import type { RecommendationExplanation } from '../lib/recommendations/similar'

/** The recommendations subsystem's counterpart to search's GlassSummaryPanel. */
export function GlassRecommendationPanel({ glass }: { glass: RecommendationExplanation }) {
  return (
    <div className="mb-4 rounded-xl border border-glass-500/40 bg-glass-50 p-4 text-sm dark:bg-glass-900/20">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-glass-900 dark:text-glass-100">How these were picked</h3>
        <span className="rounded-full bg-glass-500/15 px-2 py-0.5 text-xs font-medium text-glass-700 dark:text-glass-300">
          ran fully in your browser
        </span>
      </div>

      <p className="mb-3 text-slate-600 dark:text-slate-300">{glass.whyAiWasUsed}</p>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-xs sm:grid-cols-4">
        <Field label="method" value={glass.method} />
        <Field label="embedding model" value={glass.embeddingModel} />
        <Field label="embedding dim" value={String(glass.embeddingDim)} />
        <Field label="corpus size" value={`${glass.corpusSize} products`} />
      </dl>

      <div className="mt-3 border-t border-glass-500/20 pt-3 font-mono text-xs text-slate-600 dark:text-slate-300">
        lookup {glass.timingMs.toFixed(1)}ms
      </div>

      <div className="mt-3 border-t border-glass-500/20 pt-3">
        <p className="mb-1 text-xs font-medium text-slate-500 dark:text-slate-400">limitations</p>
        <ul className="list-inside list-disc space-y-0.5 text-xs text-slate-600 dark:text-slate-300">
          {glass.limitations.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </div>

      <p className="mt-3 text-[11px] text-slate-400 dark:text-slate-500">
        Full write-up: docs/subsystems/recommendations.md · docs/research/recommendations.md
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
