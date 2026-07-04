"""Synthetic review generator for GlassCart.

Generates a deterministic, seeded set of product reviews — review text,
star rating, author, timestamps — for the existing product catalog
(datasets/products/products.json). No real reviewers, no scraped content.

Two things are deliberately built into the generation, not left to chance,
because the downstream reviews subsystem (training/reviews/) needs real
signal to find:

1. **Aspect-sentiment structure.** Each category has a small set of
   product aspects (e.g. Electronics: battery life, build quality...).
   Genuine reviews mention 1-3 aspects with an attached positive/negative
   phrase, so an aspect-sentiment extractor has actual per-aspect opinions
   to pull out, not just an overall star rating.
2. **A synthetic fake-review minority.** ~8% of reviews are generated to
   look like spam/bot reviews: generic superlative-only text with no
   aspect mentions, reused verbatim by the same synthetic author across
   many unrelated products, posted in tight bursts. Each such review is
   tagged `is_fake_synthetic: true` in the output — a ground-truth label
   used only to *evaluate* the fake-review heuristic in training/reviews/,
   never fed into the heuristic itself (see that script's docstring and
   the model card for why that distinction matters).

Usage:
    uv run datasets/reviews/generate.py
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

SEED = 20260704
PRODUCTS_PATH = Path(__file__).parents[1] / "products" / "products.json"
OUTPUT_PATH = Path(__file__).parent / "reviews.json"

FAKE_REVIEW_RATE = 0.08
MIN_REVIEWS_PER_PRODUCT = 2
MAX_REVIEWS_PER_PRODUCT = 11

# ---------------------------------------------------------------------------
# Aspect vocabulary: a handful of product aspects per category, each with a
# bank of positive and negative phrases. This is what gives a genuine review
# its aspect-level opinions, as opposed to just an overall star rating.
# ---------------------------------------------------------------------------

CATEGORY_ASPECTS: dict[str, dict[str, dict[str, list[str]]]] = {
    "Electronics": {
        "battery life": {
            "positive": ["the battery easily lasts all day", "battery life is excellent"],
            "negative": ["the battery drains way too fast", "battery life was disappointing"],
        },
        "build quality": {
            "positive": ["it feels sturdy and well made", "build quality is solid"],
            "negative": ["it feels cheap and flimsy", "a piece came loose within a week"],
        },
        "connectivity": {
            "positive": ["it connects instantly every time", "the connection is rock solid"],
            "negative": ["it keeps dropping the connection", "pairing is unreliable"],
        },
        "price": {
            "positive": ["it's a great value for the price", "well worth the money"],
            "negative": ["it's overpriced for what you get", "not worth the price"],
        },
    },
    "Home & Kitchen": {
        "build quality": {
            "positive": ["it's built to last", "feels heavy-duty and durable"],
            "negative": ["it started falling apart quickly", "feels flimsy"],
        },
        "ease of use": {
            "positive": ["it's incredibly easy to use", "setup took two minutes"],
            "negative": ["the instructions were confusing", "it's more fiddly than it should be"],
        },
        "size": {
            "positive": ["the size is perfect for our kitchen", "compact but roomy enough"],
            "negative": ["it's bulkier than the photos suggest", "too small to be useful"],
        },
        "price": {
            "positive": ["great value for the price", "worth every penny"],
            "negative": ["overpriced for what it does", "not worth the cost"],
        },
    },
    "Books": {
        "writing": {
            "positive": ["the writing is engaging and clear", "beautifully written"],
            "negative": ["the writing felt dry", "hard to follow in places"],
        },
        "print quality": {
            "positive": ["the print quality is excellent", "pages feel sturdy and well bound"],
            "negative": ["pages started coming loose", "print quality is disappointing"],
        },
        "length": {
            "positive": ["the length felt just right", "packed with content for its size"],
            "negative": ["it felt too short for the price", "padded out longer than it needed to be"],
        },
        "price": {
            "positive": ["a great price for the content", "well worth what I paid"],
            "negative": ["overpriced for how short it is", "not worth the price"],
        },
    },
    "Clothing": {
        "fit": {
            "positive": ["the fit is true to size", "fits perfectly"],
            "negative": ["it runs way too small", "the fit is inconsistent"],
        },
        "fabric quality": {
            "positive": ["the fabric feels premium", "material is soft and durable"],
            "negative": ["the fabric feels cheap", "it pilled after one wash"],
        },
        "comfort": {
            "positive": ["it's incredibly comfortable all day", "comfortable from the first wear"],
            "negative": ["it's surprisingly uncomfortable", "the seams dig in uncomfortably"],
        },
        "price": {
            "positive": ["great quality for the price", "worth every penny"],
            "negative": ["overpriced for the quality", "not worth the cost"],
        },
    },
    "Sports & Outdoors": {
        "durability": {
            "positive": ["it holds up to heavy use", "still going strong after months of use"],
            "negative": ["it wore out faster than expected", "it broke after light use"],
        },
        "comfort": {
            "positive": ["it's comfortable for long sessions", "comfortable even after hours"],
            "negative": ["it's uncomfortable after a short time", "comfort is lacking"],
        },
        "weight": {
            "positive": ["it's impressively lightweight", "barely notice the weight"],
            "negative": ["it's heavier than expected", "the weight makes it a hassle to carry"],
        },
        "price": {
            "positive": ["great value for the price", "worth the investment"],
            "negative": ["overpriced for the quality", "not worth the money"],
        },
    },
    "Beauty": {
        "scent": {
            "positive": ["the scent is subtle and pleasant", "smells amazing"],
            "negative": ["the scent is overpowering", "the smell is unpleasant"],
        },
        "texture": {
            "positive": ["the texture feels luxurious", "absorbs quickly without residue"],
            "negative": ["the texture is greasy", "it feels sticky and heavy"],
        },
        "effectiveness": {
            "positive": ["it actually works as advertised", "noticed a difference within days"],
            "negative": ["it didn't work at all for me", "saw no noticeable difference"],
        },
        "price": {
            "positive": ["great value for the price", "worth every penny"],
            "negative": ["overpriced for what it delivers", "not worth the cost"],
        },
    },
    "Toys": {
        "durability": {
            "positive": ["it survives daily rough play", "still holding up after months"],
            "negative": ["it broke within days", "it fell apart quickly"],
        },
        "fun factor": {
            "positive": ["the kids are obsessed with it", "keeps them entertained for hours"],
            "negative": ["the kids lost interest immediately", "it wasn't as fun as expected"],
        },
        "safety": {
            "positive": ["it feels well made and safe", "no sharp edges or small parts"],
            "negative": ["a piece broke off and became a hazard", "the safety feels questionable"],
        },
        "price": {
            "positive": ["great value for the price", "worth every penny"],
            "negative": ["overpriced for what it is", "not worth the cost"],
        },
    },
    "Grocery": {
        "taste": {
            "positive": ["the taste is fantastic", "tastes better than expected"],
            "negative": ["the taste was underwhelming", "it tasted artificial"],
        },
        "freshness": {
            "positive": ["it arrived perfectly fresh", "freshness is consistently great"],
            "negative": ["it arrived stale", "freshness was disappointing"],
        },
        "packaging": {
            "positive": ["the packaging keeps it fresh", "packaging is sturdy and resealable"],
            "negative": ["the packaging arrived damaged", "packaging doesn't reseal well"],
        },
        "price": {
            "positive": ["great value for the price", "worth every penny"],
            "negative": ["overpriced for the amount you get", "not worth the cost"],
        },
    },
    "Office Supplies": {
        "build quality": {
            "positive": ["it feels sturdy and well made", "build quality is impressive"],
            "negative": ["it feels flimsy", "a part cracked within weeks"],
        },
        "ease of use": {
            "positive": ["it's simple to set up and use", "intuitive right out of the box"],
            "negative": ["it's needlessly complicated", "instructions were unclear"],
        },
        "design": {
            "positive": ["the design is sleek and practical", "looks great on my desk"],
            "negative": ["the design is impractical", "it looks cheap"],
        },
        "price": {
            "positive": ["great value for the price", "worth every penny"],
            "negative": ["overpriced for what it offers", "not worth the cost"],
        },
    },
    "Pet Supplies": {
        "durability": {
            "positive": ["it holds up to my dog's chewing", "still intact after heavy use"],
            "negative": ["it was destroyed within a day", "it fell apart quickly"],
        },
        "size": {
            "positive": ["the size is perfect for my pet", "sizing was spot on"],
            "negative": ["it runs smaller than expected", "too bulky for the space"],
        },
        "ease of use": {
            "positive": ["it's easy to clean and use", "setup was effortless"],
            "negative": ["it's a hassle to clean", "harder to use than expected"],
        },
        "price": {
            "positive": ["great value for the price", "worth every penny"],
            "negative": ["overpriced for the quality", "not worth the cost"],
        },
    },
}

OPENING_POSITIVE = [
    "Really happy with this purchase.",
    "This exceeded my expectations.",
    "Glad I bought this one.",
    "Pleasantly surprised by this.",
]
OPENING_NEGATIVE = [
    "Pretty disappointed with this purchase.",
    "This didn't meet my expectations.",
    "Wish I had bought something else.",
    "Not what I was hoping for.",
]
OPENING_MIXED = [
    "Mixed feelings about this one.",
    "Some good, some bad here.",
    "It's fine, but not perfect.",
]

CLOSING_POSITIVE = ["Would recommend.", "Would buy again.", "Happy to recommend this."]
CLOSING_NEGATIVE = ["Would not recommend.", "Probably won't buy again.", "Hard to recommend this."]
CLOSING_NEUTRAL = ["Your mileage may vary.", "Works for my needs, at least."]

FAKE_AUTHORS = ["QualityShopper99", "BestDealsFan", "TopReviewerXX", "DailyDealsGuru"]
FAKE_PHRASES = [
    "Great product! Highly recommend! Five stars!!!",
    "Amazing!!! Best purchase ever, you need this now!!!",
    "Perfect in every way, buy it immediately, 5 stars!!!",
    "Incredible quality, amazing value, everyone should buy this!!!",
]

REAL_AUTHOR_FIRST = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Sam", "Jamie",
                     "Drew", "Quinn", "Avery", "Reese", "Skyler", "Rowan", "Cameron"]
REAL_AUTHOR_LAST_INITIAL = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


@dataclass
class Review:
    id: str
    product_id: str
    author: str
    rating: int
    title: str
    body: str
    verified_purchase: bool
    helpful_votes: int
    created_at: str
    is_fake_synthetic: bool


def _real_author(rng: random.Random) -> str:
    return f"{rng.choice(REAL_AUTHOR_FIRST)} {rng.choice(REAL_AUTHOR_LAST_INITIAL)}."


def _star_for_sentiment(rng: random.Random, base_rating: float) -> int:
    # Individual reviews scatter around the product's aggregate rating
    # rather than all matching it exactly — real review distributions are
    # noisier than their own average.
    star = round(base_rating + rng.triangular(-1.5, 1.5, 0))
    return max(1, min(5, star))


def _real_review(rng: random.Random, product: dict, review_index: int) -> Review:
    aspects = CATEGORY_ASPECTS.get(product["category"], {})
    aspect_names = list(aspects.keys())
    star = _star_for_sentiment(rng, product["rating"])
    sentiment = "positive" if star >= 4 else "negative" if star <= 2 else "mixed"

    sentences = []
    if sentiment == "positive":
        sentences.append(rng.choice(OPENING_POSITIVE))
    elif sentiment == "negative":
        sentences.append(rng.choice(OPENING_NEGATIVE))
    else:
        sentences.append(rng.choice(OPENING_MIXED))

    num_aspects = rng.randint(1, min(3, len(aspect_names))) if aspect_names else 0
    chosen_aspects = rng.sample(aspect_names, k=num_aspects) if num_aspects else []
    for aspect in chosen_aspects:
        if sentiment == "mixed":
            polarity = rng.choice(["positive", "negative"])
        else:
            polarity = sentiment
        phrase = rng.choice(aspects[aspect][polarity])
        # Deliberately *not* labeled with the aspect name (e.g. no "On
        # battery life: ..." prefix) — the phrase banks below mention the
        # aspect concept in natural, varied wording ("the battery easily
        # lasts all day") so training/reviews/analyze.py has to actually
        # detect the aspect from keywords, not read a literal label back.
        sentences.append(f"{phrase.capitalize()}.")

    if sentiment == "positive":
        sentences.append(rng.choice(CLOSING_POSITIVE))
    elif sentiment == "negative":
        sentences.append(rng.choice(CLOSING_NEGATIVE))
    else:
        sentences.append(rng.choice(CLOSING_NEUTRAL))

    title_bank = {
        "positive": ["Great buy", "Very satisfied", "Exceeded expectations"],
        "negative": ["Disappointed", "Not great", "Wouldn't buy again"],
        "mixed": ["Decent, with caveats", "It's okay", "Mixed experience"],
    }

    return Review(
        id=f"R{product['id']}-{review_index:02d}",
        product_id=product["id"],
        author=_real_author(rng),
        rating=star,
        title=rng.choice(title_bank[sentiment]),
        body=" ".join(sentences),
        verified_purchase=rng.random() < 0.85,
        helpful_votes=rng.randint(0, 120),
        created_at=f"{rng.choice([2024, 2025, 2026])}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
        is_fake_synthetic=False,
    )


def _fake_review(rng: random.Random, product: dict, review_index: int, author: str, day: str) -> Review:
    return Review(
        id=f"R{product['id']}-{review_index:02d}",
        product_id=product["id"],
        author=author,
        rating=5,
        title="Amazing",
        body=rng.choice(FAKE_PHRASES),
        verified_purchase=False,
        helpful_votes=rng.randint(0, 3),
        created_at=day,
        is_fake_synthetic=True,
    )


def generate_reviews(seed: int = SEED) -> list[Review]:
    rng = random.Random(seed)
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))

    reviews: list[Review] = []
    for product in products:
        n = rng.randint(MIN_REVIEWS_PER_PRODUCT, MAX_REVIEWS_PER_PRODUCT)
        for i in range(n):
            reviews.append(_real_review(rng, product, i))

    # Fake reviews are injected as a separate pass so they can share an
    # author and a tight posting-date burst across several products — the
    # actual bot-spam pattern the fake-review heuristic looks for.
    # Target ~FAKE_REVIEW_RATE of the *final* review count as fake, each
    # fake author posting to 4 products (a small burst, not a flood).
    num_real = len(reviews)
    reviews_per_fake_author = 4
    target_fake = int(num_real * FAKE_REVIEW_RATE / (1 - FAKE_REVIEW_RATE))
    num_fake_authors = max(1, round(target_fake / reviews_per_fake_author))
    for a in range(num_fake_authors):
        author = f"{rng.choice(FAKE_AUTHORS)}{rng.randint(100, 999)}"
        burst_day = f"{rng.choice([2025, 2026])}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}"
        targets = rng.sample(products, k=min(4, len(products)))
        for j, product in enumerate(targets):
            existing = sum(1 for r in reviews if r.product_id == product["id"])
            reviews.append(_fake_review(rng, product, existing, author, burst_day))

    reviews.sort(key=lambda r: (r.product_id, r.id))
    return reviews


def main() -> None:
    reviews = generate_reviews()
    OUTPUT_PATH.write_text(
        json.dumps([asdict(r) for r in reviews], indent=2) + "\n",
        encoding="utf-8",
    )
    num_fake = sum(1 for r in reviews if r.is_fake_synthetic)
    print(f"Generated {len(reviews)} reviews ({num_fake} synthetic fake) -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
