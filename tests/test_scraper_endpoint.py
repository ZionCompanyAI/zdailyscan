import os
from unittest.mock import patch

from fastapi.testclient import TestClient


def test_scraper_aliexpress_endpoint_exists():
    """GET /scrapers/aliexpress deve retornar 200 com SCRAPER_MODE=mock."""
    from app.main import app

    client = TestClient(app)
    with patch.dict(os.environ, {"SCRAPER_MODE": "mock"}):
        response = client.get("/scrapers/aliexpress")
    assert response.status_code == 200


def test_scraper_aliexpress_response_shape():
    """Resposta deve ter chaves 'products' (list) e 'count' (int)."""
    from app.main import app

    client = TestClient(app)
    with patch.dict(os.environ, {"SCRAPER_MODE": "mock"}):
        response = client.get("/scrapers/aliexpress")
    data = response.json()
    assert "products" in data
    assert "count" in data
    assert isinstance(data["products"], list)
    assert isinstance(data["count"], int)
    assert data["count"] == len(data["products"])


def test_scraper_aliexpress_query_params():
    """Parâmetros category e limit são aceitos sem erro."""
    from app.main import app

    client = TestClient(app)
    with patch.dict(os.environ, {"SCRAPER_MODE": "mock"}):
        response = client.get("/scrapers/aliexpress?category=100003070&limit=5")
    assert response.status_code == 200


def test_pipeline_uses_scrapers_import():
    """pipeline.get_hot_products deve vir de app.scrapers, não de app.aliexpress."""
    import app.pipeline as pipeline_module

    fn = pipeline_module.get_hot_products
    assert "scrapers" in fn.__module__, (
        f"Expected get_hot_products from app.scrapers, got module: {fn.__module__}"
    )


def test_scrapers_package_exports_get_hot_products():
    """app.scrapers deve exportar get_hot_products diretamente."""
    from app.scrapers import get_hot_products  # noqa: F401 — importação é o teste

    assert callable(get_hot_products)
