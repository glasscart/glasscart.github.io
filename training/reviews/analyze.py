"""Offline review analysis: sentiment scoring, aspect extraction, and a
fake-review heuristic over the synthetic reviews dataset.

Three rule-based components, all applied to review text (never to the
`is_fake_synthetic` ground-truth field in the dataset — see
datasets/reviews/DATASET_CARD.md for why that field exists and how it's
allowed to be used):

1. **Sentiment scoring** (lexicon.py): a hand-written word-polarity
   lexicon with negation/intensifier handling, applied per review.
2. **Aspect extraction**: a small per-category keyword-to-aspect map
   (e.g. "battery"/"charge" -> "battery life") is matched against each
   review's sentences; the sentiment lexicon then scores just the
   matching sentence, giving a per-aspect opinion rather than only an
   overall score. This is real, if simple, aspect-based sentiment
   analysis (keyword-spotting is a well-documented ABSA technique — see
   docs/research/reviews.md) — not a lookup of a label the dataset
   generator wrote for us; datasets/reviews/generate.py deliberately
   embeds aspect phrases in natural wording, with no aspect-name prefix,
   specifically so this extraction step has to do real work.
3. **Fake-review heuristic**: a weighted combination of surface features
   found in real review-fraud literature (near-duplicate text reused by
   the same author, tight posting-date bursts across unrelated products,
   generic superlative-only text with no specific aspect mentions).
   Evaluated (never trained) against the dataset's synthetic
   `is_fake_synthetic` labels, purely to report how well the heuristic
   performs on the one benchmark available — see the model card's
   Metrics section for the honest caveat about evaluating a heuristic
   against its own generator's synthetic labels.

No PyTorch, no GPU, no paid API — every technique here is small enough to
read end-to-end in this file and lexicon.py.

Usage:
    uv run training/reviews/analyze.py
"""

from __future__ import annotations

import json
import platform
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from lexicon import LEXICON, score_text, split_sentences, tokenize

REVIEWS_PATH = Path(__file__).parents[2] / "datasets" / "reviews" / "reviews.json"
PRODUCTS_PATH = Path(__file__).parents[2] / "datasets" / "products" / "products.json"
OUTPUT_DIR = Path(__file__).parents[2] / "models" / "reviews"
REVIEW_ANALYSIS_PATH = OUTPUT_DIR / "review_analysis.json"
PRODUCT_SUMMARY_PATH = OUTPUT_DIR / "product_review_summary.json"
MANIFEST_PATH = OUTPUT_DIR / "manifest.json"

# ---------------------------------------------------------------------------
# Aspect extraction: keyword -> aspect name, per category. Deliberately
# broader than any single phrase in datasets/reviews/generate.py's phrase
# banks (e.g. "sturdy"/"flimsy"/"well made" all point at "build quality"),
# so this is genuine keyword spotting, not a lookup of one exact string.
# ---------------------------------------------------------------------------

ASPECT_KEYWORDS: dict[str, dict[str, list[str]]] = {
    "Electronics": {
        "battery life": ["battery"],
        "build quality": ["sturdy", "flimsy", "well made", "cheap", "loose", "built"],
        "connectivity": ["connect", "connection", "pairing", "pair", "dropping"],
        "price": ["price", "value", "worth", "money", "overpriced", "cost"],
    },
    "Home & Kitchen": {
        "build quality": ["heavy-duty", "durable", "falling apart", "flimsy", "last"],
        "ease of use": ["easy to use", "setup", "instructions", "fiddly"],
        "size": ["size", "bulkier", "compact", "small", "roomy"],
        "price": ["price", "value", "worth", "cost", "overpriced", "penny"],
    },
    "Books": {
        "writing": ["writing", "written", "follow"],
        "print quality": ["print", "pages", "bound", "binding"],
        "length": ["length", "short", "long", "padded", "content"],
        "price": ["price", "worth", "overpriced", "cost"],
    },
    "Clothing": {
        "fit": ["fit", "fits", "size", "small"],
        "fabric quality": ["fabric", "material", "pilled"],
        "comfort": ["comfortable", "uncomfortable", "seams", "comfort"],
        "price": ["price", "worth", "overpriced", "cost", "penny"],
    },
    "Sports & Outdoors": {
        "durability": ["durable", "holds up", "wore out", "broke", "durability"],
        "comfort": ["comfortable", "uncomfortable", "comfort"],
        "weight": ["lightweight", "heavier", "weight", "carry"],
        "price": ["price", "worth", "overpriced", "investment", "money"],
    },
    "Beauty": {
        "scent": ["scent", "smell", "smells"],
        "texture": ["texture", "greasy", "sticky", "absorbs"],
        "effectiveness": ["works", "difference", "advertised", "effective"],
        "price": ["price", "worth", "overpriced", "penny", "cost"],
    },
    "Toys": {
        "durability": ["durable", "broke", "holding up", "survives", "rough play"],
        "fun factor": ["fun", "obsessed", "entertained", "interest"],
        "safety": ["safe", "safety", "hazard", "sharp", "small parts"],
        "price": ["price", "worth", "overpriced", "penny", "cost"],
    },
    "Grocery": {
        "taste": ["taste", "tastes", "tasted"],
        "freshness": ["fresh", "freshness", "stale"],
        "packaging": ["packaging", "package", "resealable", "damaged"],
        "price": ["price", "worth", "overpriced", "penny", "cost"],
    },
    "Office Supplies": {
        "build quality": ["sturdy", "flimsy", "cracked", "well made"],
        "ease of use": ["easy", "intuitive", "complicated", "instructions"],
        "design": ["design", "sleek", "looks", "impractical"],
        "price": ["price", "worth", "overpriced", "penny", "cost"],
    },
    "Pet Supplies": {
        "durability": ["holds up", "destroyed", "chewing", "intact", "durable"],
        "size": ["size", "sizing", "smaller", "bulky"],
        "ease of use": ["easy", "clean", "effortless", "hassle"],
        "price": ["price", "worth", "overpriced", "penny", "cost"],
    },
}

