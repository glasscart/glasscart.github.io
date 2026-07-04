/**
 * Selects the active search provider. Defaults to the fully client-side
 * implementation (works standalone on GitHub Pages, no backend). Setting
 * `VITE_SEARCH_API_URL` at build time switches to the optional FastAPI
 * reference service instead — the same pluggable-provider pattern
 * GlassCart uses for optional LLM backends (Ollama/OpenAI/Anthropic).
 */
import { hybridSearch } from './hybrid'
import { createApiSearchProvider } from './apiProvider'
import type { SearchProvider } from './types'
import { DEFAULT_LIMIT, FUSION_ALPHA } from './config'

const apiBaseUrl = import.meta.env.VITE_SEARCH_API_URL as string | undefined

const clientProvider: SearchProvider = {
  name: 'client',
  search: (query, opts) => hybridSearch(query, opts?.limit ?? DEFAULT_LIMIT, opts?.alpha ?? FUSION_ALPHA),
}

export function getSearchProvider(): SearchProvider {
  if (apiBaseUrl) return createApiSearchProvider(apiBaseUrl)
  return clientProvider
}
