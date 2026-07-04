/**
 * Loads and inverts datasets/products/images/ATTRIBUTION.json (synced to
 * public/data/image_attribution.json — see fetch_stock_photos.py's module
 * docstring for how the underlying photos were sourced and hand-reviewed).
 * The file on disk is keyed by noun ("Smart Watch") with a `product_ids`
 * array, since one photo is reused across every combinatorial variant of
 * that noun; the frontend only ever looks things up by product id, so this
 * inverts it once into a per-product map. CC-BY/CC-BY-SA/public-domain
 * photos require on-site attribution — this is what ProductImage.tsx's
 * Glass Mode badge reads from.
 */
import type { ImageAttribution } from './types'

interface RawAttributionEntry {
  commons_title: string
  source_url: string
  artist: string
  license: string
  license_url: string
  extension: string
  product_ids: string[]
}

let attributionPromise: Promise<Map<string, ImageAttribution>> | null = null

const dataUrl = (path: string) => `${import.meta.env.BASE_URL}data/${path}`

export function loadImageAttribution(): Promise<Map<string, ImageAttribution>> {
  if (!attributionPromise) {
    attributionPromise = fetch(dataUrl('image_attribution.json'))
      .then((r) => (r.ok ? r.json() : {}))
      .catch(() => ({}))
      .then((raw: Record<string, RawAttributionEntry>) => {
        const map = new Map<string, ImageAttribution>()
        for (const entry of Object.values(raw)) {
          for (const productId of entry.product_ids) {
            map.set(productId, {
              commonsTitle: entry.commons_title,
              sourceUrl: entry.source_url,
              artist: entry.artist,
              license: entry.license,
              licenseUrl: entry.license_url,
              extension: entry.extension,
            })
          }
        }
        return map
      })
  }
  return attributionPromise
}
