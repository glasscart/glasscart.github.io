import type { ScoreBreakdown } from '../lib/search/types'

/** Per-result diagnostics: how much of the fused score came from keyword vs. semantic match. */
export function GlassScoreBreakdown({ score, alpha }: { score: ScoreBreakdown; alpha: number }) {
  const bm25Contribution = alpha * score.bm25Normalized
  const semanticContribution = (1 - alpha) * score.semanticNormalized
  const total = bm25Contribution + semanticContribution || 1
  const bm25Pct = (bm25Contribution / total) * 100

  return (
    <div className="mt-2 space-y-1.5 rounded-lg border border-glass-500/30 bg-glass-50 p-2.5 text-xs dark:bg-glass-900/20">
      <div className="flex items-center justify-between font-mono text-slate-600 dark:text-slate-300">
        <span>fused score</span>
        <span className="font-semibold text-glass-600 dark:text-glass-300">{score.fused.toFixed(3)}</span>
      </div>
      <div className="flex h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
        <div className="bg-glass-500" style={{ width: `${bm25Pct}%` }} title="BM25 (keyword) contribution" />
        <div className="bg-glass-300" style={{ width: `${100 - bm25Pct}%` }} title="Semantic contribution" />
      </div>
      <div className="flex justify-between font-mono text-[11px] text-slate-500 dark:text-slate-400">
        <span>BM25 {score.bm25Raw.toFixed(2)} → {score.bm25Normalized.toFixed(2)}</span>
        <span>cos {score.semanticRawCosine.toFixed(2)} → {score.semanticNormalized.toFixed(2)}</span>
      </div>
    </div>
  )
}
