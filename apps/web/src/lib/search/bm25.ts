/**
 * Pure-TypeScript BM25 (Okapi) implementation — runs entirely in the
 * browser, no server round-trip.
 *
 * See docs/research/search-and-retrieval.md §1 for the formula's origin
 * (Robertson & Zaragoza, 2009) and why `k1`/`b` are the two tunable
 * parameters. Both are re-exported from `config.ts` and surfaced verbatim
 * in Glass Mode rather than hidden inside this module.
 */
import { BM25_B, BM25_K1 } from './config'

const TOKEN_RE = /[a-z0-9]+/g

export function tokenize(text: string): string[] {
  return text.toLowerCase().match(TOKEN_RE) ?? []
}

export interface Bm25Index {
  score(queryTokens: string[]): Float64Array
}

/**
 * Builds an in-memory BM25 index over `docs` (already tokenized).
 * Cost is O(corpus size); fine for a catalog of a few thousand products.
 */
export function buildBm25Index(docs: string[][], k1 = BM25_K1, b = BM25_B): Bm25Index {
  const n = docs.length
  const docLengths = docs.map((d) => d.length)
  const avgDocLength = docLengths.reduce((a, b2) => a + b2, 0) / (n || 1)

  // document frequency per term
  const df = new Map<string, number>()
  const termFreqsByDoc: Map<string, number>[] = docs.map((doc) => {
    const tf = new Map<string, number>()
    for (const term of doc) tf.set(term, (tf.get(term) ?? 0) + 1)
    for (const term of tf.keys()) df.set(term, (df.get(term) ?? 0) + 1)
    return tf
  })

  const idf = new Map<string, number>()
  for (const [term, freq] of df.entries()) {
    // BM25 idf with the standard +1 smoothing to keep it non-negative.
    idf.set(term, Math.log(1 + (n - freq + 0.5) / (freq + 0.5)))
  }

  return {
    score(queryTokens: string[]): Float64Array {
      const scores = new Float64Array(n)
      const uniqueQueryTerms = Array.from(new Set(queryTokens))
      for (let i = 0; i < n; i++) {
        const tf = termFreqsByDoc[i]
        const dl = docLengths[i]
        let s = 0
        for (const term of uniqueQueryTerms) {
          const f = tf.get(term)
          if (!f) continue
          const termIdf = idf.get(term) ?? 0
          const numerator = f * (k1 + 1)
          const denominator = f + k1 * (1 - b + (b * dl) / avgDocLength)
          s += termIdf * (numerator / denominator)
        }
        scores[i] = s
      }
      return scores
    },
  }
}
