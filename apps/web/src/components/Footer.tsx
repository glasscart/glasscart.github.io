import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer className="border-t border-slate-200 py-8 text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4">
        <span>© {new Date().getFullYear()} GlassCart</span>
        <div className="flex items-center gap-4">
          <Link to="/about" className="hover:text-slate-700 dark:hover:text-slate-200">
            About this project
          </Link>
          <Link to="/transactions" className="hover:text-slate-700 dark:hover:text-slate-200">
            Transactions (demo)
          </Link>
          <Link to="/inventory" className="hover:text-slate-700 dark:hover:text-slate-200">
            Inventory (demo)
          </Link>
          <a
            href="https://github.com/glasscart/glasscart.github.io"
            className="hover:text-slate-700 dark:hover:text-slate-200"
            target="_blank"
            rel="noreferrer"
          >
            GitHub
          </a>
        </div>
      </div>
    </footer>
  )
}
