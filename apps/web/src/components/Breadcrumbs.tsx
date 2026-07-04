import { Link } from 'react-router-dom'

export interface Crumb {
  label: string
  to?: string
}

/** Shared breadcrumb trail — the last crumb is always the current page (no link). */
export function Breadcrumbs({ items }: { items: Crumb[] }) {
  return (
    <nav aria-label="Breadcrumb" className="mb-6 text-xs text-slate-500 dark:text-slate-400">
      {items.map((item, i) => (
        <span key={i}>
          {i > 0 && ' / '}
          {item.to ? (
            <Link to={item.to} className="hover:underline">
              {item.label}
            </Link>
          ) : (
            <span className="text-slate-700 dark:text-slate-300">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  )
}
