import { useQuery } from '@tanstack/react-query'
import { loadPricingManifest, loadPricingRecommendations } from '../lib/pricing/loadPricing'
import { useGlassMode } from '../store/glassMode'

const RECOMMENDATION_LABEL: Record<string, string> = {
  raise: 'Simulation suggests raising the price',
  lower: 'Simulation suggests lowering the price',
  'near-optimal': 'Simulation finds the current price near-optimal',
}

/**
 * Unlike reviews/recommendations, this panel only ever renders when Glass
 * Mode is on — a synthetic "you should charge more" signal would be
 * actively misleading to a shopper outside a context that makes clear
 * it's a simulation over made-up inputs. See models/pricing/MODEL_CARD.md.
 */
export function PricingInsightsPanel({ productId }: { productId: string }) {
  const glassMode = useGlassMode((s) => s.enabled)
  const { data } = useQuery({
    queryKey: ['pricing', productId],
    queryFn: async () => {
      const [recommendations, manifest] = await Promise.all([loadPricingRecommendations(), loadPricingManifest()])
      const recommendation = recommendations.find((r) => r.product_id === productId) ?? null
      return { recommendation, manifest }
    },
    enabled: glassMode,
  })

  if (!glassMode || !data?.recommendation) return null
  const { recommendation: r, manifest } = data

  return (
    <div className="mb-4 rounded-xl border border-glass-500/40 bg-glass-50 p-4 text-sm dark:bg-glass-900/20">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-glass-900 dark:text-glass-100">Pricing intelligence (simulated)</h3>
        <span className="rounded-full bg-glass-500/15 px-2 py-0.5 text-xs font-medium text-glass-700 dark:text-glass-300">
          Glass Mode only
        </span>
      </div>

      <p className="mb-3 text-slate-600 dark:text-slate-300">
        GlassCart has no real transaction data, so every input below (elasticity, cost, demand) is
        simulated, not measured — see the model card (linked below) before reading anything here as a
        real recommendation. The pricing formula itself (constant-elasticity demand + monopoly markup
        rule) is real economics, applied to made-up numbers.
      </p>

      <p className="mb-3 font-medium text-slate-700 dark:text-slate-200">{RECOMMENDATION_LABEL[r.recommendation]}</p>

      <dl className="grid grid-cols-2 gap-x-4 gap-y-2 font-mono text-xs sm:grid-cols-4">
        <Field label="elasticity" value={r.elasticity.toFixed(2)} />
        <Field label="marginal cost" value={`$${r.marginal_cost.toFixed(2)}`} />
        <Field label="current price" value={`$${r.current_price.toFixed(2)}`} />
        <Field label="optimal price" value={`$${r.optimal_price.toFixed(2)}`} />
        <Field label="price change" value={`${r.price_change_pct > 0 ? '+' : ''}${r.price_change_pct}%`} />
        <Field label="profit uplift" value={`${r.profit_uplift_pct > 0 ? '+' : ''}${r.profit_uplift_pct}%`} />
        <Field label="current profit" value={`$${r.current_profit.toFixed(0)}/mo`} />
        <Field label="optimal profit" value={`$${r.optimal_profit.toFixed(0)}/mo`} />
      </dl>

      <div className="mt-3 overflow-x-auto border-t border-glass-500/20 pt-3">
        <p className="mb-1 text-xs font-medium text-slate-500 dark:text-slate-400">
          simulated response curve (price → quantity/revenue/profit)
        </p>
        <table className="w-full min-w-[420px] font-mono text-[11px] text-slate-600 dark:text-slate-300">
          <thead>
            <tr className="text-left text-slate-400 dark:text-slate-500">
              <th className="pr-3 font-normal">price</th>
              <th className="pr-3 font-normal">qty</th>
              <th className="pr-3 font-normal">revenue</th>
              <th className="font-normal">profit</th>
            </tr>
          </thead>
          <tbody>
            {r.curve.map((point) => (
              <tr key={point.price_multiplier} className={point.price_multiplier === 1.0 ? 'font-semibold' : undefined}>
                <td className="pr-3">${point.price.toFixed(2)}</td>
                <td className="pr-3">{point.quantity.toFixed(0)}</td>
                <td className="pr-3">${point.revenue.toFixed(0)}</td>
                <td>${point.profit.toFixed(0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {manifest && (
        <p className="mt-3 text-[11px] text-slate-400 dark:text-slate-500">
          {manifest.methodology} · Full write-up: docs/subsystems/pricing.md · docs/research/pricing.md ·
          models/pricing/MODEL_CARD.md
        </p>
      )}
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
