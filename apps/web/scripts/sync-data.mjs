// Copies committed dataset/model artifacts into public/data so the static
// site has them to fetch. Plain Node (no Python) so `npm install && npm run
// dev` works immediately after cloning — see Workflow A in the root README.
// Re-running training pipelines (Workflow B/C) regenerates the sources this
// script copies from; run `uv run scripts/sync_web_data.py` after that, or
// just re-run `npm run dev`, which does it automatically via "predev".
import { copyFileSync, mkdirSync, existsSync } from 'node:fs'
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
