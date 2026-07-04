import { GlassModeToggle } from './GlassModeToggle'

export function Header() {
  return (
    <header className="border-b border-slate-200 dark:border-slate-800">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
        <div>
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-semibold tracking-tight">GlassCart</span>
            <span className="hidden text-xs text-slate-500 sm:inline">AI-first. AI-transparent.</span>
          </div>
        </div>
        <GlassModeToggle />
      </div>
    </header>
  )
}
