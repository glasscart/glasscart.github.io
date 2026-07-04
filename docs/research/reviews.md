# Research Notes: Review Sentiment, Aspect Extraction & Fake-Review Detection

> Bibliography and design rationale for GlassCart's reviews subsystem: a from-scratch,
> lexicon-based sentiment scorer, keyword-based aspect extraction, and a rule-based
> fake-review heuristic, run entirely offline over a synthetic review corpus. Like the other
> subsystem research notes, this is written from what actually drove the implementation.

---

## 1. Lexicon-Based Sentiment Analysis

**Explanation.** Before (and alongside) trained sentiment classifiers, lexicon-based methods score text by summing the polarity of the words it contains, using a dictionary of word → sentiment weight built by hand or from crowd-sourced ratings. They need no training data or GPU, run in microseconds, and — critically for this project — are fully inspectable: every point of a score can be traced to a specific word in a specific dictionary entry, unlike a trained model's weights.

**Citations.**
- Hutto, C. J., & Gilbert, E. (2014). *VADER: A Parsimonious Rule-Based Model for Sentiment Analysis of Social Media Text*. In Proceedings of the Eighth International AAAI Conference on Weblogs and Social Media (ICWSM-14). https://ojs.aaai.org/index.php/ICWSM/article/view/14550
- Nielsen, F. Å. (2011). *A New ANEW: Evaluation of a Word List for Sentiment Analysis in Microblogs* (the AFINN word list). arXiv:1103.2903. https://arxiv.org/abs/1103.2903

**Used in GlassCart:** `training/reviews/lexicon.py` is a hand-written word-polarity lexicon in the same family as AFINN/VADER — word weights on a roughly -3..+3 scale, plus VADER-style negation flipping and intensifier scaling. It is not copied from either source (see the model card's "Training Data" section for why an independent lexicon matters here specifically); it borrows the *technique*, not the data.

---

## 2. Negation and Intensifier Handling

**Explanation.** A naive bag-of-words sentiment sum gets "not good" and "good" exactly backwards. VADER's contribution (among others) was a set of simple, effective heuristics for handling negation (flip the sign of a sentiment word if a negation word precedes it within a small window) and intensifiers/degree modifiers (scale a sentiment word's magnitude when preceded by "very," "extremely," etc.) without needing a full syntactic parse.

**Citations.**
- Hutto, C. J., & Gilbert, E. (2014). *VADER* (as cited in §1) — §3.1–3.2 describe the negation and intensifier/booster heuristics this implementation adapts.
- Polanyi, L., & Zaenen, A. (2006). *Contextual Valence Shifters*. In Computing Attitude and Affect in Text: Theory and Applications, 1–10. Springer. https://doi.org/10.1007/1-4020-4102-0_1 — earlier foundational work on how negation and modifiers shift sentiment polarity.

**Used in GlassCart:** `lexicon.py`'s `score_text` looks at the 3 tokens preceding each sentiment word for a negation, and tracks a "pending intensity" multiplier set by the token immediately before a sentiment word. This is a deliberately simplified version of VADER's own rules (no exclamation-mark boosting, no all-caps emphasis, no contrastive-conjunction handling for "but") — sized to be read end-to-end rather than to match VADER's benchmark performance.

---

## 3. Aspect-Based Sentiment Analysis (ABSA)

**Explanation.** Overall review sentiment hides useful structure: a review can be positive about battery life and negative about price in the same three sentences. Aspect-Based Sentiment Analysis extracts sentiment *per aspect* (a product attribute like "battery life" or "price") rather than one score per document. Approaches range from simple keyword/rule-based aspect detection to full syntactic-dependency parsing to end-to-end trained models; keyword-based detection — checking whether any of a small set of trigger words for an aspect appears in a sentence, then scoring that sentence — is the simplest member of the family and the one used here.

