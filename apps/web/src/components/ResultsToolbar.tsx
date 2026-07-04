export interface SortOption<T extends string> {
  value: T
  label: string
}

export function ResultsToolbar<T extends string>({
  count,
  totalCount,
  sort,
  sortOptions,
  onSortChange,
}: {
  count: number
  /** When filters have narrowed the visible set, shows "N of totalCount results" instead of just "N results". */
  totalCount?: number
  sort: T
  sortOptions: SortOption<T>[]
  onSortChange: (value: T) => void
}) {
  return (
    <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-3 dark:border-slate-800">
      <p className="text-sm text-slate-500 dark:text-slate-400">
        {totalCount !== undefined && totalCount !== count ? (
          <>
            {count} of {totalCount} results
          </>
        ) : (
          <>{count} results</>
        )}
      </p>
      <label className="flex items-center gap-2 text-sm">
        <span className="text-slate-500 dark:text-slate-400">Sort by</span>
        <select
          value={sort}
          onChange={(e) => onSortChange(e.target.value as T)}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
        >
          {sortOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </label>
    </div>
  )
}
