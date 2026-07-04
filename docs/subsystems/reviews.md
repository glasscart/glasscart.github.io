# Subsystem: Review Sentiment, Aspects & Fake-Review Detection

## What problem does this solve?

An aggregate star rating (`4.2 ★, 2,455 ratings`) hides everything useful about *why* people feel that way, and gives no way to tell a genuine opinion from a planted one. This subsystem turns raw review text into three things a shopper can actually use: an overall sentiment reading per review, a per-aspect breakdown (is this product's battery life liked, even if the reviews are mixed overall?), and a visible flag on reviews that look like spam.

## Why does it exist (in this form)?

Before this subsystem, GlassCart's catalog had no review text at all — only the aggregate `rating`/`rating_count` fields (see the [products dataset card](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/products/DATASET_CARD.md)). Building sentiment/aspect/fraud analysis meant building the review corpus first: [`datasets/reviews/`](https://github.com/glasscart/glasscart.github.io/tree/main/datasets/reviews) generates one, deliberately engineered (not random) to carry the signal a real analysis pipeline would need — aspect-sentiment structure per review, and one specific, documented bot-spam pattern for the fake-review heuristic to find. See [docs/research/reviews.md](../research/reviews.md) for the literature behind each of the three analysis components.

## How does it work?

`training/reviews/analyze.py` runs three rule-based components over every review, entirely offline:

1. **Sentiment scoring** — a hand-written word-polarity lexicon (`training/reviews/lexicon.py`) with negation and intensifier handling, in the same family as AFINN/VADER.
2. **Aspect extraction** — a small per-category keyword-to-aspect map (e.g. "battery" → "battery life" for Electronics) matched sentence-by-sentence; each matching sentence is scored by the same lexicon, giving a per-aspect opinion rather than one number for the whole review.
3. **Fake-review heuristic** — a weighted combination of three surface signals from the opinion-spam literature: duplicate review text, posting-burst behavior (the same author reviewing several unrelated products in a tight date window), and generic/non-specific text (short, exclamation-heavy, no aspect mentions).

The build step writes per-review and per-product artifacts to `models/reviews/` (see the [model card](https://github.com/glasscart/glasscart.github.io/blob/main/models/reviews/MODEL_CARD.md)), which the product detail page renders directly — no client-side inference happens for this subsystem, since there's no live user query to respond to (unlike search); it's static, precomputed content, published the same way the product catalog itself is.

## Why this implementation was chosen (vs. alternatives)

| Alternative | Why not (for this slice) |
|---|---|
| A trained sentiment classifier (e.g. a fine-tuned transformer) | Needs labeled training data GlassCart doesn't have, and would move CPU-only inference cost into a per-review classification step for no clear benefit at this catalog's scale; a lexicon is instant and fully inspectable. |
| A hosted sentiment/moderation API | Requires a paid account and a network call per review — violates the "no paid APIs, works on GitHub Pages" constraint every other subsystem follows. |
| Full syntactic-dependency-based ABSA | More accurate in principle, but a much bigger implementation for a small, templated synthetic corpus — keyword-based ABSA (Hu & Liu, 2004) is the right amount of technique for the actual text this pipeline processes. |
| Removing/hiding likely-fake reviews automatically | The heuristic is validated only against one synthetic pattern (see the model card's Metrics section) — acting on it automatically would overstate its real-world reliability. It's surfaced as a Glass Mode flag instead, never used to filter content. |

## Strengths

- Every score — sentiment, per-aspect, and fake — is traceable to specific words/features in the review text, with the exact contributing components shown in Glass Mode.
- Zero runtime cost: analysis happens once, offline, at build time; the deployed site only ever reads static JSON.
- The fake-review heuristic implements real, cited signals from the opinion-spam literature, not an invented approach — even though the *benchmark* it's evaluated against is synthetic (documented honestly, not hidden).

## Weaknesses & known failure cases

- The lexicon is small (~110 words) and English-only; unlisted or context-dependent sentiment words contribute nothing or contribute wrongly (see the model card's example of "fast" scoring positive inside a negative claim about battery drain).
- Aspect keyword matching can false-positive on incidental word overlap — observed directly in this dataset (a fake review's "amazing value" phrase matched the "price" aspect purely by coincidence).
- The fake-review heuristic's perfect precision/recall is a property of evaluating it against the one synthetic pattern it was built to catch, not evidence it would catch real review fraud (see [docs/research/reviews.md](../research/reviews.md) §5).
- The underlying review corpus is templated and far less lexically diverse than real reviews (see the [dataset card](https://github.com/glasscart/glasscart.github.io/blob/main/datasets/reviews/DATASET_CARD.md)), so every component here likely looks more capable than it would on real text.

## How it could be improved

- Expand the lexicon (or swap in a larger existing one, with a license check) and add more of VADER's own heuristics (exclamation/caps emphasis, contrastive conjunctions).
- Replace keyword-based aspect detection with dependency-parse-based extraction once a parsing dependency is judged worth adding to the CPU-only stack.
- Build a genuinely adversarial fake-review benchmark (varied patterns, not one bot signature) to get an evaluation number that means more than "the test matches the method."
- Surface per-review Glass Mode diagnostics inline in the review list itself (currently a separate panel), so the sentiment/aspect/fake breakdown sits next to the review it describes.

## Where to look in the code

| Concern | Offline (Python) | Client (TypeScript) |
|---|---|---|
| Dataset generation | `datasets/reviews/generate.py` | — |
| Sentiment lexicon | `training/reviews/lexicon.py` | — |
| Aspect extraction + fake-review heuristic + build | `training/reviews/analyze.py` | — |
| Types + data loading | — | `apps/web/src/lib/reviews/types.ts`, `apps/web/src/lib/reviews/loadReviews.ts` |
| UI | — | `apps/web/src/components/ReviewsSection.tsx`, `GlassReviewsPanel.tsx` |
| Wired into | — | `apps/web/src/pages/ProductDetailPage.tsx` |

## Further reading

See the full [research bibliography for reviews](../research/reviews.md) for primary sources on lexicon-based sentiment analysis, negation/intensifier handling, aspect-based sentiment analysis, and opinion-spam/fake-review detection.
