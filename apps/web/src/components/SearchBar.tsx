interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  isLoading?: boolean
}

export function SearchBar({ value, onChange, isLoading }: SearchBarProps) {
  return (
    <div className="relative">
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search the catalog — try “cozy running gear” or “eco kitchen”…"
        className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-base outline-none focus:border-glass-500 focus:ring-2 focus:ring-glass-500/30 dark:border-slate-700 dark:bg-slate-900"
        autoFocus
      />
      {isLoading && (
        <span className="absolute right-4 top-1/2 -translate-y-1/2 text-xs text-slate-400">
          searching…
        </span>
      )}
    </div>
  )
}
