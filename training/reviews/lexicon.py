"""A small, hand-written sentiment lexicon and scorer.

Word-polarity sentiment lexicons (AFINN, VADER, and similar) assign a
positive or negative weight to individual words, then score text by
summing the weights of the words it contains, adjusted for negation and
intensifiers. This is the classic "lexicon-based" approach to sentiment
analysis — real, well-established, and (unlike a trained classifier) fully
inspectable: every word's contribution to a score can be read straight out
of a dictionary. See docs/research/reviews.md for the primary sources.

This lexicon is hand-written for this project, not copied from AFINN/VADER
or any other existing list, and deliberately covers general product-review
vocabulary rather than being fit to datasets/reviews/generate.py's own
phrase banks — using the same phrases the generator used to score its own
output would be circular. It is intentionally small (~130 words): a real
production system would use a lexicon with tens of thousands of entries
(or a trained model); this one is sized to be readable end-to-end, matching
the project's `bm25.ts`/`hybrid.ts` precedent of favoring a from-scratch,
inspectable implementation over an opaque one, even at the cost of some
coverage.
"""

from __future__ import annotations

import re

# Word -> polarity weight. Roughly -3..+3, matching the scale AFINN uses,
# so magnitudes are comparable to what readers of the sentiment-analysis
# literature would expect.
LEXICON: dict[str, float] = {
    # Strong positive
    "excellent": 3.0, "amazing": 3.0, "fantastic": 3.0, "perfect": 3.0, "incredible": 3.0,
    "outstanding": 3.0, "love": 2.5, "loved": 2.5, "best": 2.5, "wonderful": 2.5,
    "impressive": 2.5, "flawless": 3.0, "exceeded": 2.0, "obsessed": 2.5, "premium": 2.0,
    # Mild positive
    "good": 1.5, "great": 2.0, "nice": 1.0, "solid": 1.5, "sturdy": 1.5, "durable": 1.5,
    "comfortable": 1.5, "reliable": 1.5, "easy": 1.0, "smooth": 1.0, "happy": 1.5,
    "satisfied": 1.5, "recommend": 1.5, "recommended": 1.5, "value": 1.0, "worth": 1.0,
    "quality": 1.0, "fast": 1.0, "convenient": 1.0, "clean": 1.0, "pleasant": 1.5,
    "subtle": 0.5, "engaging": 1.5, "beautiful": 2.0, "beautifully": 2.0, "sleek": 1.0,
    "intuitive": 1.5, "roomy": 1.0, "lightweight": 1.0, "effective": 1.5, "works": 1.0,
    "glad": 1.5, "pleased": 1.5, "consistently": 0.5, "instantly": 0.5, "rock": 0.5,
    "delighted": 2.0,
    # Strong negative
    "terrible": -3.0, "horrible": -3.0, "awful": -3.0, "worst": -3.0, "disgusting": -3.0,
    "broken": -2.5, "useless": -2.5, "garbage": -3.0, "junk": -2.5, "unacceptable": -2.5,
    "disappointing": -2.0, "disappointed": -2.0, "hazard": -2.5, "destroyed": -2.0,
    # Mild negative
    "bad": -1.5, "cheap": -1.0, "flimsy": -1.5, "poor": -1.5, "uncomfortable": -1.5,
    "unreliable": -1.5, "confusing": -1.0, "difficult": -1.0, "hard": -0.5, "slow": -1.0,
    "loose": -1.0, "greasy": -1.0, "sticky": -1.0, "overpriced": -1.5, "underwhelming": -1.5,
    "stale": -1.5, "artificial": -0.5, "questionable": -1.0, "impractical": -1.0,
    "fell": -1.0, "wore": -0.5, "drains": -1.0, "dropping": -1.0, "loses": -1.0,
    "lost": -0.5, "wish": -0.5, "unpleasant": -1.5, "overpowering": -1.0, "bulkier": -0.5,
    "bulky": -0.5, "smaller": -0.5, "shorter": -0.5, "padded": -0.5, "inconsistent": -1.0,
    "dry": -0.5, "hazardous": -2.0, "cracked": -1.5, "fiddly": -1.0,
    # Negation words
    "not": None, "no": None, "never": None, "n't": None, "without": None, "hardly": None,
    # Intensifiers (multiply the next sentiment word's weight)
    "very": 1.5, "extremely": 2.0, "incredibly": 2.0, "really": 1.3, "totally": 1.5,
    "surprisingly": 1.3, "absolutely": 1.8, "barely": 0.5,
}

NEGATIONS = {w for w, v in LEXICON.items() if v is None}
INTENSIFIERS = {"very", "extremely", "incredibly", "really", "totally", "surprisingly", "absolutely", "barely"}

_WORD_RE = re.compile(r"[a-z']+")


def tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


def score_text(text: str) -> float:
    """Sums word polarities with simple negation flipping and intensifier scaling.

    Negation: a negation word within the 3 preceding tokens flips the sign
    of a sentiment word ("not good" -> negative). Intensifiers scale the
    *next* sentiment word's magnitude ("very good" -> stronger positive).
    This is a deliberately simplified version of the negation/intensifier
    handling VADER popularized — see docs/research/reviews.md.
    """
    tokens = tokenize(text)
    total = 0.0
    count = 0
    pending_intensity = 1.0
    for i, tok in enumerate(tokens):
        if tok in INTENSIFIERS:
            pending_intensity = LEXICON[tok]
            continue
        weight = LEXICON.get(tok)
        if weight is None or tok in NEGATIONS:
            pending_intensity = 1.0
            continue
        window = tokens[max(0, i - 3):i]
        negated = any(w in NEGATIONS for w in window)
        signed_weight = -weight if negated else weight
        total += signed_weight * pending_intensity
        count += 1
        pending_intensity = 1.0
    if count == 0:
        return 0.0
    # Average rather than sum so review length doesn't dominate the score —
    # a one-sentence and a five-sentence review with the same intensity of
    # opinion should land at a similar sentiment score.
    return total / count
