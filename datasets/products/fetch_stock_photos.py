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
# Widened from 10 to 25 after the first two passes: several nouns' only
# acceptable candidate sat outside the top-10 (e.g. "Sleeping Bag"'s good
# match was position 14 once the bad top-10 entries were denylisted).
CANDIDATES_PER_QUERY = 25

ALLOWED_LICENSES = {"cc0", "cc-by", "cc-by-2.0", "cc-by-3.0", "cc-by-4.0", "cc-by-sa-2.0", "cc-by-sa-3.0", "cc-by-sa-4.0", "public domain", "pd"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
STOPWORDS = {"set", "kit", "pack", "pouch", "the", "a", "an", "of", "for"}

# Hand-picked, more literal search phrases for nouns whose bare noun is
# either a common-word collision risk (e.g. "Blender" the noun vs. Blender
# the 3D software) or too generic to find a specific-enough Commons match
# on its own. When present, this REPLACES the noun as both the search
# query and the basis for the full-word-coverage check (see
# _significant_words) — the override phrase describes what an acceptable
# candidate's title should actually contain, which for these nouns is not
# the same as the noun text taken literally.
QUERY_OVERRIDES: dict[str, str] = {
    "Blender": "blender jug kitchen",
    "Sun Hat": "sun hat clothing",
    "Spice Set": "spice rack bottles kitchen",
    "Reference Manual": "instruction manual book cover",
    "Automatic Feeder": "pet automatic feeder bowl",
    "4K Monitor": "led monitor screen computer",
    "Card Game": "playing cards deck",
    "Kite": "kite toy sky",
    "Litter Mat": "cat litter mat",
    "Grooming Brush": "dog grooming brush",
    "Nail Care Kit": "manicure set nail clippers",
    "Foam Roller": "foam roller fitness equipment",
    "Sticky Note Pack": "post-it notes pad",
    "Adjustable Harness": "dog harness",
    "Illustrated Atlas": "world atlas book",
    "Puzzle Collection": "puzzle book",
    "Non-Stick Pan": "frying pan kitchen",
    "Ceramic Dinner Set": "ceramic dinner plate set",
    # Round 2 of overrides — added after the first override attempt still
    # found nothing acceptable, in an expanded push for coverage across
    # every noun still relying on the procedural placeholder.
    "Wireless Headphones": "over-ear wireless headphones",
    "USB-C Hub": "usb-c hub adapter",
    "Mechanical Keyboard": "mechanical keyboard computer",
    "Portable Charger": "portable power bank charger",
    "Noise-Cancelling Earbuds": "wireless earbuds case",
    "Laptop Stand": "laptop riser stand desk",
    "Chef Knife Set": "chef knife set kitchen",
    "Cast Iron Skillet": "cast iron skillet pan",
    "Air Fryer": "air fryer kitchen appliance",
    "Stand Mixer": "stand mixer kitchen appliance",
    "Storage Containers": "plastic storage containers kitchen",
    "Bamboo Utensil Set": "bamboo kitchen utensils",
    "Beginner's Guide": "how-to guide book",
    "Field Notebook": "pocket notebook journal",
    "Cookbook": "cookbook recipe book",
    "Short Story Anthology": "short stories book",
    "Poetry Collection": "poetry book",
    "Study Planner": "student planner notebook",
    "Running Jacket": "running jacket athletic",
    "Cotton T-Shirt": "cotton t-shirt clothing",
    "Wool Beanie": "wool beanie hat",
    "Yoga Leggings": "yoga leggings pants",
    "Rain Poncho": "rain poncho waterproof",
    "Hiking Socks": "hiking socks wool",
    "Fleece Hoodie": "fleece hoodie jacket",
    "Canvas Sneakers": "canvas sneakers shoes",
    "Yoga Mat": "yoga mat exercise",
    "Insulated Water Bottle": "insulated water bottle steel",
    "Resistance Bands Set": "resistance band exercise",
    "Facial Serum": "facial serum bottle skincare",
    "Bamboo Hairbrush": "wooden hairbrush",
    "Sunscreen Lotion": "sunscreen bottle lotion",
    "Lip Balm Set": "lip balm stick",
    "Clay Face Mask": "clay face mask jar skincare",
    "Electric Toothbrush": "electric toothbrush",
    "Body Wash": "body wash bottle",
    "Hair Dryer": "hair dryer blow dryer appliance",
    "Wooden Puzzle": "wooden jigsaw puzzle",
    "Plush Toy": "plush toy stuffed animal",
    "Modeling Clay Kit": "modeling clay kit toy",
    "Science Experiment Kit": "science kit toy",
    "Stacking Rings": "stacking rings toy baby",
    "Organic Trail Mix": "trail mix nuts snack",
    "Cold-Brew Coffee Bags": "cold brew coffee bag",
    "Herbal Tea Sampler": "herbal tea bags box",
    "Whole Grain Pasta": "pasta box whole grain",
    "Granola Cereal": "granola cereal box",
    "Sparkling Water Pack": "sparkling water bottles",
    "Nut Butter Jar": "peanut butter jar",
    "Desk Organizer": "desk organizer office supplies",
    "Notebook Set": "notebook stationery",
    "Standing Desk Converter": "standing desk converter riser",
    "Whiteboard": "whiteboard dry erase board",
    "Filing Cabinet": "filing cabinet office",
    "Cable Management Tray": "cable management box",
    "Desk Lamp": "led desk lamp office",
    "Ergonomic Chair Cushion": "office chair seat cushion",
    "Dog Chew Toy": "dog chew toy",
    "Cat Scratching Post": "cat scratching post",
    "Pet Carrier": "pet carrier travel bag",
    "Orthopedic Pet Bed": "dog bed orthopedic foam",
    "Pet Water Fountain": "pet water fountain bowl",
    "Training Treat Pouch": "dog treat pouch training",
    # The bare noun matched "Central Building for Block of Two Setts (Sets)
    # of Barracks" — every significant word happened to appear across an
    # unrelated 19th-century architectural blueprint's title.
    "Building Block Set": "toy building blocks",
    # The bare noun's top candidates were consistently ornate antique
    # wall-mounted hand-crank grinders (rustic collectible style, not a
    # modern product) two rounds in a row — nothing keyword-detectable
    # about "antique aesthetic" exists, so the query itself is narrowed
    # toward a modern appliance instead.
    "Coffee Grinder": "electric coffee grinder machine",
}

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
    "ad", "coupon", "brochure", "catalog", "catalogue",
    # AI-generated content — Commons hosts some AI-generated images (often
    # tagged public domain, since AI output frequently can't be
    # copyrighted), which is exactly the kind of image this project
    # deliberately avoids shipping (see training/product_images/'s "built
    # and evaluated, not shipped" status in docs/roadmap.md) — a real photo
    # sourcing script accidentally shipping an AI-generated one would be a
    # direct contradiction. Caught the hard way: "Ring Light" matched a
    # DALL-E image of an anthropomorphic rhinoceros in a suit.
    "dall-e", "dall·e", "midjourney", "stable diffusion", "ai-generated",
    "ai generated", "generated by ai", "artstation", "generative ai",
    # generic irrelevant
    "flag", "logo", "diagram", "coat of arms", "map", "figure",
    # Repeat offenders: a specific Commons series/photographer/collection
    # kept resurfacing a wrong match for the same noun under a different
    # filename each time widening the candidate pool ran past the first
    # bad entry — blocking the whole series by name is more robust than
    # denylisting one accession number or angle at a time (see
    # REJECTED_COMMONS_TITLES for the individual titles these replaced).
    "junya watanabe",  # avant-garde runway/museum-archive denim jacket series
    "yale center for british art",  # digitized 19th-century artist sketchbook
    "cryptomeria japonica",  # nature photography where trekking poles are an incidental prop
    "mary mcleod bethune",  # preserved National Historic Site office exhibit, resurfaced for "Filing Cabinet" under two different filenames
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
#
# A fourth round — widening CANDIDATES_PER_QUERY from 10 to 25 and adding
# QUERY_OVERRIDES to chase full coverage — surfaced 18 more nouns' worth of
# candidates (new nouns, plus a few of the already-shipped nouns whose
# candidate shifted once the pool widened). 11 of those 18 were wrong:
#   - Air Fryer -> "Jeno's Pizza Rolls air fryer ad.jpg": a decades-old
#     magazine advertisement (with a 10-cent coupon) for a "FryBaby deep
#     fryer" — not even the right appliance, let alone a real product photo.
#   - Building Block Set -> "Central Building for Block of Two Setts (Sets)
#     of Barracks...jpg": a 19th-century architectural blueprint; "Building"
#     + "Block" + "Set(t)s" all happened to appear in an unrelated title.
#   - Coffee Grinder -> "Coffee grinder 2.jpg": three antique wall-mounted
#     hand-crank grinders — a collectible display, not a modern product.
#   - Denim Jacket -> "2002 Junya Watanabe for Comme des Garçons jacket,
#     blue denim jeans patchwork...jpg": an avant-garde museum/runway
#     costume-archive piece, not an ordinary commercial product photo.
#   - Desk Lamp -> "Retro desk lamp.jpg": a moody art-deco lounge/interior
#     shot (with a mirror and a framed photo in the background), not a
#     clean product photo.
#   - Fishing Rod -> "FMIB 44367 Messrs Farlow's Patent Reel and Rod
#     Rest...jpeg": a sepia 19th-century patent-illustration book scan.
#   - Laptop Stand -> "...Closed laptop rests on a black perforated stand
#     labeled THEATER 2...jpg": an AV equipment patch-panel rack in a
#     theater, not a desk laptop stand.
#   - Pet Carrier -> "Close-up of Plaid Pet Carrier Bag with Flower
#     Charm.jpg": too extreme a macro crop to read as "pet carrier" at a
#     glance — just fabric texture and a zipper charm.
#   - Ring Light -> "DALL-E - Professional model photo of anthropomorphic
#     rhinoceros wearing a business suit...jpg": an AI-generated (DALL-E)
#     image — see NEGATIVE_KEYWORDS' AI-generated-content entry, added
#     because of this exact miss.
#   - Sketchbook -> "Barbara Bodichon - Sketchbook...Yale Center for British
#     Art.jpg": a page from a 19th-century artist's museum sketchbook (a
#     watercolor painting), not a modern blank sketchbook product.
#   - Trekking Poles -> "Cryptomeria japonica with trekking poles on Mount
#     Horaiji.jpg": the poles are tiny incidental props leaning against a
#     giant tree trunk — the photo is about the tree.
#
# A fifth round re-ran with three of those same offenders now blocked by
# NEGATIVE_KEYWORDS phrase (Junya Watanabe, Yale Center for British Art,
# Cryptomeria japonica) rather than title — but "Coffee Grinder" surfaced a
# second bad candidate under a plain-enough filename that only a look at
# the actual photo caught it:
#   - Coffee Grinder -> "Coffee grinder with coffee.jpg": an ornate wooden
#     hand-crank grinder shot in a rustic/antique style — a collectible
#     display piece, not a modern product, and nothing in its title flags
#     it as such.
#
# A sixth round added ~65 more QUERY_OVERRIDES to chase coverage on every
# noun still relying on the placeholder — it only netted 2 nouns net (most
# overrides found nothing at all), and surfaced 4 more bad candidates:
#   - Bamboo Utensil Set -> "A Jungle Kitchen. Cooking in Bamboo
#     Utensils.jpg": a black-and-white colonial-era ethnographic photograph.
#   - Denim Jacket -> "Denim jacket with fox lining, Düsseldorf, November
#     2025.jpg": a busy candid street-fashion photo (person from behind,
#     mid-shopping, other brands' billboards and shopping bags filling the
#     frame) — not a product-focused shot despite being a genuine, modern,
#     dated photo of someone actually wearing a denim jacket.
#   - Filing Cabinet -> "Filing cabinet, office, Mary McLeod Bethune
#     Council House NHS.jpg": a preserved exhibit in a National Historic
#     Site, with a vintage civil-rights-era poster on top.
#   - Resistance Bands Set -> "...Neatly organized home gym closet
#     featuring exercise balls foam rollers and a resistance band
#     system.jpg": a cluttered closet interior; the bands are barely
#     visible among other equipment.
#
# "Filing Cabinet" resurfaced the same Mary McLeod Bethune Council House
# exhibit a second time under yet another filename ("Flower on filing
# cabinet..."), confirming it's a whole-series problem rather than one bad
# upload — moved to a NEGATIVE_KEYWORDS phrase entry instead of a third
# title here.
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
    "File:Jeno's Pizza Rolls air fryer ad.jpg",
    "File:Central Building for Block of Two Setts (Sets) of Barracks, Fort Hamilton, New York - DPLA - e1d856ebb299a51c4676e9000af32b58.jpg",
    "File:Coffee grinder 2.jpg",
    "File:2002 Junya Watanabe for Comme des Garçons jacket, blue denim jeans patchwork 01.jpg",
    "File:Retro desk lamp.jpg",
    "File:FMIB 44367 Messrs Farlow's Patent Reel and Rod Rest for Big Game Fishing.jpeg",
    "File:EFTA00001880 - Closed laptop rests on a black perforated stand labeled THEATER 2 in a professional audio setup.jpg",
    "File:Close-up of Plaid Pet Carrier Bag with Flower Charm.jpg",
    "File:DALL-E - Professional model photo of anthropomorphic rhinoceros wearing a business suit in a dark room, ring light shine on top of him.jpg",
    "File:Barbara Bodichon - Sketchbook - B1991.23.2(1) - Yale Center for British Art.jpg",
    "File:Cryptomeria japonica with trekking poles on Mount Horaiji.jpg",
    "File:Coffee grinder with coffee.jpg",
    "File:A Jungle Kitchen. Cooking in Bamboo Utensils.jpg",
    "File:Denim jacket with fox lining, Düsseldorf, November 2025.jpg",
    "File:Filing cabinet, office, Mary McLeod Bethune Council House NHS.jpg",
    "File:EFTA00000622 - Neatly organized home gym closet featuring exercise balls foam rollers and a resistance band system.jpg",
}


