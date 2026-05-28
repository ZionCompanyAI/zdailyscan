from unittest.mock import AsyncMock, patch


from app.scoring.scorer import ProductScore
from app.reporters.telegram_reporter import _format_message, send_daily_report
from app.reporters.file_reporter import save_daily_report


def _make_product(i: int) -> ProductScore:
    return ProductScore(
        product_id=f"p{i}",
        title=f"Product {i}",
        score_total=round(0.80 - i * 0.01, 6),
        score_margem=0.5,
        score_demanda_br=0.8,
        score_oportunidade=0.6,
        score_tendencia=0.5,
        score_logistica=1.0,
        margin_brl=60.0,
        sell_price_suggestion_brl=112.50,
        viavel=True,
        demand_count=234,
        import_cost_brl=45.0,
    )


def test_report_format_contains_required_fields():
    products = [_make_product(i) for i in range(15)]
    msg = _format_message(products)

    # top 10 incluídos, 11º em diante excluídos
    assert "Product 0" in msg
    assert "Product 9" in msg
    assert "Product 10" not in msg

    # campos obrigatórios
    assert "score:" in msg
    assert "Custo importação" in msg
    assert "Sugestão de venda" in msg
    assert "Demanda ML" in msg
    assert "aliexpress.com/item/p0.html" in msg


async def test_mc_failure_does_not_raise(monkeypatch):
    monkeypatch.setenv("ALIEXPRESS_APP_KEY", "x")
    monkeypatch.setenv("ALIEXPRESS_APP_SECRET", "x")
    monkeypatch.setenv("ALIEXPRESS_TRACKING_ID", "x")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "x")
    monkeypatch.setenv("MC_API_KEY", "x")
    monkeypatch.setenv("MC_URL", "http://localhost:9999")

    products = [_make_product(0)]

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(side_effect=Exception("connection refused"))

    with patch("app.reporters.telegram_reporter.httpx.AsyncClient", return_value=mock_client):
        result = await send_daily_report(products)

    assert result is False


def test_file_report_saved(tmp_path):
    products = [_make_product(i) for i in range(3)]
    path = save_daily_report(products, reports_dir=tmp_path)

    assert path.exists()
    content = path.read_text()
    assert "Product 0" in content
    assert "aliexpress.com/item/p0.html" in content
