from app.scrapers.models import AliProduct

_MOCK_DATA: list[AliProduct] = [
    AliProduct(
        product_id="mock001",
        title="Wireless Earbuds Pro Max",
        price_usd=15.99,
        sale_count_30d=5420,
        rating=4.9,
        image_url="https://ae01.alicdn.com/kf/mock001.jpg",
        product_url="https://www.aliexpress.com/item/mock001.html",
        category_id="",
    ),
    AliProduct(
        product_id="mock002",
        title="Phone Case Premium Clear",
        price_usd=5.99,
        sale_count_30d=3200,
        rating=5.0,
        image_url="https://ae01.alicdn.com/kf/mock002.jpg",
        product_url="https://www.aliexpress.com/item/mock002.html",
        category_id="",
    ),
    AliProduct(
        product_id="mock003",
        title="USB-C Cable Braided 3m",
        price_usd=3.99,
        sale_count_30d=8100,
        rating=4.8,  # below 4.9 — filtered by min_rating
        image_url="https://ae01.alicdn.com/kf/mock003.jpg",
        product_url="https://www.aliexpress.com/item/mock003.html",
        category_id="",
    ),
    AliProduct(
        product_id="mock004",
        title="Screen Protector Tempered Glass Pack",
        price_usd=2.99,
        sale_count_30d=6300,
        rating=4.9,
        image_url="https://ae01.alicdn.com/kf/mock004.jpg",
        product_url="https://www.aliexpress.com/item/mock004.html",
        category_id="",
    ),
    AliProduct(
        product_id="mock005",
        title="Wireless Charger Pad 15W",
        price_usd=12.99,
        sale_count_30d=4150,
        rating=4.7,  # below 4.9 — filtered by min_rating
        image_url="https://ae01.alicdn.com/kf/mock005.jpg",
        product_url="https://www.aliexpress.com/item/mock005.html",
        category_id="",
    ),
]


def get_mock_products(
    category_id: str, min_rating: float = 4.9, max_results: int = 100
) -> list[AliProduct]:
    products = [p.model_copy(update={"category_id": category_id}) for p in _MOCK_DATA]
    filtered = [p for p in products if p.rating >= min_rating]
    return filtered[:max_results]
