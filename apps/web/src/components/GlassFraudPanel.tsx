import type { FraudManifest } from '../lib/fraud/types'

/** Explains the fraud subsystem's methodology and its evaluation, including its known miss pattern. */
export function GlassFraudPanel({ manifest }: { manifest: FraudManifest }) {
  const evaluation = manifest.fraud_evaluation

  return (
    <div className="mb-4 rounded-xl border border-glass-500/40 bg-glass-50 p-4 text-sm dark:bg-glass-900/20">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-glass-900 dark:text-glass-100">How fraud scores are computed</h3>
        <span className="rounded-full bg-glass-500/15 px-2 py-0.5 text-xs font-medium text-glass-700 dark:text-glass-300">
          precomputed offline
        </span>
      </div>

      <dl className="space-y-1.5 text-xs">
        <div>
          <dt className="font-medium text-slate-500 dark:text-slate-400">velocity (weight {manifest.weights.velocity})</dt>
          <dd className="font-mono text-slate-700 dark:text-slate-300">{manifest.methodology.velocity}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500 dark:text-slate-400">region risk (weight {manifest.weights.region_risk})</dt>
          <dd className="font-mono text-slate-700 dark:text-slate-300">{manifest.methodology.region_risk}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500 dark:text-slate-400">
            new account + high value (weight {manifest.weights.new_account_high_value})
          </dt>
          <dd className="font-mono text-slate-700 dark:text-slate-300">{manifest.methodology.new_account_high_value}</dd>
        </div>
      </dl>

      <div className="mt-3 border-t border-glass-500/20 pt-3">
        <p className="mb-1 text-xs font-medium text-slate-500 dark:text-slate-400">
          evaluation (vs. this dataset's synthetic fraud labels)
        </p>
        <div className="flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs text-slate-600 dark:text-slate-300">
          <span>precision {evaluation.precision}</span>
          <span>recall {evaluation.recall}</span>
          <span>f1 {evaluation.f1}</span>
          <span>
            {evaluation.false_negatives} missed / {evaluation.true_positives + evaluation.false_negatives} fraud
          </span>
        </div>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{evaluation.caveat}</p>
      </div>

      <p className="mt-3 text-[11px] text-slate-400 dark:text-slate-500">
        Full write-up: docs/subsystems/fraud.md · docs/research/fraud.md · models/fraud/MODEL_CARD.md
      </p>
    </div>
  )
}
