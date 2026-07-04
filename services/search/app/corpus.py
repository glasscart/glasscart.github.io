"""Loads the product catalog and precomputed embeddings into memory once."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from .config import EMBEDDINGS_PATH, MANIFEST_PATH, PRODUCTS_PATH

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


@dataclass(frozen=True)
class Corpus:
    products: list[dict]
    products_by_id: dict[str, dict]
    tokenized_docs: list[list[str]]
    embedding_matrix: np.ndarray  # (N, dim), L2-normalized rows, row order == products order
    embedding_ids: list[str]
    embedding_manifest: dict


@lru_cache(maxsize=1)
def load_corpus() -> Corpus:
    products = json.loads(PRODUCTS_PATH.read_text(encoding="utf-8"))
    products_by_id = {p["id"]: p for p in products}
    tokenized_docs = [tokenize(f"{p['title']} {p['description']}") for p in products]

    embeddings_raw = json.loads(EMBEDDINGS_PATH.read_text(encoding="utf-8"))
    embedding_ids = embeddings_raw["ids"]
    embedding_matrix = np.array(embeddings_raw["vectors"], dtype=np.float32)

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8")) if MANIFEST_PATH.exists() else {}

    if embedding_ids != [p["id"] for p in products]:
        # Re-align defensively in case artifacts were regenerated out of order.
        index_by_id = {pid: i for i, pid in enumerate(embedding_ids)}
        order = [index_by_id[p["id"]] for p in products]
        embedding_matrix = embedding_matrix[order]
        embedding_ids = [embedding_ids[i] for i in order]

    return Corpus(
        products=products,
        products_by_id=products_by_id,
        tokenized_docs=tokenized_docs,
        embedding_matrix=embedding_matrix,
        embedding_ids=embedding_ids,
        embedding_manifest=manifest,
    )