**Citations.**
- Hu, M., & Liu, B. (2004). *Mining and Summarizing Customer Reviews*. In Proceedings of KDD '04, 168–177. https://doi.org/10.1145/1014052.1014073 — foundational paper establishing feature/aspect-based opinion mining from product reviews, including frequency-based feature (aspect) extraction.
- Liu, B. (2012). *Sentiment Analysis and Opinion Mining*. Synthesis Lectures on Human Language Technologies, Morgan & Claypool. https://doi.org/10.2200/S00416ED1V01Y201204HLT016 — Chapter 5 surveys aspect extraction methods including keyword/rule-based approaches.

**Used in GlassCart:** `training/reviews/analyze.py`'s `ASPECT_KEYWORDS` maps a handful of product aspects per category to trigger keywords (e.g. Electronics' "connectivity" triggers on "connect"/"connection"/"pairing"), matched sentence-by-sentence, with each matching sentence scored independently by the same lexicon from §1. This is real, working keyword-based ABSA, not a lookup of a label — `datasets/reviews/generate.py` deliberately never writes an aspect's name into the generated review text, specifically so this step has to detect the aspect from context.

---

## 4. Fake Review / Opinion Spam Detection

**Explanation.** Review-fraud detection research identifies fake/spam reviews using signals like duplicate or near-duplicate content across reviews, unusual reviewer behavior (bursts of activity, reviewing unrelated products in a short window), and linguistic differences between genuine and deceptive reviews (e.g. genuine reviews tend to include more specific, concrete detail; fake reviews skew toward generic, superlative language).

**Citations.**
- Jindal, N., & Liu, B. (2008). *Opinion Spam and Analysis*. In Proceedings of WSDM '08, 219–230. https://doi.org/10.1145/1341531.1341560 — foundational paper identifying duplicate/near-duplicate reviews and reviewer behavioral patterns as opinion-spam signals.
- Ott, M., Choi, Y., Cardie, C., & Hancock, J. T. (2011). *Finding Deceptive Opinion Spam by Any Stretch of the Imagination*. In Proceedings of ACL-HLT 2011, 309–319. https://aclanthology.org/P11-1032/ — establishes that deceptive reviews are linguistically distinguishable from genuine ones (e.g. less concrete/specific detail), motivating "genericness" as a usable signal.
- Mukherjee, A., Venkataraman, V., Liu, B., & Glance, N. (2013). *What Yelp Fake Review Filter Might Be Doing?* In Proceedings of ICWSM 2013. https://ojs.aaai.org/index.php/ICWSM/article/view/14389 — behavioral signals (posting bursts, reviewer activity patterns) used by a real production fake-review filter.

**Used in GlassCart:** `training/reviews/analyze.py`'s fake-review heuristic combines three of these documented signal families directly: duplicate text (Jindal & Liu), posting-burst behavior across unrelated products (Mukherjee et al.), and generic/non-specific language approximated by "short, punctuation-heavy, no detected aspect mentions" (a crude proxy for Ott et al.'s concreteness finding — real genuine reviews mention specific product aspects; the synthetic fake reviews here, by construction, don't). The heuristic is real and based on real literature; what's synthetic is the *benchmark* it's evaluated against (see §5) — the underlying detection logic isn't fabricated for this project.

---

## 5. Evaluating a Heuristic Against Data It Was Designed to Catch

**Explanation.** A detector evaluated only against a test set built with the exact pattern it was designed to detect can score perfectly without that score meaning the detector generalizes to anything else — a well-known trap in any evaluation methodology, not specific to fake-review detection.

**Citations.** (methodology, not a specific paper — but see Mukherjee et al. 2013, cited in §4, for a real-world discussion of how hard *validating* a fake-review filter is, precisely because ground truth is scarce)

**Used in GlassCart:** `datasets/reviews/generate.py`'s synthetic `is_fake_synthetic` label and `training/reviews/analyze.py`'s fake-review heuristic are two independent things — the dataset generator constructs one specific bot-spam pattern (duplicate text, posting bursts, generic language) and labels it; the heuristic was written from the fraud-detection literature (§4) to catch that *class* of pattern generally, not fit to this dataset's specific instances. It still scores near-perfectly here, and the model card is explicit that this reflects "the test matches the method by construction," not evidence of real-world skill — the alternative (reporting no evaluation at all) would hide information a reader needs to correctly discount the number.
