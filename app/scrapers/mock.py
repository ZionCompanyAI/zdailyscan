from app.scrapers import AliProduct


async def get_hot_products(
    category_id: str,
    min_rating: float = 4.9,
    max_results: int = 100,
) -> list[AliProduct]:
    return [
        AliProduct(
            product_id="mock-001",
            title="Mock Beauty Serum A",
            price_usd=12.99,
            sale_count_30d=1500,
            rating=5.0,
            image_url="https://ae01.alicdn.com/mock/001.jpg",
            product_url="https://www.aliexpress.com/item/mock001.html",
            category_id=category_id,
        ),
        AliProduct(
            product_id="mock-002",
            title="Mock Facial Mask B",
            price_usd=8.50,
            sale_count_30d=800,
            rating=4.9,
            image_url="https://ae01.alicdn.com/mock/002.jpg",
            product_url="https://www.aliexpress.com/item/mock002.html",
            category_id=category_id,
        ),
        AliProduct(
            product_id="mock-003",
            title="Mock Lip Gloss C",
            price_usd=25.00,
            sale_count_30d=2000,
            rating=4.95,
            image_url="https://ae01.alicdn.com/mock/003.jpg",
            product_url="https://www.aliexpress.com/item/mock003.html",
            category_id=category_id,
        ),
        AliProduct(
            product_id="mock-004",
            title="Mock Low Rating Cream D",
            price_usd=5.00,
            sale_count_30d=100,
            rating=4.5,
            image_url="https://ae01.alicdn.com/mock/004.jpg",
            product_url="https://www.aliexpress.com/item/mock004.html",
            category_id=category_id,
        ),
        AliProduct(
            product_id="mock-005",
            title="Mock Low Rating Toner E",
            price_usd=3.20,
            sale_count_30d=50,
            rating=4.2,
            image_url="https://ae01.alicdn.com/mock/005.jpg",
            product_url="https://www.aliexpress.com/item/mock005.html",
            category_id=category_id,
        ),
    ]
