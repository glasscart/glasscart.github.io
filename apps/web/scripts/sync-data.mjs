// Copies committed dataset/model artifacts into public/data so the static
// site has them to fetch. Plain Node (no Python) so `npm install && npm run
// dev` works immediately after cloning — see Workflow A in the root README.
// Re-running training pipelines (Workflow B/C) regenerates the sources this
// script copies from; run `uv run scripts/sync_web_data.py` after that, or
// just re-run `npm run dev`, which does it automatically via "predev".
import { copyFileSync, mkdirSync, existsSync, readdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const repoRoot = join(here, '..', '..', '..')
const dest = join(here, '..', 'public', 'data')

// { src, name }: `name` is the explicit filename under public/data — several
// subsystems each ship their own manifest.json, so basename alone would
// collide (search-embeddings/manifest.json vs. reviews/manifest.json).
const sources = [
  { src: join(repoRoot, 'datasets', 'products', 'products.json'), name: 'products.json' },
  { src: join(repoRoot, 'models', 'search-embeddings', 'product_embeddings.json'), name: 'product_embeddings.json' },
  { src: join(repoRoot, 'models', 'search-embeddings', 'manifest.json'), name: 'manifest.json' },
  { src: join(repoRoot, 'datasets', 'reviews', 'reviews.json'), name: 'reviews.json' },
  { src: join(repoRoot, 'models', 'reviews', 'review_analysis.json'), name: 'review_analysis.json' },
  { src: join(repoRoot, 'models', 'reviews', 'product_review_summary.json'), name: 'product_review_summary.json' },
  { src: join(repoRoot, 'models', 'reviews', 'manifest.json'), name: 'reviews_manifest.json' },
  { src: join(repoRoot, 'models', 'pricing', 'pricing_recommendations.json'), name: 'pricing_recommendations.json' },
  { src: join(repoRoot, 'models', 'pricing', 'manifest.json'), name: 'pricing_manifest.json' },
]

mkdirSync(dest, { recursive: true })

for (const { src, name } of sources) {
  if (!existsSync(src)) {
    console.error(`Missing ${src} — run the dataset/training pipeline first (see README.md).`)
    process.exit(1)
  }
  const target = join(dest, name)
  copyFileSync(src, target)
  console.log(`${src} -> ${target}`)
}

// Product images are optional (see training/product_images/, gated behind the
// `imagegen` dependency group) — copy them if they've been generated, but
// don't fail the build if they haven't. ProductImage.tsx falls back to a
// procedural placeholder for any product without a generated image.
const imagesSrcDir = join(repoRoot, 'datasets', 'products', 'images')
if (existsSync(imagesSrcDir)) {
  const imagesDestDir = join(dest, 'images')
  mkdirSync(imagesDestDir, { recursive: true })
  const files = readdirSync(imagesSrcDir).filter((f) => f.endsWith('.png'))
  for (const file of files) {
    copyFileSync(join(imagesSrcDir, file), join(imagesDestDir, file))
  }
  console.log(`${imagesSrcDir} -> ${imagesDestDir} (${files.length} images)`)
} else {
  console.log(`${imagesSrcDir} not found — skipping (run training/product_images/ to generate)`)
}
