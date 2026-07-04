/**
 * Static category metadata (icon + accent) for the 10 fixed categories in the
 * synthetic catalog (see datasets/products/generate.py). Kept as a lookup
 * rather than derived from the data so icons/colors stay stable across
 * dataset regenerations.
 */
export interface CategoryMeta {
  slug: string
  label: string
  icon: string
  gradient: string
}

const RAW: Array<[string, string, string]> = [
  ['Electronics', '🎧', 'from-sky-400 to-blue-600'],
  ['Home & Kitchen', '🏠', 'from-amber-400 to-orange-600'],
  ['Books', '📚', 'from-violet-400 to-purple-600'],
  ['Clothing', '👕', 'from-pink-400 to-rose-600'],
  ['Sports & Outdoors', '🏕️', 'from-emerald-400 to-green-600'],
  ['Beauty', '💄', 'from-fuchsia-400 to-pink-600'],
  ['Toys', '🧸', 'from-yellow-400 to-amber-600'],
  ['Grocery', '🛒', 'from-lime-400 to-green-600'],
  ['Office Supplies', '🖇️', 'from-slate-400 to-slate-600'],
  ['Pet Supplies', '🐾', 'from-teal-400 to-cyan-600'],
]

export const CATEGORIES: CategoryMeta[] = RAW.map(([label, icon, gradient]) => ({
  slug: slugify(label),
  label,
  icon,
  gradient,
}))

const BY_LABEL = new Map(CATEGORIES.map((c) => [c.label, c]))
const BY_SLUG = new Map(CATEGORIES.map((c) => [c.slug, c]))

export function slugify(label: string): string {
  return label.toLowerCase().replace(/&/g, 'and').replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
}

export function categoryByLabel(label: string): CategoryMeta | undefined {
  return BY_LABEL.get(label)
}

export function categoryBySlug(slug: string): CategoryMeta | undefined {
  return BY_SLUG.get(slug)
}