def _has_negative_keyword(title: str, description: str) -> bool:
    """Word-boundary matching, not substring, for plain single words — an
    earlier version used naive `kw in text`, which meant the entry "sketch"
    silently rejected every candidate for the noun "Sketchbook" (since
    "sketch" is a substring of "sketchbook"), and generic short entries
    like "war"/"gun"/"map"/"flag" could equally false-positive on unrelated
    words that merely contain them ("hardware", "burgundy", "mapping",
    "flagship"). Keywords containing a space or hyphen ("coat of arms",
    "dall-e") fall back to substring matching, since word-set membership
    doesn't apply to them and accidental collisions for a multi-word/
    hyphenated phrase are far less likely."""
    text = f"{title} {description}".lower()
    words = set(re.findall(r"[a-z0-9]+", text))
    for kw in NEGATIVE_KEYWORDS:
        if kw.isalnum():
            if kw in words:
                return True
        elif kw in text:
            return True
    return False


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


def _search_candidates(query: str) -> list[dict]:
    data = _api_get(
        {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": query,
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
    query = QUERY_OVERRIDES.get(noun, noun)
    try:
        candidates = _search_candidates(query)
    except Exception as e:
        print(f"  search failed for {noun!r}: {e}")
        return None

    # When an override is in play, the full-word-coverage check is against
    # the override phrase, not the noun itself — the override exists
    # precisely because the noun's own words are the wrong (or too
    # ambiguous) thing to require in a candidate's title. See QUERY_OVERRIDES.
    noun_words = _significant_words(query)

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
