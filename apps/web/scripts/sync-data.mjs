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

const sources = [
  join(repoRoot, 'datasets', 'products', 'products.json'),
  join(repoRoot, 'models', 'search-embeddings', 'product_embeddings.json'),
  join(repoRoot, 'models', 'search-embeddings', 'manifest.json'),
]

mkdirSync(dest, { recursive: true })

for (const src of sources) {
  if (!existsSync(src)) {
    console.error(`Missing ${src} — run the dataset/training pipeline first (see README.md).`)
    process.exit(1)
  }
  const target = join(dest, src.split('/').pop())
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
