import { useGlassMode } from '../store/glassMode'

export function GlassModeToggle() {
  const enabled = useGlassMode((s) => s.enabled)
  const toggle = useGlassMode((s) => s.toggle)

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={enabled}
      title="Glass Mode exposes the model, latency, and score breakdown behind every AI-assisted result on this page."
      className={[
        'flex items-center gap-2 rounded-full border px-3 py-1.5 text-sm font-medium transition-colors',
        enabled
          ? 'border-glass-500 bg-glass-500/10 text-glass-600 dark:text-glass-300'
          : 'border-slate-300 text-slate-600 hover:border-slate-400 dark:border-slate-700 dark:text-slate-300 dark:hover:border-slate-600',
      ].join(' ')}
    >
      <span
        className={[
          'inline-block h-2 w-2 rounded-full transition-colors',
          enabled ? 'bg-glass-500' : 'bg-slate-400 dark:bg-slate-600',
        ].join(' ')}
      />
      Glass Mode
    </button>
  )
}
