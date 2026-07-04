"""Synthetic product catalog generator for GlassCart.

Generates a deterministic, seeded catalog of products across multiple
categories by combining templated attributes. No real brand names, no
scraped content, no copyrighted material — every field is synthesized.

Usage:
    uv run datasets/products/generate.py
"""

from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from pathlib import Path

SEED = 20260704
OUTPUT_PATH = Path(__file__).parent / "products.json"

# ---------------------------------------------------------------------------
# Vocabulary. Each category defines the building blocks used to synthesize
# titles, descriptions and tags. Nothing here references a real brand.
# ---------------------------------------------------------------------------

CATEGORIES: dict[str, dict] = {
    "Electronics": {
        "nouns": ["Wireless Headphones", "Bluetooth Speaker", "USB-C Hub", "Mechanical Keyboard",
                   "Smart Watch", "Portable Charger", "Webcam", "Noise-Cancelling Earbuds",
                   "4K Monitor", "Laptop Stand", "Wireless Mouse", "Ring Light"],
        "adjectives": ["Compact", "Ultra-Slim", "Rugged", "Ergonomic", "Foldable", "Backlit",
                       "High-Fidelity", "Long-Battery", "Fast-Charging", "Travel-Ready"],
        "materials": ["Aluminum", "Carbon Fiber", "Recycled Plastic", "Brushed Metal"],
        "tags": ["gadgets", "audio", "office", "gaming", "productivity"],
        "price_range": (14.99, 349.99),
    },
    "Home & Kitchen": {
        "nouns": ["Chef Knife Set", "Cast Iron Skillet", "Air Fryer", "Ceramic Dinner Set",
                   "Stand Mixer", "Coffee Grinder", "Storage Containers", "Cutting Board",
                   "Electric Kettle", "Blender", "Bamboo Utensil Set", "Non-Stick Pan"],
        "adjectives": ["Dishwasher-Safe", "Stackable", "Space-Saving", "Heavy-Duty",
                       "Non-Toxic", "Even-Heating", "Quick-Clean", "Countertop"],
        "materials": ["Stainless Steel", "Bamboo", "Cast Iron", "BPA-Free Plastic", "Ceramic"],
        "tags": ["kitchen", "cooking", "home", "dining"],
        "price_range": (9.99, 199.99),
    },
    "Books": {
        "nouns": ["Beginner's Guide", "Field Notebook", "Cookbook", "Illustrated Atlas",
                   "Puzzle Collection", "Short Story Anthology", "Reference Manual",
                   "Sketchbook", "Poetry Collection", "Study Planner"],
        "adjectives": ["Illustrated", "Pocket-Sized", "Annotated", "Beginner-Friendly",
                       "Comprehensive", "Updated", "Collectible"],
        "materials": ["Hardcover", "Paperback", "Spiral-Bound"],
        "tags": ["books", "learning", "reference", "hobby"],
        "price_range": (6.99, 44.99),
    },
    "Clothing": {
        "nouns": ["Running Jacket", "Cotton T-Shirt", "Wool Beanie", "Denim Jacket",
                   "Yoga Leggings", "Rain Poncho", "Hiking Socks", "Fleece Hoodie",
                   "Canvas Sneakers", "Sun Hat"],
        "adjectives": ["Breathable", "Water-Resistant", "Quick-Dry", "Lightweight",
                       "Stretch-Fit", "Reinforced", "All-Season"],
        "materials": ["Organic Cotton", "Recycled Polyester", "Merino Wool", "Canvas"],
        "tags": ["apparel", "outdoor", "fitness", "everyday"],
        "price_range": (11.99, 89.99),
    },
    "Sports & Outdoors": {
        "nouns": ["Yoga Mat", "Camping Tent", "Trekking Poles", "Insulated Water Bottle",
                   "Resistance Bands Set", "Sleeping Bag", "Bike Helmet", "Fishing Rod",
                   "Dumbbell Set", "Foam Roller"],
        "adjectives": ["Portable", "Weatherproof", "Adjustable", "Anti-Slip",
                       "Ultra-Light", "Shock-Absorbing", "Packable"],
        "materials": ["Ripstop Nylon", "Aircraft-Grade Aluminum", "EVA Foam", "Neoprene"],
        "tags": ["outdoor", "fitness", "camping", "sports"],
        "price_range": (12.99, 249.99),
    },
    "Beauty": {
        "nouns": ["Facial Serum", "Bamboo Hairbrush", "Sunscreen Lotion", "Lip Balm Set",
                   "Clay Face Mask", "Electric Toothbrush", "Nail Care Kit", "Body Wash",
                   "Makeup Brush Set", "Hair Dryer"],
        "adjectives": ["Fragrance-Free", "Fast-Absorbing", "Cruelty-Free", "Dermatologist-Tested",
                       "Hydrating", "Travel-Size", "Reusable"],
        "materials": ["Recyclable Glass", "Bamboo", "Silicone"],
        "tags": ["beauty", "skincare", "self-care", "wellness"],
        "price_range": (5.99, 59.99),
    },
    "Toys": {
        "nouns": ["Building Block Set", "Wooden Puzzle", "Remote Control Car", "Plush Toy",
                   "Board Game", "Modeling Clay Kit", "Kite", "Card Game",
                   "Science Experiment Kit", "Stacking Rings"],
        "adjectives": ["Educational", "Non-Toxic", "Screen-Free", "Age-Appropriate",
                       "Reusable", "Colorful", "Durable"],
        "materials": ["FSC-Certified Wood", "Recycled Cardboard", "Silicone", "ABS Plastic"],
        "tags": ["toys", "kids", "educational", "family"],
        "price_range": (7.99, 64.99),
    },
    "Grocery": {
        "nouns": ["Organic Trail Mix", "Cold-Brew Coffee Bags", "Herbal Tea Sampler",
                   "Whole Grain Pasta", "Extra Virgin Olive Oil", "Dark Chocolate Bar",
                   "Granola Cereal", "Sparkling Water Pack", "Nut Butter Jar", "Spice Set"],
        "adjectives": ["Organic", "Non-GMO", "Small-Batch", "Single-Origin",
                       "Low-Sugar", "Plant-Based", "Locally-Sourced"],
        "materials": ["Compostable Packaging", "Glass Jar", "Recyclable Pouch"],
        "tags": ["grocery", "pantry", "organic", "snacks"],
        "price_range": (3.99, 34.99),
    },
    "Office Supplies": {
        "nouns": ["Desk Organizer", "Notebook Set", "Standing Desk Converter", "Whiteboard",
                   "Fountain Pen", "Filing Cabinet", "Cable Management Tray", "Desk Lamp",
                   "Sticky Note Pack", "Ergonomic Chair Cushion"],
        "adjectives": ["Space-Saving", "Adjustable", "Modular", "Minimalist",
                       "Anti-Glare", "Foldable", "Sturdy"],
        "materials": ["Powder-Coated Steel", "Bamboo", "Recycled Cardboard", "MDF Wood"],
        "tags": ["office", "productivity", "desk", "organization"],
        "price_range": (6.99, 129.99),
    },
    "Pet Supplies": {
        "nouns": ["Dog Chew Toy", "Cat Scratching Post", "Pet Carrier", "Automatic Feeder",
                   "Orthopedic Pet Bed", "Grooming Brush", "Pet Water Fountain",
                   "Adjustable Harness", "Training Treat Pouch", "Litter Mat"],
        "adjectives": ["Durable", "Machine-Washable", "Chew-Resistant", "Non-Slip",
                       "Odor-Resistant", "Adjustable", "Compact"],
        "materials": ["Memory Foam", "Natural Rubber", "Recycled Fabric", "Stainless Steel"],
        "tags": ["pets", "home", "dog", "cat"],
        "price_range": (4.99, 89.99),
    },
}

