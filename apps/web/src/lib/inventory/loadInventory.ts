/**
 * Loads the precomputed inventory forecast artifacts (see
 * training/inventory/forecast.py and models/inventory/MODEL_CARD.md).
 * Static, offline-computed content, fetched the same way reviews/pricing/
 * fraud are.
 */
import type { InventoryManifest, ProductForecast } from './types'

let forecastsPromise: Promise<ProductForecast[]> | null = null
let manifestPromise: Promise<InventoryManifest | null> | null = null

const dataUrl = (path: string) => `${import.meta.env.BASE_URL}data/${path}`

export function loadInventoryForecasts(): Promise<ProductForecast[]> {
  if (!forecastsPromise) {
    forecastsPromise = fetch(dataUrl('inventory_forecasts.json')).then((r) => {
      if (!r.ok) throw new Error(`Failed to load inventory_forecasts.json: ${r.status}`)
      return r.json()
    })
  }
  return forecastsPromise
}

export function loadInventoryManifest(): Promise<InventoryManifest | null> {
  if (!manifestPromise) {
    manifestPromise = fetch(dataUrl('inventory_manifest.json'))
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null)
  }
  return manifestPromise
}
