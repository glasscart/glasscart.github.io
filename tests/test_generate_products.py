from datasets.products.generate import SEED, generate_products


def test_generation_is_deterministic():
    first = generate_products(SEED)
    second = generate_products(SEED)
    assert [p.id for p in first] == [p.id for p in second]
    assert [p.price for p in first] == [p.price for p in second]


def test_ids_are_unique_and_sequential():
    products = generate_products(SEED)
    ids = [p.id for p in products]
    assert len(ids) == len(set(ids))
    assert ids == sorted(ids)


def test_every_product_has_required_fields():
    for product in generate_products(SEED):
        assert product.title
        assert product.description
        assert product.category
        assert product.price > 0
        assert 1.0 <= product.rating <= 5.0
        assert product.currency == "USD"
