export function AboutPage() {
  return (
    <main className="mx-auto max-w-3xl px-4 py-12">
      <h1 className="text-2xl font-semibold">About this project</h1>
      <p className="mt-4 text-slate-600 dark:text-slate-400">
        GlassCart is an open-source, educational demo of an AI-powered commerce platform. Nothing
        here is a real store: the catalog, ratings, and search results are all synthetically
        generated. The point isn't to sell anything — it's to show, in the open, how the AI
        features behind a modern storefront actually work.
      </p>

      <h2 className="mt-8 text-lg font-semibold">Glass Mode</h2>
      <p className="mt-2 text-slate-600 dark:text-slate-400">
        Toggle <span className="font-medium text-glass-600 dark:text-glass-300">Glass Mode</span> in
        the header and any AI-assisted feature on the site — starting with search — exposes its own
        diagnostics inline: which model ran, how long it took, and how the final result was scored.
        Nothing AI-driven on this site is a black box.
      </p>

      <h2 className="mt-8 text-lg font-semibold">How search works today</h2>
      <p className="mt-2 text-slate-600 dark:text-slate-400">
        Product search runs entirely in your browser, combining classic keyword matching (BM25)
        with semantic embedding search, fused into a single ranked result. See the full write-up
        and reproduction steps in{' '}
        <code className="rounded bg-slate-100 px-1 py-0.5 text-sm dark:bg-slate-800">
          docs/subsystems/search.md
        </code>
        , the model card in{' '}
        <code className="rounded bg-slate-100 px-1 py-0.5 text-sm dark:bg-slate-800">
          models/search-embeddings/MODEL_CARD.md
        </code>
        , and the dataset card in{' '}
        <code className="rounded bg-slate-100 px-1 py-0.5 text-sm dark:bg-slate-800">
          datasets/products/DATASET_CARD.md
        </code>
        .
      </p>

      <h2 className="mt-8 text-lg font-semibold">Source</h2>
      <p className="mt-2 text-slate-600 dark:text-slate-400">
        The full source, roadmap, and research bibliography are on{' '}
        <a
          href="https://github.com/glasscart/glasscart.github.io"
          className="text-glass-600 hover:underline dark:text-glass-300"
          target="_blank"
          rel="noreferrer"
        >
          GitHub
        </a>
        .
      </p>
    </main>
  )
}
