import hashlib
import os
import time

import httpx
from pydantic import BaseModel

_ALIEXPRESS_API_URL = "https://api-sg.aliexpress.com/sync"


class AliExpressProduct(BaseModel):
    product_id: str
    title: str
    price_usd: float
    freight_usd: float = 5.0


def _sign(params: dict, secret: str) -> str:
    pairs = sorted(params.items())
    query = secret + "".join(f"{k}{v}" for k, v in pairs) + secret
    return hashlib.md5(query.encode("utf-8")).hexdigest().upper()


async def get_hot_products(category_id: str, limit: int = 20) -> list[AliExpressProduct]:
    app_key = os.environ.get("ALIEXPRESS_APP_KEY", "")
    app_secret = os.environ.get("ALIEXPRESS_APP_SECRET", "")
    if not app_key or not app_secret:
        return []

    params: dict[str, str] = {
        "app_key": app_key,
        "category_ids": category_id,
        "fields": "product_id,product_title,target_sale_price",
        "format": "json",
        "method": "aliexpress.affiliate.hotproduct.query",
        "page_size": str(limit),
        "sign_method": "md5",
        "timestamp": str(int(time.time() * 1000)),
        "v": "2.0",
    }
    params["sign"] = _sign(params, app_secret)

    async with httpx.AsyncClient() as client:
        response = await client.post(_ALIEXPRESS_API_URL, data=params)
        response.raise_for_status()
        data = response.json()

    raw = (
        data.get("aliexpress_affiliate_hotproduct_query_response", {})
        .get("resp_result", {})
        .get("result", {})
        .get("products", {})
        .get("product", [])
    )

    out: list[AliExpressProduct] = []
    for p in raw:
        price_str = str(p.get("target_sale_price", "0")).replace("$", "").replace(",", "")
        try:
            price_usd = float(price_str)
        except ValueError:
            price_usd = 0.0
        out.append(
            AliExpressProduct(
                product_id=str(p.get("product_id", "")),
                title=str(p.get("product_title", "")),
                price_usd=price_usd,
            )
        )
    return out
