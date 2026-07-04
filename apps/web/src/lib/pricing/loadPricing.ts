/**
 * Loads the precomputed pricing-simulation artifacts (see
 * training/pricing/simulate.py and models/pricing/MODEL_CARD.md). Like
 * reviews, this is static, offline-computed content — no client-side
 * inference — fetched the same way apps/web/src/lib/search/loadData.ts
 * fetches the product catalog itself.
 */
import type { PricingManifest, PricingRecommendation } from './types'

let recommendationsPromise: Promise<PricingRecommendation[]> | null = null
let manifestPromise: Promise<PricingManifest | null> | null = null

const dataUrl = (path: string) => `${import.meta.env.BASE_URL}data/${path}`

export function loadPricingRecommendations(): Promise<PricingRecommendation[]> {
  if (!recommendationsPromise) {
    recommendationsPromise = fetch(dataUrl('pricing_recommendations.json')).then((r) => {
      if (!r.ok) throw new Error(`Failed to load pricing_recommendations.json: ${r.status}`)
      return r.json()
    })
  }
  return recommendationsPromise
}

export function loadPricingManifest(): Promise<PricingManifest | null> {
  if (!manifestPromise) {
    manifestPromise = fetch(dataUrl('pricing_manifest.json'))
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null)
  }
  return manifestPromise
}
