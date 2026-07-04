import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { Product } from '../lib/search/types'
import { categoryByLabel } from '../lib/categories'
import { loadImageAttribution } from '../lib/images/loadImageAttribution'
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
      // No `relative` here: the caller always passes `absolute inset-0` (see
      // ProductImage below), and Tailwind's stylesheet order makes the
      // `relative` utility win over `absolute` when both classes land on the
      // same element regardless of HTML attribute order — silently
      // collapsing this div to its content's natural height instead of
      // filling its positioned parent. `absolute` alone still establishes a
      // positioning context for the decorative overlay div below.
      className={[
        'flex items-center justify-center overflow-hidden bg-gradient-to-br',
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

function GlassBadge({ label, text }: { label: string; text: string }) {
  return (
    <span
      title={text}
      className="absolute bottom-1.5 right-1.5 z-10 rounded-full bg-glass-500/90 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-white shadow-sm"
    >
      {label}
    </span>
  )
}

/**
 * Renders a real stock photo for the product's noun if one was sourced (see
 * datasets/products/fetch_stock_photos.py — CC0/CC-BY/CC-BY-SA/public-domain
 * photos from Wikimedia Commons, hand-reviewed one by one, ~15% of nouns
 * matched since most short/generic nouns don't have a suitable photo in a
 * general-purpose archive). One photo is reused across every combinatorial
 * variant of that noun (see the script's docstring for why), so this is
 * never the *exact* product, only representative of it — Glass Mode makes
 * that explicit via the attribution badge below rather than passing it off
 * as a real product photo. Every product without a sourced photo (the
 * large majority) renders the deterministic procedural placeholder — a
 * category-tinted gradient seeded purely from the product id/category. An
 * earlier AI image-generation pipeline (training/product_images/) was
 * built and benchmarked but its output wasn't judged good enough to ship
 * (see models/product-images/MODEL_CARD.md and docs/roadmap.md); it
 * produces no images checked into this repo.
 */
export function ProductImage({ product, className }: { product: Product; className?: string }) {
  const [imageFailed, setImageFailed] = useState(false)
  const glassMode = useGlassMode((s) => s.enabled)
  const { data: attributionMap } = useQuery({
    queryKey: ['image-attribution'],
    queryFn: loadImageAttribution,
    staleTime: Infinity,
  })
  const attribution = attributionMap?.get(product.id)

  // The caller's sizing classes (aspect ratio, dimensions, flex/grid behavior
  // like `shrink-0`) go on this wrapper, not the <img> — a nested element
  // can't retroactively size a flex/grid item from the inside.
  return (
    <div className={['relative overflow-hidden', className ?? ''].join(' ')}>
      {imageFailed || !attribution ? (
        <ProceduralPlaceholder product={product} className="absolute inset-0" />
      ) : (
        <img
          src={dataUrl(`images/${product.id}.${attribution.extension}`)}
          alt={product.title}
          onError={() => setImageFailed(true)}
          className="absolute inset-0 h-full w-full bg-slate-100 object-cover dark:bg-slate-800"
        />
      )}
      {glassMode && !imageFailed && attribution && (
        <GlassBadge
          label="PHOTO"
          text={`Representative stock photo, not this exact product: "${attribution.commonsTitle}" by ${attribution.artist}, ${attribution.license}. ${attribution.sourceUrl}`}
        />
      )}
    </div>
  )
}
