# Model Card: `reviews` (lexicon sentiment + keyword aspect extraction + fake-review heuristic)

Following the structure proposed by [Model Cards for Model Reporting](https://arxiv.org/abs/1810.03993) (Mitchell et al., 2019). This covers three small, rule-based components — sentiment scoring, aspect extraction, and fake-review detection — documented together because they're tightly coupled (the same lexicon powers the first two, and aspect detection feeds the third) and each is too small to warrant a separate card. Everything here is surfaced in the product UI whenever [Glass Mode](../../docs/glass-mode.md) is switched on.

## Purpose

Turn raw review text (see the [reviews dataset](../../datasets/reviews/DATASET_CARD.md)) into three things a shopper or seller would actually want: an overall sentiment score per review, a per-aspect breakdown ("battery life: negative, price: positive"), and a flag for reviews that look like spam. None of this is a hard-coded number — every score is computed from the review's actual text.

## Architecture

- **Sentiment scoring**: a hand-written word-polarity lexicon (`training/reviews/lexicon.py`, ~110 scored words) with negation flipping ("not good" → negative) and intensifier scaling ("very good" → stronger positive) — the same family of technique as AFINN/VADER, reimplemented from scratch rather than taken from a library, matching this project's `bm25.ts` precedent of favoring a small, fully-readable implementation over an opaque dependency.
- **Aspect extraction**: a per-category keyword-to-aspect map (e.g. Electronics' "battery life" aspect triggers on the keyword "battery"). Each sentence in a review is checked against the current product category's keywords; a match's *sentence* (not the whole review) is scored with the same lexicon, giving a per-aspect opinion. This is genuine keyword-based aspect-based sentiment analysis (ABSA) — a real, documented technique, simpler than dependency-parsing-based ABSA — not a lookup of a label the dataset generator wrote for us (see "Training Data" below for why that distinction is real, not just asserted).
- **Fake-review heuristic**: a weighted sum of three surface-feature indicators, each normalized to `[0, 1]`: exact-duplicate review text shared across ≥3 reviews (weight `0.4`), the same author posting to ≥3 distinct products within a 7-day window (weight `0.35`), and short (≤12 tokens), punctuation-heavy (≥2 `!`) text with no detected aspect mentions (weight `0.25`). A review is flagged `likely_fake` at a combined score ≥ `0.5`.

## Training Data

None of these three components is trained — they're deterministic, hand-set rules. The only "data" involved is the lexicon's word list, hand-written for this project (not copied from AFINN, VADER, or any other existing list) and deliberately *not* derived from [`datasets/reviews/generate.py`](../../datasets/reviews/generate.py)'s own phrase banks — scoring a generator's output using the same words it was built from would be circular. Similarly, `datasets/reviews/generate.py` deliberately never writes an aspect's name into review text (no "On battery life: ..." prefix) specifically so aspect extraction has to detect the aspect from context, not read back a label.

## What GlassCart Does With It

`training/reviews/analyze.py` reads `datasets/reviews/reviews.json`, scores every review, aggregates per-product summaries (average sentiment, per-aspect average sentiment and mention count, count of reviews flagged likely-fake — fake-flagged reviews are excluded from the aggregate where any non-fake reviews exist), and writes:

- `review_analysis.json` — per-review sentiment score, aspect breakdown, fake score, and flag.
- `product_review_summary.json` — per-product aggregate.
- `manifest.json` — methodology, lexicon size, heuristic weights, and an evaluation of the fake-review heuristic (see "Metrics").

`apps/web/src/components/ReviewsSection.tsx` renders this on the product detail page; Glass Mode shows the full per-review breakdown and the methodology panel.

## Metrics

**Sentiment/aspect**: no accuracy metric is reported — there is no independently-labeled ground truth for "correct" sentiment on this synthetic text, so a number here would imply a precision the method doesn't have. Glass Mode instead shows the raw lexicon contributions so a user can verify a score by reading the words that produced it.

**Fake-review heuristic**, evaluated against the dataset's synthetic `is_fake_synthetic` labels (see `models/reviews/manifest.json`'s `fake_heuristic_evaluation` for the exact numbers from the last build):

| Metric | Value (typical) |
|---|---|
| Precision | 1.0 |
| Recall | 1.0 |
| F1 | 1.0 |

**This is not a claim of 100% real-world fake-review detection accuracy.** The evaluation set is the same generator's own synthetic fake reviews, built with a single, blatant, known pattern (verbatim-duplicated text, tight posting bursts, generic superlative language) that the heuristic's three rules were explicitly designed to catch — a heuristic scoring perfectly here is closer to "the test matches the method by construction" than a measurement of real-world skill. It's reported anyway, honestly labeled, because an evaluation number with an aggressive caveat is more transparent than no evaluation at all. See "Non-Intended Use."

## Confidence & Uncertainty

Sentiment and aspect scores are unbounded lexicon sums, not probabilities — Glass Mode presents them as raw scores (with their sign and the contributing words), not as a false "% confident" figure. The fake-review score is a weighted sum of binary/normalized indicators in `[0, 1]` and is shown as exactly that (a threshold-compared score with its component breakdown), not a calibrated probability of fraud.

## Hardware Used

Pure Python, stdlib only for `analyze.py` and `lexicon.py` — no GPU, no ML framework, negligible runtime (the entire 2,200-review corpus analyzes in well under a second; see `manifest.json`'s `build_duration_seconds`).

## Known Limitations & Failure Cases

- **Lexicon coverage is small (~110 words)** and English-only; any sentiment-bearing word outside the list contributes nothing, and context-dependent words are scored the same regardless of context (e.g. "fast" is scored positive even in "drains way too fast," where it's part of a negative claim about battery life).
- **Aspect keyword lists can false-positive on incidental word overlap**: a synthetic fake review's boilerplate phrase "amazing value" was observed matching the "price" aspect's `value` keyword purely by coincidence, despite the review having nothing genuine to say about price — a real illustration of why keyword-based ABSA is a heuristic, not true language understanding.
- **Fake-review heuristic is tuned to this dataset's one synthetic fraud pattern** (see "Metrics") and has no evidence of generalizing to real review fraud, which is far more varied and adversarial.
- **No calibration**: none of the three components' scores have been validated against human judgment of any kind, synthetic or real.
- **Templated input**: the dataset's reviews (see its [DATASET_CARD.md](../../datasets/reviews/DATASET_CARD.md)) are far less lexically diverse than real reviews, so all three components likely look more accurate here than they would on real text.

## Ethical & Privacy Considerations

- All review text, authors, and ratings are synthetic; no real reviewer data is processed anywhere in this pipeline.
- The fake-review heuristic flags reviews for display in Glass Mode only — it does not remove, hide, or otherwise act on flagged reviews, avoiding a false sense of automated moderation for a heuristic this simple and this narrowly validated.

## Intended Use

Demonstrating a small, fully-inspectable, rule-based NLP pipeline (sentiment, aspect extraction, fraud heuristic) end-to-end, including an honest account of how a fake-review detector was built and evaluated against a synthetic benchmark it was designed to catch.

## Non-Intended Use

Not intended for real fraud/spam detection, real content moderation, or any decision with real consequences for a real reviewer or seller. Not validated on any real-world review corpus, in any language other than English, or against any professionally-labeled sentiment/ABSA benchmark.

## Reproducibility

```bash
uv sync
uv run datasets/products/generate.py     # if the product catalog changed
uv run datasets/reviews/generate.py      # regenerate the synthetic review corpus
uv run training/reviews/analyze.py       # rebuild sentiment/aspect/fake-review artifacts
uv run scripts/sync_web_data.py          # publish artifacts to apps/web/public/data
```

Re-running with the same `reviews.json` produces byte-identical analysis output (every component is a deterministic function of its input text; there is no sampling or randomness in `analyze.py`).
