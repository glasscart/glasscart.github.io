import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { loadFraudManifest, loadFraudScores, loadTransactions } from '../lib/fraud/loadFraud'
import { useGlassMode } from '../store/glassMode'
import { GlassFraudPanel } from '../components/GlassFraudPanel'

const MAX_ROWS = 200

/**
 * An internal/ops-style page, not part of the shopper storefront — there is
 * no real checkout on this site, so this renders the synthetic transaction
 * log (see datasets/transactions/) with fraud scores (training/fraud/).
 * Gated behind Glass Mode: showing a fraud score with no explanation of
 * what it means or how synthetic the underlying data is would be far more
 * misleading than showing nothing. See docs/subsystems/fraud.md.
 */
export function TransactionsPage() {
  const glassMode = useGlassMode((s) => s.enabled)
  const { data } = useQuery({
    queryKey: ['transactions-fraud'],
    queryFn: async () => {
      const [transactions, scores, manifest] = await Promise.all([
        loadTransactions(),
        loadFraudScores(),
        loadFraudManifest(),
      ])
      return { transactions, scores, manifest }
    },
    enabled: glassMode,
  })

  const rows = useMemo(() => {
    if (!data) return []
    const scoreById = new Map(data.scores.map((s) => [s.transaction_id, s]))
    return data.transactions
      .map((t) => ({ transaction: t, score: scoreById.get(t.id) }))
      .sort((a, b) => (b.score?.fraud_score ?? 0) - (a.score?.fraud_score ?? 0))
  }, [data])

  return (
    <main className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="mb-1 text-2xl font-semibold">Transactions (demo)</h1>
      <p className="mb-5 text-sm text-slate-500 dark:text-slate-400">
        An internal-style ops view over GlassCart's synthetic transaction log — there is no real
        checkout on this site, so nothing here represents a real purchase. See{' '}
        <Link to="/about" className="text-glass-600 hover:underline dark:text-glass-300">
          About this project
        </Link>
        .
      </p>

      {!glassMode && (
        <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
          Turn on <span className="font-medium text-glass-600 dark:text-glass-300">Glass Mode</span> above to
          see the transaction log and fraud-detection scores.
        </div>
      )}

      {glassMode && data && (
        <>
          <GlassFraudPanel manifest={data.manifest!} />

          <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500 dark:bg-slate-900 dark:text-slate-400">
                <tr>
                  <th className="px-3 py-2">Transaction</th>
                  <th className="px-3 py-2">Buyer</th>
                  <th className="px-3 py-2">Amount</th>
                  <th className="px-3 py-2">Regions</th>
                  <th className="px-3 py-2">Account age</th>
                  <th className="px-3 py-2">Fraud score</th>
                  <th className="px-3 py-2">Ground truth</th>
                </tr>
              </thead>
              <tbody>
                {rows.slice(0, MAX_ROWS).map(({ transaction: t, score }) => (
                  <tr key={t.id} className="border-t border-slate-100 dark:border-slate-800">
                    <td className="px-3 py-2 font-mono text-xs">{t.id}</td>
                    <td className="px-3 py-2 font-mono text-xs">{t.buyer_id}</td>
                    <td className="px-3 py-2">${t.amount.toFixed(2)}</td>
                    <td className="px-3 py-2 text-xs">
                      {t.shipping_region === t.billing_region
                        ? t.shipping_region
                        : `${t.billing_region} → ${t.shipping_region}`}
                    </td>
                    <td className="px-3 py-2 text-xs">{t.buyer_account_age_days}d</td>
                    <td className="px-3 py-2">
                      {score && (
                        <span
                          className={
                            score.likely_fraud
                              ? 'rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-950 dark:text-red-300'
                              : 'text-xs text-slate-500 dark:text-slate-400'
                          }
                        >
                          {score.fraud_score.toFixed(2)}
                          {score.likely_fraud ? ' flagged' : ''}
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-400">
                      {t.is_fraud_synthetic ? 'synthetic fraud' : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {rows.length > MAX_ROWS && (
            <p className="mt-2 text-xs text-slate-400">
              Showing the {MAX_ROWS} highest-scored of {rows.length} transactions.
            </p>
          )}
        </>
      )}
    </main>
  )
}
