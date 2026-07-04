import { cartSubtotal, useCart } from '../store/cart'
import { ProductImage } from './ProductImage'

export function CartDrawer() {
  const isOpen = useCart((s) => s.isOpen)
  const lines = useCart((s) => s.lines)
  const close = useCart((s) => s.close)
  const setQuantity = useCart((s) => s.setQuantity)
  const removeItem = useCart((s) => s.removeItem)

  if (!isOpen) return null

  const subtotal = cartSubtotal(lines)

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      <button
        type="button"
        aria-label="Close cart"
        className="absolute inset-0 bg-slate-950/40"
        onClick={close}
      />
      <div className="relative flex h-full w-full max-w-sm flex-col bg-white shadow-xl dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-4 dark:border-slate-800">
          <h2 className="text-lg font-semibold">Your cart</h2>
          <button
            type="button"
            onClick={close}
            className="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4">
          {lines.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">Your cart is empty.</p>
          ) : (
            <ul className="space-y-4">
              {lines.map((line) => (
                <li key={line.product.id} className="flex gap-3">
                  <ProductImage product={line.product} className="h-16 w-16 shrink-0 rounded-lg" />
                  <div className="flex flex-1 flex-col">
                    <span className="line-clamp-1 text-sm font-medium">{line.product.title}</span>
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      ${line.product.price.toFixed(2)}
                    </span>
                    <div className="mt-1 flex items-center gap-2">
                      <select
                        aria-label={`Quantity for ${line.product.title}`}
                        value={line.quantity}
                        onChange={(e) => setQuantity(line.product.id, Number(e.target.value))}
                        className="rounded-md border border-slate-300 bg-white px-1.5 py-0.5 text-xs dark:border-slate-700 dark:bg-slate-900"
                      >
                        {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                          <option key={n} value={n}>
                            {n}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() => removeItem(line.product.id)}
                        className="text-xs text-slate-400 hover:text-red-500"
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                  <span className="text-sm font-semibold">
                    ${(line.product.price * line.quantity).toFixed(2)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="border-t border-slate-200 px-4 py-4 dark:border-slate-800">
          <div className="mb-3 flex items-center justify-between text-sm font-medium">
            <span>Subtotal</span>
            <span>${subtotal.toFixed(2)}</span>
          </div>
          <button
            type="button"
            disabled={lines.length === 0}
            title="GlassCart is a static demo with no backend — there is no real checkout."
            className="w-full rounded-xl bg-slate-900 py-2.5 text-sm font-medium text-white transition-colors hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-200"
          >
            Checkout (demo only)
          </button>
        </div>
      </div>
    </div>
  )
}
