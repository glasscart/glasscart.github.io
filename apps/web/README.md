# `apps/web`

GlassCart's web app — React 19 + TypeScript + Vite + Tailwind CSS v4. Fully static; works standalone with no backend.

See the [root README](../../README.md) for the full quickstart, and [`docs/subsystems/search.md`](../../docs/subsystems/search.md) for how the search feature implemented here works.

```bash
npm install
npm run dev      # regenerates apps/web/public/data from datasets/ + models/, then starts Vite
npm run build    # typecheck + production build
npm run lint     # eslint
```

`predev`/`prebuild` run `scripts/sync-data.mjs`, which copies the committed dataset/embedding artifacts from `datasets/` and `models/` into `public/data/` — see [`docs/architecture/overview.md`](../../docs/architecture/overview.md#reproducibility-pipeline).
