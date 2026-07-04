import { useState } from 'react'
import type { Product } from '../lib/search/types'
import { categoryByLabel } from '../lib/categories'
import { useGlassMode } from '../store/glassMode'

/** Cheap deterministic string hash so the same product always renders the same pattern. */
function hash(input: string): number {
  let h = 0
  for (let i = 0; i < input.length; i++) {
    h = (h * 31 + input.charCodeAt(i)) >>> 0
  }
  return h
}

const dataUrl = (path: string) => `${import.meta.env.BASE_URL}data/${path}`

function ProceduralPlaceholder({ product, className }: { product: Product; className?: string }) {
  const meta = categoryByLabel(product.category)
  const seed = hash(product.id)
  const rotation = seed % 360
  const scale = 1 + ((seed >> 8) % 40) / 100

  return (
    <div
      className={[
        'relative flex items-center justify-center overflow-hidden bg-gradient-to-br',
        meta?.gradient ?? 'from-slate-400 to-slate-600',
        className ?? '',
      ].join(' ')}
    >
      <div
        aria-hidden
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage:
            'repeating-linear-gradient(45deg, rgba(255,255,255,0.35) 0 2px, transparent 2px 18px)',
          transform: `rotate(${rotation}deg) scale(${scale})`,
        }}
      />
      <span className="relative text-4xl drop-shadow-sm" role="img" aria-label={product.category}>
        {meta?.icon ?? '🛍️'}
      </span>
    </div>
  )
}

function GlassBadge({ text }: { text: string }) {
  return (
    <span
      title={text}
      className="absolute bottom-1.5 right-1.5 z-10 rounded-full bg-glass-500/90 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-white shadow-sm"
    >
      AI
    </span>
  )
}

/**
 * Renders the product's generated image if one exists (it currently never
 * does — the diffusion pipeline in training/product_images/ was built and
 * benchmarked but its output wasn't judged good enough to ship, see
 * models/product-images/MODEL_CARD.md and docs/roadmap.md — this fallback
 * path is kept so the site picks images up automatically if that pipeline
 * is ever revisited and its output committed to datasets/products/images/).
 * Until then every product renders the deterministic procedural
 * placeholder below — a category-tinted gradient, seeded purely from the
 * product id/category. Glass Mode only badges the image as "AI" when a
 * real generated image is actually showing, never the procedural one.
 */
export function ProductImage({ product, className }: { product: Product; className?: string }) {
  const [imageFailed, setImageFailed] = useState(false)
  const glassMode = useGlassMode((s) => s.enabled)

  // The caller's sizing classes (aspect ratio, dimensions, flex/grid behavior
  // like `shrink-0`) go on this wrapper, not the <img> — a nested element
  // can't retroactively size a flex/grid item from the inside.
  return (
    <div className={['relative overflow-hidden', className ?? ''].join(' ')}>
      {imageFailed ? (
        <ProceduralPlaceholder product={product} className="absolute inset-0" />
      ) : (
        <img
          src={dataUrl(`images/${product.id}.png`)}
          alt={product.title}
          onError={() => setImageFailed(true)}
          className="absolute inset-0 h-full w-full bg-slate-100 object-cover dark:bg-slate-800"
        />
      )}
      {glassMode && !imageFailed && (
        <GlassBadge text="AI-generated placeholder (Stable Diffusion 1.5, 512px, 25 steps, INT8-quantized) — not real product photography. See models/product-images/MODEL_CARD.md." />
      )}
    </div>
  )
}
