import { useMemo, useState } from 'react'
import type { Product } from '../lib/search/types'

export interface ProductFilters {
  minRating: number
  maxPrice: number | null
  brands: string[]
  materials: string[]
}

export const EMPTY_FILTERS: ProductFilters = { minRating: 0, maxPrice: null, brands: [], materials: [] }

export interface ProductFacets {
  brands: string[]
  materials: string[]
  priceMax: number
}

/**
 * Client-side faceted filtering over whatever product list the caller
 * already has (a category's products, or a search page's ranked
 * candidates) — facet values (brands/materials/price ceiling) are derived
 * from that same list, not the whole catalog, so a facet never offers an
 * option that would filter every visible result down to zero.
 */
export function useProductFilters(products: Product[]) {
  const [filters, setFilters] = useState<ProductFilters>(EMPTY_FILTERS)

  const facets = useMemo<ProductFacets>(() => {
    const brands = new Set<string>()
    const materials = new Set<string>()
    let priceMax = 0
    for (const p of products) {
      brands.add(p.brand)
      materials.add(p.material)
      if (p.price > priceMax) priceMax = p.price
    }
    return { brands: [...brands].sort(), materials: [...materials].sort(), priceMax: Math.ceil(priceMax) }
  }, [products])

  const filtered = useMemo(() => {
    return products.filter((p) => {
      if (p.rating < filters.minRating) return false
      if (filters.maxPrice !== null && p.price > filters.maxPrice) return false
      if (filters.brands.length > 0 && !filters.brands.includes(p.brand)) return false
      if (filters.materials.length > 0 && !filters.materials.includes(p.material)) return false
      return true
    })
  }, [products, filters])

  return { filtered, filters, setFilters, facets }
}