# ---------------------------------------------------------------------------
# Fake-review heuristic weights. Each indicator is normalized to [0, 1]
# before weighting, so the final fake_score is also roughly in [0, 1].
# ---------------------------------------------------------------------------

WEIGHT_DUPLICATE_TEXT = 0.4
WEIGHT_AUTHOR_BURST = 0.35
WEIGHT_GENERIC_TEXT = 0.25
FAKE_SCORE_THRESHOLD = 0.5


@dataclass
class ReviewAnalysis:
    review_id: str
    product_id: str
    sentiment_score: float
    aspects: dict[str, float]
    fake_score: float
    likely_fake: bool
    is_fake_synthetic: bool  # carried through for the evaluation report only


def extract_aspects(body: str, category: str) -> dict[str, float]:
    keywords = ASPECT_KEYWORDS.get(category, {})
    sentences = split_sentences(body)
    found: dict[str, list[float]] = defaultdict(list)
    for sentence in sentences:
        lower = sentence.lower()
        for aspect, triggers in keywords.items():
            if any(trigger in lower for trigger in triggers):
                found[aspect].append(score_text(sentence))
    return {aspect: round(sum(scores) / len(scores), 3) for aspect, scores in found.items()}


def _burst_score(same_author_reviews: list[dict]) -> float:
    """1.0 if this author reviewed >=3 distinct products within a 7-day window, else 0.0."""
    if len(same_author_reviews) < 3:
        return 0.0
    dates = sorted(datetime.strptime(r["created_at"], "%Y-%m-%d").date() for r in same_author_reviews)
    distinct_products = len({r["product_id"] for r in same_author_reviews})
    span = (dates[-1] - dates[0]).days
    return 1.0 if distinct_products >= 3 and span <= 7 else 0.0


def _generic_text_score(body: str, category: str) -> float:
    """High for short, exclamation-heavy text with no detected aspect mentions."""
    tokens = tokenize(body)
    if not tokens:
        return 0.0
    exclamations = body.count("!")
    has_aspect = bool(extract_aspects(body, category))
    short = len(tokens) <= 12
    punchy = exclamations >= 2
    if short and punchy and not has_aspect:
        return 1.0
    if (short or punchy) and not has_aspect:
        return 0.5
    return 0.0


def compute_fake_scores(reviews: list[dict], product_by_id: dict[str, dict]) -> dict[str, float]:
    by_author: dict[str, list[dict]] = defaultdict(list)
    for r in reviews:
        by_author[r["author"]].append(r)

    body_counts = Counter(r["body"] for r in reviews)

    scores: dict[str, float] = {}
    for r in reviews:
        category = product_by_id[r["product_id"]]["category"]
        duplicate = 1.0 if body_counts[r["body"]] >= 3 else 0.0
        burst = _burst_score(by_author[r["author"]])
        generic = _generic_text_score(r["body"], category)
        scores[r["id"]] = round(
            WEIGHT_DUPLICATE_TEXT * duplicate + WEIGHT_AUTHOR_BURST * burst + WEIGHT_GENERIC_TEXT * generic,
            3,
        )
    return scores


