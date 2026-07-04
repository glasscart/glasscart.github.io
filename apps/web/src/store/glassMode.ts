import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface GlassModeState {
  enabled: boolean
  toggle: () => void
  setEnabled: (enabled: boolean) => void
}

/**
 * Global "Glass Mode" switch. When on, every AI-assisted UI element exposes
 * its diagnostics (model, latency, score breakdown, limitations) instead of
 * just rendering a result. Persisted so a reader's preference survives a
 * refresh.
 */
export const useGlassMode = create<GlassModeState>()(
  persist(
    (set) => ({
      enabled: false,
      toggle: () => set((s) => ({ enabled: !s.enabled })),
      setEnabled: (enabled) => set({ enabled }),
    }),
    { name: 'glasscart:glass-mode' },
  ),
)
