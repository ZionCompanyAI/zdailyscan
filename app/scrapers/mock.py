from app.scrapers.aliexpress import AliProduct


def get_mock_products(category_id: str) -> list[AliProduct]:
    """5 fixed products — ratings [5.0, 4.9, 4.8, 4.7, 5.0]. With min_rating=4.9, 3 pass."""
    base_url = "https://www.aliexpress.com/item"
    return [
        AliProduct(
            product_id="1001",
            title="Wireless Earbuds Pro X",
            price_usd=12.99,
            sale_count_30d=4200,
            rating=5.0,
            image_url="https://ae01.alicdn.com/mock/1001.jpg",
            product_url=f"{base_url}/1001.html",
            category_id=category_id,
        ),
        AliProduct(
            product_id="1002",
            title="Smart LED Strip 5m",
            price_usd=8.49,
            sale_count_30d=3100,
            rating=4.9,
            image_url="https://ae01.alicdn.com/mock/1002.jpg",
            product_url=f"{base_url}/1002.html",
            category_id=category_id,
        ),
        AliProduct(
            product_id="1003",
            title="Portable Charger 10000mAh",
            price_usd=15.00,
            sale_count_30d=2800,
            rating=4.8,  # below 4.9 — filtered out
            image_url="https://ae01.alicdn.com/mock/1003.jpg",
            product_url=f"{base_url}/1003.html",
            category_id=category_id,
        ),
        AliProduct(
            product_id="1004",
            title="Silicone Kitchen Utensil Set",
            price_usd=6.99,
            sale_count_30d=1900,
            rating=4.7,  # below 4.9 — filtered out
            image_url="https://ae01.alicdn.com/mock/1004.jpg",
            product_url=f"{base_url}/1004.html",
            category_id=category_id,
        ),
        AliProduct(
            product_id="1005",
            title="Resistance Bands Set 11pcs",
            price_usd=9.90,
            sale_count_30d=5600,
            rating=5.0,
            image_url="https://ae01.alicdn.com/mock/1005.jpg",
            product_url=f"{base_url}/1005.html",
            category_id=category_id,
        ),
    ]
