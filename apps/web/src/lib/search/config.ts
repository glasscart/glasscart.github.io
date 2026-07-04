/**
 * Canonical hybrid search constants. Mirrors `services/search/app/config.py`
 * so the client-side and server-side implementations are two independent
 * renderings of the same documented algorithm — see
 * docs/research/search-and-retrieval.md.
 */

export const EMBEDDING_MODEL_NAME = 'Xenova/all-MiniLM-L6-v2'
export const EMBEDDING_MODEL_NAME_OFFLINE = 'sentence-transformers/all-MiniLM-L6-v2'

// BM25 (Robertson & Zaragoza, 2009)
export const BM25_K1 = 1.5
export const BM25_B = 0.75

// Hybrid fusion (linear combination)
export const FUSION_ALPHA = 0.5

export const DEFAULT_LIMIT = 12

export const LIMITATIONS = [
  'Synthetic, templated catalog — lexical diversity is lower than a real marketplace.',
  'all-MiniLM-L6-v2 is English-only and not fine-tuned on e-commerce data.',
  'Static index: newly added products require rebuilding the embedding artifact.',
]

export const WHY_AI_WAS_USED =
  'Keyword matching alone misses paraphrases and synonyms; a pure embedding search misses exact brand/SKU matches. Hybrid search covers both.'