DESCRIPTION_TEMPLATES = [
    "A {adjective_lower} {noun_lower} made from {material_lower}, designed for everyday {tag} use.",
    "This {material_lower} {noun_lower} combines a {adjective_lower} design with reliable performance for {tag} enthusiasts.",
    "Upgrade your {tag} routine with this {adjective_lower} {noun_lower}, built with {material_lower} for lasting durability.",
    "A {noun_lower} crafted from {material_lower}. {adjective} construction keeps it practical for daily {tag} use.",
]

SELLER_PREFIXES = ["North", "Cedar", "Harbor", "Willow", "Granite", "Maple", "River", "Summit",
                    "Alder", "Birch", "Coral", "Sage", "Terra", "Ivory", "Onyx"]
SELLER_SUFFIXES = ["Goods", "Supply Co.", "Workshop", "Collective", "Trading Post", "Studio",
                    "& Sons", "Provisions", "Outfitters", "Makers"]


@dataclass
class Product:
    id: str
    title: str
    description: str
    category: str
    brand: str
    seller_id: str
    price: float
    currency: str
    rating: float
    rating_count: int
    tags: list[str]
    material: str
    created_at: str


def _price(rng: random.Random, low: float, high: float) -> float:
    return round(rng.uniform(low, high), 2)


def _rating(rng: random.Random) -> float:
    # Skew ratings toward 3.5-5.0, mirroring real marketplace distributions.
    return round(min(5.0, max(1.0, rng.triangular(2.5, 5.0, 4.4))), 1)


