/**
 * Second-stage re-ranking layered on top of search and recommendation
 * candidates: business-rule boosts (rating, popularity) plus
 * diversification (down-weighting near-duplicate products so they don't
 * crowd a result page). This is deliberately not a learned ranker —
 * GlassCart has no click/purchase logs to train one on (same reason
 * recommendations are content-based, see docs/research/recommendations.md
 * §3) — it's transparent, hand-set business logic, which Glass Mode shows
 * as a literal per-item breakdown rather than a single opaque score.
 *
 * Diversification matters specifically because the product dataset
 * generator *intentionally* creates near-duplicate products (same noun,
 * different adjective/material — see datasets/products/DATASET_CARD.md)
 * to be realistic. Without it, a result page can be dominated by minor
 * variants of the same base product.
 *
 * See docs/research/ranking.md and docs/subsystems/ranking.md.
 */
import type { Product } from '../search/types'

export interface RankableCandidate {
  product: Product
  baseScore: number
}

export interface RankedItem {
  product: Product
  baseScore: number
  ratingBoost: number
  popularityBoost: number
  diversityPenalty: number
  finalScore: number
}

export interface RankingWeights {
  ratingWeight: number
  popularityWeight: number
  diversityWeight: number
}

export interface RankingExplanation extends RankingWeights {
  whyAiWasUsed: string
  diversityKey: string
  candidatePoolSize: number
  timingMs: number
  limitations: string[]
}

export interface RankingOutcome {
  items: RankedItem[]
  glass: RankingExplanation
}

export const SEARCH_RANKING_WEIGHTS: RankingWeights = {
  ratingWeight: 0.05,
  popularityWeight: 0.05,
  diversityWeight: 0.15,
}

export const RECOMMENDATION_RANKING_WEIGHTS: RankingWeights = {
  // Recommendations are already a similarity ranking; boosting by rating/
  // popularity here would trade away genuine similarity for generic
  // "popular items," which isn't the point of a similar-products list. Only
  // diversification is applied.
  ratingWeight: 0,
  popularityWeight: 0,
  diversityWeight: 0.15,
}

const WHY_AI_WAS_USED =
  'Results are re-scored by explicit, named business rules — not a learned model — because GlassCart has no interaction data to train a ranker on. Every adjustment below is a documented constant, not a black box.'

const LIMITATIONS = [
  'Not a learned ranker: weights are hand-set constants, not fit to any measured outcome (there is no interaction data to fit them against).',
  'Diversity key (category + first word of title) is a heuristic proxy for "near-duplicate," not a true duplicate detector — it can both miss real near-duplicates and flag genuinely distinct products that happen to share a first word.',
  'Popularity boost saturates at a fixed assumed maximum rating_count (4200, the dataset generator\'s own upper bound) rather than a measured distribution.',
]

// log-scaled and normalized against the dataset generator's own max
// rating_count (see DATASET_CARD.md's schema table), so a handful of very
// popular items don't saturate the boost for everyone else.
const MAX_RATING_COUNT = 4200

function popularityScore(ratingCount: number): number {
  return Math.min(1, Math.log10(ratingCount + 1) / Math.log10(MAX_RATING_COUNT + 1))
}

function diversityKey(product: Product): string {
  return `${product.category}::${product.title.split(' ')[0].toLowerCase()}`
}

/**
 * Re-ranks `candidates` (already sorted or not — order in is irrelevant)
 * down to `limit` items, applying business-rule boosts and greedy
 * diversification. Diversification is applied last and looks at the
 * *whole* candidate pool, not just the top `limit` by base score, so it
 * can actually swap in a diverse alternative rather than just re-ordering
 * a pool that was already truncated to near-duplicates.
 */
export function rerank(candidates: RankableCandidate[], limit: number, weights: RankingWeights): RankingOutcome {
  const t0 = performance.now()
  const { ratingWeight, popularityWeight, diversityWeight } = weights

  const scored: RankedItem[] = candidates.map((c) => {
    const ratingBoost = ratingWeight * ((c.product.rating - 1) / 4)
    const popularityBoost = popularityWeight * popularityScore(c.product.rating_count)
    return {
      product: c.product,
      baseScore: c.baseScore,
      ratingBoost,
      popularityBoost,
      diversityPenalty: 0,
      finalScore: c.baseScore + ratingBoost + popularityBoost,
    }
  })

  const seenCounts = new Map<string, number>()
  const remaining = [...scored]
  const result: RankedItem[] = []

  while (remaining.length > 0 && result.length < limit) {
    for (const r of remaining) {
      const seen = seenCounts.get(diversityKey(r.product)) ?? 0
      r.diversityPenalty = diversityWeight * seen
    }
    remaining.sort((a, b) => b.finalScore - b.diversityPenalty - (a.finalScore - a.diversityPenalty))
    const next = remaining.shift()
    if (!next) break
    seenCounts.set(diversityKey(next.product), (seenCounts.get(diversityKey(next.product)) ?? 0) + 1)
    result.push(next)
  }

  return {
    items: result,
    glass: {
      whyAiWasUsed: WHY_AI_WAS_USED,
      ...weights,
      diversityKey: 'category + first word of title',
      candidatePoolSize: candidates.length,
      timingMs: performance.now() - t0,
      limitations: LIMITATIONS,
    },
  }
}
