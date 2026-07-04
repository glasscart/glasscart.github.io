/**
 * Loads the precomputed transaction log + fraud-score artifacts (see
 * training/fraud/detect.py and models/fraud/MODEL_CARD.md). Static,
 * offline-computed content, fetched the same way reviews/pricing are.
 */
import type { FraudManifest, FraudScore, Transaction } from './types'

let transactionsPromise: Promise<Transaction[]> | null = null
let scoresPromise: Promise<FraudScore[]> | null = null
let manifestPromise: Promise<FraudManifest | null> | null = null

const dataUrl = (path: string) => `${import.meta.env.BASE_URL}data/${path}`

export function loadTransactions(): Promise<Transaction[]> {
  if (!transactionsPromise) {
    transactionsPromise = fetch(dataUrl('transactions.json')).then((r) => {
      if (!r.ok) throw new Error(`Failed to load transactions.json: ${r.status}`)
      return r.json()
    })
  }
  return transactionsPromise
}

export function loadFraudScores(): Promise<FraudScore[]> {
  if (!scoresPromise) {
    scoresPromise = fetch(dataUrl('fraud_scores.json')).then((r) => {
      if (!r.ok) throw new Error(`Failed to load fraud_scores.json: ${r.status}`)
      return r.json()
    })
  }
  return scoresPromise
}

export function loadFraudManifest(): Promise<FraudManifest | null> {
  if (!manifestPromise) {
    manifestPromise = fetch(dataUrl('fraud_manifest.json'))
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null)
  }
  return manifestPromise
}
