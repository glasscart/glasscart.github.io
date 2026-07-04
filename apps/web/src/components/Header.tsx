import { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { GlassModeToggle } from './GlassModeToggle'
import { useCart, cartCount } from '../store/cart'
import { CATEGORIES } from '../lib/categories'

export function Header() {
  const navigate = useNavigate()
  const [headerQuery, setHeaderQuery] = useState('')
  const categoriesRef = useRef<HTMLDetailsElement>(null)
  const lines = useCart((s) => s.lines)
  const openCart = useCart((s) => s.open)
  const count = cartCount(lines)

  function submitSearch(e: React.FormEvent) {
    e.preventDefault()
    navigate(`/search?q=${encodeURIComponent(headerQuery)}`)
  }

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-3">
        <Link to="/" className="flex items-center">
          <img src={`${import.meta.env.BASE_URL}logo.svg`} alt="GlassCart" className="h-7 w-auto" />
        </Link>

        <nav className="hidden items-center gap-4 text-sm font-medium text-slate-600 md:flex dark:text-slate-300">
          <Link to="/" className="hover:text-slate-900 dark:hover:text-white">
            Home
          </Link>
          <Link to="/search" className="hover:text-slate-900 dark:hover:text-white">
            Shop all
          </Link>
          <details ref={categoriesRef} className="relative">
            <summary className="flex cursor-pointer list-none items-center gap-1 hover:text-slate-900 [&::-webkit-details-marker]:hidden dark:hover:text-white">
              Categories
              <span aria-hidden className="text-xs">▾</span>
            </summary>
            <div className="absolute left-0 top-full z-50 grid w-64 grid-cols-1 gap-0.5 rounded-xl border border-slate-200 bg-white p-2 shadow-lg dark:border-slate-800 dark:bg-slate-900">
              {CATEGORIES.map((c) => (
                <Link
                  key={c.slug}
                  to={`/category/${c.slug}`}
                  onClick={() => categoriesRef.current?.removeAttribute('open')}
                  className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <span aria-hidden>{c.icon}</span> {c.label}
                </Link>
              ))}
            </div>
          </details>
        </nav>

        <form onSubmit={submitSearch} className="order-last w-full flex-1 sm:order-none sm:w-auto">
          <input
            type="search"
            value={headerQuery}
            onChange={(e) => setHeaderQuery(e.target.value)}
            placeholder="Search products…"
            className="w-full min-w-0 rounded-full border border-slate-300 bg-slate-50 px-4 py-1.5 text-sm outline-none focus:border-glass-500 focus:ring-2 focus:ring-glass-500/30 dark:border-slate-700 dark:bg-slate-900"
          />
        </form>

        <div className="ml-auto flex items-center gap-2 sm:ml-0">
          <GlassModeToggle />
          <button
            type="button"
            onClick={openCart}
            aria-label="Open cart"
            className="relative flex items-center gap-1.5 rounded-full border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-600 hover:border-slate-400 dark:border-slate-700 dark:text-slate-300 dark:hover:border-slate-600"
          >
            🛒
            <span className="hidden sm:inline">Cart</span>
            {count > 0 && (
              <span className="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-glass-500 px-1 text-[10px] font-semibold text-white">
                {count}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  )
}