def evaluate_fake_heuristic(analyses: list[ReviewAnalysis]) -> dict:
    tp = sum(1 for a in analyses if a.likely_fake and a.is_fake_synthetic)
    fp = sum(1 for a in analyses if a.likely_fake and not a.is_fake_synthetic)
    fn = sum(1 for a in analyses if not a.likely_fake and a.is_fake_synthetic)
    tn = sum(1 for a in analyses if not a.likely_fake and not a.is_fake_synthetic)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "true_negatives": tn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "caveat": (
            "Evaluated against this dataset's own synthetically-generated fake-review "
            "pattern, not real review fraud — see models/reviews/MODEL_CARD.md."
        ),
    }


def build() -> None:
    started_at = datetime.now(timezone.utc)
    reviews = json.loads(REVIEWS_PATH.read_text(encoding="utf-8"))
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    product_by_id = {p["id"]: p for p in products}

    fake_scores = compute_fake_scores(reviews, product_by_id)

    analyses: list[ReviewAnalysis] = []
    for r in reviews:
        category = product_by_id[r["product_id"]]["category"]
        sentiment = round(score_text(r["body"]), 3)
        aspects = extract_aspects(r["body"], category)
        fake_score = fake_scores[r["id"]]
        analyses.append(
            ReviewAnalysis(
                review_id=r["id"],
                product_id=r["product_id"],
                sentiment_score=sentiment,
                aspects=aspects,
                fake_score=fake_score,
                likely_fake=fake_score >= FAKE_SCORE_THRESHOLD,
                is_fake_synthetic=r["is_fake_synthetic"],
            )
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_ANALYSIS_PATH.write_text(
        json.dumps(
            [
                {
                    "review_id": a.review_id,
                    "product_id": a.product_id,
                    "sentiment_score": a.sentiment_score,
                    "aspects": a.aspects,
                    "fake_score": a.fake_score,
                    "likely_fake": a.likely_fake,
                }
                for a in analyses
            ],
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # Per-product aggregation: average sentiment, per-aspect average
    # sentiment + mention count, and how many reviews were flagged.
    by_product: dict[str, list[ReviewAnalysis]] = defaultdict(list)
    for a in analyses:
        by_product[a.product_id].append(a)

    summaries = []
    for product_id, items in by_product.items():
        non_fake = [a for a in items if not a.likely_fake]
        pool = non_fake if non_fake else items
        avg_sentiment = round(sum(a.sentiment_score for a in pool) / len(pool), 3)
        aspect_scores: dict[str, list[float]] = defaultdict(list)
        for a in pool:
            for aspect, score in a.aspects.items():
                aspect_scores[aspect].append(score)
        aspect_summary = [
            {"aspect": aspect, "avg_sentiment": round(sum(scores) / len(scores), 3), "mentions": len(scores)}
            for aspect, scores in sorted(aspect_scores.items(), key=lambda kv: -len(kv[1]))
        ]
        summaries.append(
            {
                "product_id": product_id,
                "review_count": len(items),
                "avg_sentiment": avg_sentiment,
                "aspects": aspect_summary,
                "likely_fake_count": sum(1 for a in items if a.likely_fake),
            }
        )
    summaries.sort(key=lambda s: s["product_id"])
    PRODUCT_SUMMARY_PATH.write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")

    evaluation = evaluate_fake_heuristic(analyses)
    finished_at = datetime.now(timezone.utc)

    manifest = {
        "methodology": {
            "sentiment": "hand-written word-polarity lexicon with negation/intensifier handling (training/reviews/lexicon.py)",
            "aspect_extraction": "per-category keyword-to-aspect matching + sentence-level lexicon scoring",
            "fake_review_heuristic": "weighted rule combination: duplicate text, author posting-burst, generic/short/punchy text with no aspect mentions",
        },
        "lexicon_size": len({w for w, v in LEXICON.items() if v is not None}),
        "fake_score_threshold": FAKE_SCORE_THRESHOLD,
        "fake_heuristic_weights": {
            "duplicate_text": WEIGHT_DUPLICATE_TEXT,
            "author_burst": WEIGHT_AUTHOR_BURST,
            "generic_text": WEIGHT_GENERIC_TEXT,
        },
        "num_reviews": len(reviews),
        "num_products": len(products),
        "fake_heuristic_evaluation": evaluation,
        "generated_at": started_at.isoformat(),
        "build_duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "runtime": {"python": platform.python_version()},
        "dataset_seed": 20260704,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Analyzed {len(reviews)} reviews across {len(summaries)} products")
    print(f"Fake-review heuristic: precision={evaluation['precision']}, recall={evaluation['recall']}, f1={evaluation['f1']}")
    print(f"-> {REVIEW_ANALYSIS_PATH}\n-> {PRODUCT_SUMMARY_PATH}\n-> {MANIFEST_PATH}")


if __name__ == "__main__":
    build()
