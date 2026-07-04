"""Fetch real, permissively-licensed stock photos for the product catalog
from Wikimedia Commons — no API key, no paid service, no scraping (the
Commons API is a public, keyless, rate-limit-friendly JSON API meant for
exactly this kind of use).

Products are combinatorial (`{Adjective} {Noun} — {Material}`, see
datasets/products/generate.py) — there is no way to source a distinct
real photo for e.g. "Ergonomic Wireless Headphones" vs. "Travel-Ready
Wireless Headphones" specifically, since neither exists. Instead, this
fetches **one representative photo per noun** (104 distinct nouns across
10 categories) and reuses it across every variant of that noun, the same
way a real combinatorial catalog often shows one base product photo
across color/material options.

Only images licensed CC0, CC-BY, or CC-BY-SA are used (redistribution-safe,
with attribution — recorded per noun in `images/ATTRIBUTION.json`). A
noun with no sufficiently relevant, appropriately-licensed match is left
without an image entirely — `apps/web/src/components/ProductImage.tsx`
already falls back to the procedural placeholder for any product without
a generated image, so this doesn't need special-case handling on the
frontend.

Matching a short, generic noun against a general-purpose image archive is
genuinely unreliable: an early version of this script picked the highest
keyword-overlap match out of Commons' top 10 results and produced results
ranging from fine to actively bad (a 19th-century painting for "Card
Game," a WWII grenade-production photo for "Sticky Note Pack," because
both share the word "sticky"). The current approach is deliberately more
conservative: it trusts Commons' own search relevance ranking instead of
re-ranking by keyword overlap, requires *every* significant word in the
noun to appear in a candidate's title (not just one), and rejects a
sizeable blocklist of historical/artwork/military/document keywords (see
NEGATIVE_KEYWORDS). This eliminates most bad matches but not all —
**every accepted match was still visually reviewed by hand before being
committed** (see the review log referenced in datasets/products/
DATASET_CARD.md). Nouns with no acceptable candidate are simply skipped,
in favor of the honest procedural placeholder over a wrong photo.

Usage:
    uv run datasets/products/fetch_stock_photos.py
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import generate  # noqa: E402  (CATEGORIES vocabulary lives here)

PRODUCTS_PATH = Path(__file__).parent / "products.json"
IMAGES_DIR = Path(__file__).parent / "images"
ATTRIBUTION_PATH = IMAGES_DIR / "ATTRIBUTION.json"

API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "GlassCart/1.0 (https://github.com/glasscart/glasscart.github.io; educational demo, non-commercial)"
THUMB_WIDTH = 640
CANDIDATES_PER_QUERY = 10

ALLOWED_LICENSES = {"cc0", "cc-by", "cc-by-2.0", "cc-by-3.0", "cc-by-4.0", "cc-by-sa-2.0", "cc-by-sa-3.0", "cc-by-sa-4.0", "public domain", "pd"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
STOPWORDS = {"set", "kit", "pack", "pouch", "the", "a", "an", "of", "for"}

# A first automated pass at this (see git history) matched candidates by
# naive keyword overlap alone and produced genuinely bad results: a 19th-
# century painting for "Card Game," a WWII grenade-production photo for
# "Sticky Note Pack" (shared word: "sticky"), a wartime medical-treatment
# photo for "Training Treat Pouch" (shared word: "treat"). Short/common
# nouns collide with unrelated Commons content constantly. This blocklist
# — plus requiring *every* significant noun word to appear, not just one
# (see _best_candidate) — catches most of that; every accepted match is
# still visually reviewed by hand before shipping (see
# datasets/products/DATASET_CARD.md).
NEGATIVE_KEYWORDS = {
    # historical / artwork / museum
    "painting", "attributed", "engraving", "illustration", "drawing", "sketch",
    "portrait", "sculpture", "statue", "manuscript", "postcard", "stamp", "coin",
    "vintage", "antique", "museum", "exhibition", "gallery", "woodcut", "etching",
    # military / conflict / medical
    "military", "army", "navy", "marine", "war", "combat", "weapon", "grenade",
    "bomb", "soldier", "troops", "operation", "nara", "injury", "wound", "medic",
    "casualty", "gun", "rifle", "ammunition",
    # documents / print media
    "caption", "advertisement", "poster", "magazine", "newspaper", "manuscript",
    # generic irrelevant
    "flag", "logo", "diagram", "coat of arms", "map", "figure",
}


# Even after every automated filter above, a second full pass (every
# accepted match opened and looked at, not just its title) still rejected
# 11 of the 25 nouns that passed the filters — a 44% false-positive rate
# despite the blocklist, full-word-coverage, and historical-year checks.
# None of these are things a smarter regex would have caught; they needed
# a human looking at the actual pixels. Recorded here (by exact Commons
# file title) so a future re-run of this script doesn't silently
# resurrect them:
#   - Automatic Feeder -> "Automatic Fish Feeder (51372009281).jpg":
#     an aquaculture pond feeder rig, not a pet-bowl-style feeder.
#   - Bike Helmet -> "Bike helmet lamps jeh.jpg": a filthy, DIY-modified
#     helmet photographed on a couch, not a product shot.
#   - Blender -> "Mercury render with Blender 01.png": a 3D render of the
#     planet Mercury made with the Blender *software* — the noun matched
#     the tool that made the image, not a kitchen blender.
#   - Hair Dryer -> "Hair dryer in a bag in the hotel bathroom.jpg": shows
#     an opaque drawstring bag embroidered "HAIR DRYER", not the dryer.
#   - Notebook Set -> "Notebook writing.jpg": a messy personal homework
#     photo, not a notebook product.
#   - Reference Manual -> "Geographic Areas Reference Manual Figure
#     10-1.png": a diagram *from inside* the manual, not a photo of it.
#   - Sleeping Bag -> "19th century knowledge hiking and camping sheepskin
#     knapsack sleeping bag.jpg": an antique engraving; "19th century" is
#     spelled out in words, which the digit-year regex can't catch.
#   - Spice Set -> "Tiffany - Spice set in presentation box.jpg": an
#     antique Louis Comfort Tiffany museum piece in a display case.
#   - Storage Containers -> "Storage containers in Svalbard Global Seed
#     Vault 01.jpg": an industrial warehouse scene with a person in it.
#   - Sun Hat -> "The Sun Has Got His Hat On.jpg": a vintage sheet-music
#     cover — the sun-wearing-a-hat cartoon is the song's mascot, not a
#     product.
#   - Whiteboard -> "Hang Whiteboard On Door With Over The Door Hooks.png":
#     a hand-drawn design sketch, not a photo of a whiteboard.
#   - Hair Dryer -> "Hair dryer in a bag in the hotel bathroom.jpg": shows
#     an opaque drawstring bag embroidered "HAIR DRYER", not the dryer
#     itself (a second crop of the same photo, "...with label legible",
#     turned up on a later re-run and needed adding here too).
REJECTED_COMMONS_TITLES = {
    "File:Bike helmet lamps jeh.jpg",
    "File:Mercury render with Blender 01.png",
    "File:Hair dryer in a bag in the hotel bathroom.jpg",
    "File:Hair dryer in a bag in the hotel bathroom (with label legible).jpg",
    "File:Notebook writing.jpg",
    "File:19th century knowledge hiking and camping sheepskin knapsack sleeping bag.jpg",
    "File:Tiffany - Spice set in presentation box.jpg",
    "File:Storage containers in Svalbard Global Seed Vault 01.jpg",
    "File:The Sun Has Got His Hat On.jpg",
    "File:Hang Whiteboard On Door With Over The Door Hooks.png",
    "File:Movable Whiteboard Goes Around Table.png",
}


# Two nouns exhausted their entire top-10 Commons result set across three
# rounds of hand review without ever surfacing a real product photo:
# "Reference Manual" only returns illustrations/diagrams from actual
# reference manuals (never a photo of one — two different diagram/cover-art
# titles turned up across three re-runs, see REJECTED_COMMONS_TITLES'
# history in git log for the earlier ones), and "Automatic Feeder" only
# returns industrial aquaculture/fish-farm feeder rigs (Commons simply has
# no consumer pet-feeder photography under this term — three different
# fish-feeder photos turned up in turn). Rather than keep extending
# REJECTED_COMMONS_TITLES one Commons upload at a time, these nouns are
# skipped outright — the honest procedural placeholder beats a fourth
# wrong photo.
FORCE_SKIP_NOUNS = {"Reference Manual", "Automatic Feeder"}


def _has_negative_keyword(title: str, description: str) -> bool:
    text = f"{title} {description}".lower()
    return any(kw in text for kw in NEGATIVE_KEYWORDS)


def _looks_historical(title: str, description: str) -> bool:
    """Flags likely pre-1990 photos/artifacts, which are almost never what
    a product-catalog photo should look like for these categories. Catches
    both digit years ("1957") and spelled-out era references ("19th
    century") — the latter slipped through an earlier, digit-only version
    of this check (see REJECTED_COMMONS_TITLES' "Sleeping Bag" entry)."""
    text = f"{title} {description}".lower()
    if re.search(r"\b(1[6-9]\d{2}|19[0-8]\d)\b", text):
        return True
    return bool(re.search(r"\b\d{1,2}(st|nd|rd|th)[\s-]century\b", text)) or "century" in text


def _api_get(params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(f"{API_URL}?{query}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _search_candidates(noun: str) -> list[dict]:
    data = _api_get(
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": noun,
            "gsrnamespace": 6,  # File: namespace
            "gsrlimit": CANDIDATES_PER_QUERY,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|mime",
            "iiurlwidth": THUMB_WIDTH,
        }
    )
    pages = data.get("query", {}).get("pages", {})
    return list(pages.values())


def _license_of(page: dict) -> str:
    info = (page.get("imageinfo") or [{}])[0]
    return (info.get("extmetadata", {}).get("LicenseShortName", {}).get("value") or "").strip().lower()


def _extension_of(title: str) -> str:
    return Path(title).suffix.lower()


def _significant_words(noun: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[a-zA-Z]+", noun) if w.lower() not in STOPWORDS}


def _covers_all_words(noun_words: set[str], title: str) -> bool:
    title_words = {w.lower() for w in re.findall(r"[a-zA-Z]+", title)}
    return noun_words.issubset(title_words)


def _best_candidate(noun: str) -> dict | None:
    if noun in FORCE_SKIP_NOUNS:
        return None
    try:
        candidates = _search_candidates(noun)
    except Exception as e:
        print(f"  search failed for {noun!r}: {e}")
        return None

    noun_words = _significant_words(noun)

    # Deliberately *not* re-ranked by our own scoring — Commons' own search
    # relevance ordering is trusted; the first candidate to pass every
    # filter (license, file type, full noun-word coverage, no negative
    # keyword, not obviously historical) is taken. A first version of this
    # function re-ranked by naive keyword overlap and that reordering was
    # itself part of why bad matches won (see NEGATIVE_KEYWORDS' docstring).
    for page in candidates:
        title = page.get("title", "")
        description = page.get("imageinfo", [{}])[0].get("extmetadata", {}).get("ImageDescription", {}).get("value", "")
        if title in REJECTED_COMMONS_TITLES:
            continue
        if _extension_of(title) not in ALLOWED_EXTENSIONS:
            continue
        if _license_of(page) not in ALLOWED_LICENSES:
            continue
        if not noun_words or not _covers_all_words(noun_words, title):
            continue
        if _has_negative_keyword(title, description):
            continue
        if _looks_historical(title, description):
            continue
        return page

    return None


def _download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
        f.write(resp.read())


def main() -> None:
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    products_by_noun: dict[str, list[dict]] = {}
    for category, spec in generate.CATEGORIES.items():
        for noun in spec["nouns"]:
            products_by_noun[noun] = [p for p in products if p["category"] == category and noun in p["title"]]

    attribution: dict[str, dict] = {}
    found, skipped = 0, 0

    for noun, matching_products in products_by_noun.items():
        if not matching_products:
            continue
        best = _best_candidate(noun)
        time.sleep(0.2)  # polite delay between requests to a shared public API

        if best is None:
            print(f"SKIP  {noun!r}: no sufficiently relevant, permissively-licensed match found")
            skipped += 1
            continue

        info = (best.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata", {})
        thumb_url = info.get("thumburl") or info.get("url")
        raw_ext = _extension_of(best["title"]) or ".jpg"
        ext = ".jpg" if raw_ext == ".jpeg" else raw_ext

        image_bytes_paths = []
        try:
            for product in matching_products:
                dest = IMAGES_DIR / f"{product['id']}{ext}"
                _download(thumb_url, dest)
                image_bytes_paths.append(dest)
        except Exception as e:
            print(f"FAIL  {noun!r}: download error: {e}")
            for p in image_bytes_paths:
                p.unlink(missing_ok=True)
            skipped += 1
            continue

        attribution[noun] = {
            "commons_title": best["title"],
            "source_url": info.get("descriptionurl"),
            "artist": re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "unknown")),
            "license": meta.get("LicenseShortName", {}).get("value", "unknown"),
            "license_url": meta.get("LicenseUrl", {}).get("value", ""),
            # Without the dot, so the frontend can build `images/{id}.{extension}`
            # directly instead of re-deriving it from commons_title.
            "extension": ext.lstrip("."),
            "product_ids": [p["id"] for p in matching_products],
        }
        print(f"OK    {noun!r} -> {best['title']} ({meta.get('LicenseShortName', {}).get('value')})")
        found += 1

    ATTRIBUTION_PATH.write_text(json.dumps(attribution, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"\n{found} nouns matched, {skipped} skipped (no image; procedural placeholder will be used)")
    print(f"-> {IMAGES_DIR}\n-> {ATTRIBUTION_PATH}")


if __name__ == "__main__":
    main()
