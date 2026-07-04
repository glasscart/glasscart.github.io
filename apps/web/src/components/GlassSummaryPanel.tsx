import type { GlassExplanation } from '../lib/search/types'

/** The full "model card, live" panel shown once per search when Glass Mode is on. */
export function GlassSummaryPanel({ glass }: { glass: GlassExplanation }) {
  return (
    <div className="mb-6 rounded-xl border border-glass-500/40 bg-glass-50 p-4 text-sm dark:bg-glass-900/20">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-semibold text-glass-900 dark:text-glass-100">How this search worked</h2>
        <span className="rounded-full bg-glass-500/15 px-2 py-0.5 text-xs font-medium text-glass-700 dark:text-glass-300">
          {glass.provider === 'client' ? 'ran fully in your browser' : 'ran on the reference API'}
        </span>
      </div>

      <p className="mb-3 text-slate-600 dark:text-slate-300">{glass.whyAiWasUsed}</p>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-xs sm:grid-cols-3">
        <Field label="embedding model" value={glass.embeddingModel} />
        <Field label="embedding dim" value={String(glass.embeddingDim)} />
        <Field label="BM25 k1 / b" value={`${glass.bm25K1} / ${glass.bm25B}`} />
        <Field label="fusion α (BM25 weight)" value={String(glass.fusionAlpha)} />
        <Field label="corpus size" value={`${glass.corpusSize} products`} />
        <Field
          label="embeddings built"
          value={glass.artifactGeneratedAt ? new Date(glass.artifactGeneratedAt).toISOString().slice(0, 10) : 'unknown'}
        />
      </dl>

      <div className="mt-3 border-t border-glass-500/20 pt-3">
        <p className="mb-1 text-xs font-medium text-slate-500 dark:text-slate-400">latency breakdown</p>
        <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs text-slate-600 dark:text-slate-300">
          <span>tokenize {glass.timing.tokenizeQueryMs.toFixed(1)}ms</span>
          <span>BM25 {glass.timing.bm25ScoreMs.toFixed(1)}ms</span>
          <span>embed+semantic {glass.timing.embedQueryMs.toFixed(1)}ms</span>
          <span>fuse {glass.timing.fusionMs.toFixed(1)}ms</span>
          <span className="font-semibold">total {glass.timing.totalMs.toFixed(1)}ms</span>
        </div>
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
        Full write-up: docs/subsystems/search.md · models/search-embeddings/MODEL_CARD.md · datasets/products/DATASET_CARD.md
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
