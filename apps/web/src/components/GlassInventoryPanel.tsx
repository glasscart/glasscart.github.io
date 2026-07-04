import type { InventoryManifest } from '../lib/inventory/types'

/** Explains the inventory subsystem's forecasting + reorder-point methodology. */
export function GlassInventoryPanel({ manifest }: { manifest: InventoryManifest }) {
  return (
    <div className="mb-4 rounded-xl border border-glass-500/40 bg-glass-50 p-4 text-sm dark:bg-glass-900/20">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-glass-900 dark:text-glass-100">How forecasts are computed</h3>
        <span className="rounded-full bg-glass-500/15 px-2 py-0.5 text-xs font-medium text-glass-700 dark:text-glass-300">
          precomputed offline
        </span>
      </div>

      <dl className="space-y-1.5 text-xs">
        <div>
          <dt className="font-medium text-slate-500 dark:text-slate-400">demand forecast</dt>
          <dd className="font-mono text-slate-700 dark:text-slate-300">{manifest.methodology.forecast}</dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500 dark:text-slate-400">reorder point</dt>
          <dd className="font-mono text-slate-700 dark:text-slate-300">{manifest.methodology.reorder_point}</dd>
        </div>
      </dl>

      <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 border-t border-glass-500/20 pt-3 font-mono text-xs sm:grid-cols-4">
        <Field label="alpha (level)" value={String(manifest.alpha)} />
        <Field label="beta (trend)" value={String(manifest.beta)} />
        <Field label="forecast horizon" value={`${manifest.forecast_horizon_days}d`} />
        <Field label="assumed lead time" value={`${manifest.assumed_lead_time_days}d`} />
        <Field label="service level z" value={String(manifest.service_level_z)} />
        <Field label="products tracked" value={String(manifest.num_products)} />
        <Field label="need reorder" value={String(manifest.num_products_needing_reorder)} />
      </div>

      <p className="mt-3 text-[11px] text-slate-400 dark:text-slate-500">
        Assumed lead time is a documented simplification, not a measured or leaked simulation value —
        see models/inventory/MODEL_CARD.md. Full write-up: docs/subsystems/inventory.md ·
        docs/research/inventory.md
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
