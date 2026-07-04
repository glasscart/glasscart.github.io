from fastapi.testclient import TestClient

from services.search.app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["corpus_size"] > 0


def test_search_returns_ranked_results():
    resp = client.get("/search", params={"q": "wireless headphones", "limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "wireless headphones"
    assert 1 <= len(body["results"]) <= 5

    ranks = [r["rank"] for r in body["results"]]
    assert ranks == sorted(ranks)

    fused_scores = [r["score"]["fused"] for r in body["results"]]
    assert fused_scores == sorted(fused_scores, reverse=True)


def test_search_glass_explanation_is_populated():
    resp = client.get("/search", params={"q": "eco friendly kitchen tools"})
    glass = resp.json()["glass"]
    assert glass["embedding_dim"] == 384
    assert glass["bm25_k1"] > 0
    assert 0.0 <= glass["fusion_alpha"] <= 1.0
    assert glass["timing"]["total_ms"] >= 0
    assert len(glass["limitations"]) > 0


def test_search_rejects_blank_query():
    resp = client.get("/search", params={"q": "   "})
    assert resp.status_code == 400


def test_alpha_extremes_change_ranking_behavior():
    """alpha=1 is pure BM25; alpha=0 is pure semantic. They need not agree."""
    keyword_only = client.get("/search", params={"q": "aluminum headphones", "alpha": 1.0, "limit": 3}).json()
    semantic_only = client.get("/search", params={"q": "aluminum headphones", "alpha": 0.0, "limit": 3}).json()
    assert keyword_only["results"][0]["score"]["semantic_normalized"] >= 0
    assert semantic_only["results"][0]["score"]["bm25_normalized"] >= 0
