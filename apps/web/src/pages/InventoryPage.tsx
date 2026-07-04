import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { loadInventoryForecasts, loadInventoryManifest } from '../lib/inventory/loadInventory'
import { loadProducts } from '../lib/search/loadData'
import { useGlassMode } from '../store/glassMode'
import { GlassInventoryPanel } from '../components/GlassInventoryPanel'

const MAX_ROWS = 200

/**
 * An internal/ops-style page, not part of the shopper storefront — there is
 * no real warehouse or supplier system behind this site, so this renders
 * forecasts over the synthetic sales/stock history (see
 * datasets/inventory/, training/inventory/). Gated behind Glass Mode for
 * the same reason /transactions is: a "reorder now" flag with no context
 * that it's simulated would be actively misleading. See
 * docs/subsystems/inventory.md.
 */
export function InventoryPage() {
  const glassMode = useGlassMode((s) => s.enabled)
  const { data } = useQuery({
    queryKey: ['inventory-forecasts'],
    queryFn: async () => {
      const [forecasts, manifest, products] = await Promise.all([
        loadInventoryForecasts(),
        loadInventoryManifest(),
        loadProducts(),
      ])
      return { forecasts, manifest, products }
    },
    enabled: glassMode,
  })

  const rows = useMemo(() => {
    if (!data) return []
    const productById = new Map(data.products.map((p) => [p.id, p]))
    return data.forecasts
      .map((f) => ({ forecast: f, product: productById.get(f.product_id) }))
      .sort((a, b) => a.forecast.days_of_supply - b.forecast.days_of_supply)
  }, [data])

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-semibold">Inventory (demo)</h1>
      <p className="mb-5 text-sm text-slate-500 dark:text-slate-400">
        An internal-style ops view over GlassCart's synthetic sales/stock history — there is no
        real warehouse behind this site, so nothing here reflects real inventory. See{' '}
        <Link to="/about" className="text-glass-600 hover:underline dark:text-glass-300">
          About this project
        </Link>
        .
      </p>

      {!glassMode && (
        <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
          Turn on <span className="font-medium text-glass-600 dark:text-glass-300">Glass Mode</span> above to
          see demand forecasts and reorder recommendations.
        </div>
      )}

      {glassMode && data && (
        <>
          <GlassInventoryPanel manifest={data.manifest!} />

          <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-900 dark:text-slate-400">
                <tr>
                  <th className="px-3 py-2">Product</th>
                  <th className="px-3 py-2">Stock</th>
                  <th className="px-3 py-2">Forecast/day</th>
                  <th className="px-3 py-2">Days of supply</th>
                  <th className="px-3 py-2">Reorder point</th>
                  <th className="px-3 py-2">Stockouts (90d)</th>
                  <th className="px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, MAX_ROWS).map(({ forecast: f, product }) => (
                  <tr key={f.product_id} className="border-t border-slate-100 dark:border-slate-800">
                    <td className="px-3 py-2">
                      <span className="font-mono text-xs text-slate-400">{f.product_id}</span>{' '}
                      {product ? (
                        <Link to={`/product/${product.id}`} className="hover:underline">
                          {product.title}
                        </Link>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td className="px-3 py-2">{f.current_stock}</td>
                    <td className="px-3 py-2">{f.avg_daily_forecast.toFixed(2)}</td>
                    <td className="px-3 py-2">{f.days_of_supply < 0 ? '∞' : `${f.days_of_supply}d`}</td>
                    <td className="px-3 py-2">{f.reorder_point.toFixed(1)}</td>
                    <td className="px-3 py-2">{f.stockout_days_observed}</td>
                    <td className="px-3 py-2">
                      {f.needs_reorder ? (
                        <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                          reorder
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">ok</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {rows.length > MAX_ROWS && (
            <p className="mt-2 text-xs text-slate-400">
              Showing the {MAX_ROWS} lowest days-of-supply of {rows.length} products.
            </p>
          )}
        </>
      )}
    </main>
  )
}
