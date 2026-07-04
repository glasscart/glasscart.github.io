import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Product } from '../lib/search/types'

export interface CartLine {
  product: Product
  quantity: number
}

interface CartState {
  lines: CartLine[]
  isOpen: boolean
  open: () => void
  close: () => void
  addItem: (product: Product, quantity?: number) => void
  removeItem: (productId: string) => void
  setQuantity: (productId: string, quantity: number) => void
  clear: () => void
}

/**
 * No checkout or payment flow exists (or is planned) — GlassCart is
 * static-first with no backend to hold an order. This store exists purely so
 * the storefront *feels* like commerce software (add-to-cart, running totals)
 * without implying a transaction actually happens anywhere.
 */
export const useCart = create<CartState>()(
  persist(
    (set) => ({
      lines: [],
      isOpen: false,
      open: () => set({ isOpen: true }),
      close: () => set({ isOpen: false }),
      addItem: (product, quantity = 1) =>
        set((s) => {
          const existing = s.lines.find((l) => l.product.id === product.id)
          if (existing) {
            return {
              lines: s.lines.map((l) =>
                l.product.id === product.id ? { ...l, quantity: l.quantity + quantity } : l,
              ),
              isOpen: true,
            }
          }
          return { lines: [...s.lines, { product, quantity }], isOpen: true }
        }),
      removeItem: (productId) => set((s) => ({ lines: s.lines.filter((l) => l.product.id !== productId) })),
      setQuantity: (productId, quantity) =>
        set((s) => ({
          lines: quantity <= 0
            ? s.lines.filter((l) => l.product.id !== productId)
            : s.lines.map((l) => (l.product.id === productId ? { ...l, quantity } : l)),
        })),
      clear: () => set({ lines: [] }),
    }),
    { name: 'glasscart:cart', partialize: (s) => ({ lines: s.lines }) },
  ),
)

export function cartCount(lines: CartLine[]): number {
  return lines.reduce((sum, l) => sum + l.quantity, 0)
}

export function cartSubtotal(lines: CartLine[]): number {
  return lines.reduce((sum, l) => sum + l.quantity * l.product.price, 0)
}