def _created_at(rng: random.Random) -> str:
    year = rng.choice([2023, 2024, 2025, 2026])
    month = rng.randint(1, 12)
    day = rng.randint(1, 28)
    return f"{year:04d}-{month:02d}-{day:02d}"


def generate_products(seed: int = SEED) -> list[Product]:
    rng = random.Random(seed)
    sellers = [f"{p} {s}" for p in SELLER_PREFIXES for s in SELLER_SUFFIXES]
    rng.shuffle(sellers)

    products: list[Product] = []
    product_index = 0

    for category, spec in CATEGORIES.items():
        nouns = spec["nouns"]
        adjectives = spec["adjectives"]
        materials = spec["materials"]
        base_tags = spec["tags"]
        low, high = spec["price_range"]

        for noun in nouns:
            # Generate 3 variants per noun (different adjective/material combos)
            # so the catalog has near-duplicates for search/dedup to contend with.
            variant_adjectives = rng.sample(adjectives, k=min(3, len(adjectives)))
            for adjective in variant_adjectives:
                material = rng.choice(materials)
                template = rng.choice(DESCRIPTION_TEMPLATES)
                tag = rng.choice(base_tags)
                seller = sellers[product_index % len(sellers)]
                brand = seller.split(" ")[0]

                title = f"{adjective} {noun} — {material}"
                description = template.format(
                    adjective=adjective,
                    adjective_lower=adjective.lower(),
                    noun_lower=noun.lower(),
                    material_lower=material.lower(),
                    tag=tag,
                )

                products.append(
                    Product(
                        id=f"P{product_index:05d}",
                        title=title,
                        description=description,
                        category=category,
                        brand=brand,
                        seller_id=f"S{(product_index % len(sellers)):04d}",
                        price=_price(rng, low, high),
                        currency="USD",
                        rating=_rating(rng),
                        rating_count=rng.randint(0, 4200),
                        tags=sorted({tag, *rng.sample(base_tags, k=min(2, len(base_tags)))}),
                        material=material,
                        created_at=_created_at(rng),
                    )
                )
                product_index += 1

    return products


def main() -> None:
    products = generate_products()
    OUTPUT_PATH.write_text(
        json.dumps([asdict(p) for p in products], indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {len(products)} products -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
