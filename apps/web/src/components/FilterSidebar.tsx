import type { ProductFacets, ProductFilters } from '../hooks/useProductFilters'
import { EMPTY_FILTERS } from '../hooks/useProductFilters'

const RATING_OPTIONS = [4, 3, 2] as const

export function FilterSidebar({
  facets,
  filters,
  onChange,
}: {
  facets: ProductFacets
  filters: ProductFilters
  onChange: (filters: ProductFilters) => void
}) {
  const hasActiveFilters =
    filters.minRating > 0 || filters.maxPrice !== null || filters.brands.length > 0 || filters.materials.length > 0

  function toggle(list: string[], value: string): string[] {
    return list.includes(value) ? list.filter((v) => v !== value) : [...list, value]
  }

  return (
    <aside className="w-full shrink-0 space-y-6 md:w-56">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold">Filters</h2>
        {hasActiveFilters && (
          <button
            type="button"
            onClick={() => onChange(EMPTY_FILTERS)}
            className="text-xs text-glass-600 hover:underline dark:text-glass-300"
          >
            Clear all
          </button>
        )}
      </div>

      <div>
        <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">Customer rating</h3>
        <div className="space-y-1.5">
          {RATING_OPTIONS.map((r) => (
            <label key={r} className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="radio"
                name="min-rating"
                checked={filters.minRating === r}
                onChange={() => onChange({ ...filters, minRating: r })}
                className="accent-glass-500"
              />
              <span className="text-amber-400" aria-hidden>
                {'★'.repeat(r)}
                <span className="text-slate-300 dark:text-slate-700">{'★'.repeat(5 - r)}</span>
              </span>
              <span className="text-slate-600 dark:text-slate-400">& up</span>
            </label>
          ))}
          <label className="flex cursor-pointer items-center gap-2 text-sm">
            <input
              type="radio"
              name="min-rating"
              checked={filters.minRating === 0}
              onChange={() => onChange({ ...filters, minRating: 0 })}
              className="accent-glass-500"
            />
            <span className="text-slate-600 dark:text-slate-400">Any rating</span>
          </label>
        </div>
      </div>

      <div>
        <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">Max price</h3>
        <div className="flex items-center gap-2">
          <input
            type="range"
            min={0}
            max={facets.priceMax}
            step={1}
            value={filters.maxPrice ?? facets.priceMax}
            onChange={(e) => onChange({ ...filters, maxPrice: Number(e.target.value) })}
            className="w-full accent-glass-500"
          />
        </div>
        <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Up to ${(filters.maxPrice ?? facets.priceMax).toFixed(0)}
        </div>
      </div>

      {facets.brands.length > 1 && (
        <div>
          <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">Brand</h3>
          <div className="max-h-40 space-y-1.5 overflow-y-auto pr-1">
            {facets.brands.map((brand) => (
              <label key={brand} className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={filters.brands.includes(brand)}
                  onChange={() => onChange({ ...filters, brands: toggle(filters.brands, brand) })}
                  className="accent-glass-500"
                />
                <span className="text-slate-600 dark:text-slate-400">{brand}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {facets.materials.length > 1 && (
        <div>
          <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">Material</h3>
          <div className="max-h-40 space-y-1.5 overflow-y-auto pr-1">
            {facets.materials.map((material) => (
              <label key={material} className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={filters.materials.includes(material)}
                  onChange={() => onChange({ ...filters, materials: toggle(filters.materials, material) })}
                  className="accent-glass-500"
                />
                <span className="text-slate-600 dark:text-slate-400">{material}</span>
              </label>
            ))}
          </div>
        </div>
      )}
    </aside>
  )
}
