/**
 * Loads the precomputed review data + analysis artifacts (see
 * training/reviews/analyze.py and models/reviews/MODEL_CARD.md). Unlike
 * search/recommendations/ranking, there's no live client-side inference
 * here — sentiment/aspect/fake-review scoring already happened offline,
 * so this is just static JSON fetching, the same pattern
 * apps/web/src/lib/search/loadData.ts uses for the product catalog itself.
 */
import type { ProductReviewSummary, Review, ReviewAnalysis, ReviewsManifest } from './types'

let reviewsPromise: Promise<Review[]> | null = null
let analysisPromise: Promise<ReviewAnalysis[]> | null = null
let summariesPromise: Promise<ProductReviewSummary[]> | null = null
let manifestPromise: Promise<ReviewsManifest | null> | null = null

const dataUrl = (path: string) => `${import.meta.env.BASE_URL}data/${path}`

export function loadReviews(): Promise<Review[]> {
  if (!reviewsPromise) {
    reviewsPromise = fetch(dataUrl('reviews.json')).then((r) => {
      if (!r.ok) throw new Error(`Failed to load reviews.json: ${r.status}`)
      return r.json()
    })
  }
  return reviewsPromise
}

export function loadReviewAnalysis(): Promise<ReviewAnalysis[]> {
  if (!analysisPromise) {
    analysisPromise = fetch(dataUrl('review_analysis.json')).then((r) => {
      if (!r.ok) throw new Error(`Failed to load review_analysis.json: ${r.status}`)
      return r.json()
    })
  }
  return analysisPromise
}

export function loadProductReviewSummaries(): Promise<ProductReviewSummary[]> {
  if (!summariesPromise) {
    summariesPromise = fetch(dataUrl('product_review_summary.json')).then((r) => {
      if (!r.ok) throw new Error(`Failed to load product_review_summary.json: ${r.status}`)
      return r.json()
    })
  }
  return summariesPromise
}

export function loadReviewsManifest(): Promise<ReviewsManifest | null> {
  if (!manifestPromise) {
    manifestPromise = fetch(dataUrl('reviews_manifest.json'))
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null)
  }
  return manifestPromise
}
