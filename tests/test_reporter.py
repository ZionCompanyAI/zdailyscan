import pytest
from pathlib import Path
from datetime import date
from unittest.mock import AsyncMock, patch, MagicMock

from app.models import ProductScore


SAMPLE_PRODUCTS = [
    ProductScore(
        name="Fone Bluetooth TWS",
        score=0.82,
        import_cost_brl=45.00,
        suggested_price_brl=112.50,
        ml_listing_count=234,
        aliexpress_url="https://aliexpress.com/item/1234567890.html",
    ),
    ProductScore(
        name="Relógio Smartwatch",
        score=0.75,
        import_cost_brl=78.30,
        suggested_price_brl=195.00,
        ml_listing_count=180,
        aliexpress_url="https://aliexpress.com/item/9876543210.html",
    ),
]


@pytest.mark.asyncio
async def test_report_format_contains_required_fields():
    """Mensagem enviada ao MC contém nome, score, custo, sugestão de venda e link."""
    from app.reporters.telegram_reporter import send_daily_report, _format_message

    msg = _format_message(SAMPLE_PRODUCTS)

    assert "Fone Bluetooth TWS" in msg
    assert "0.82" in msg
    assert "45,00" in msg or "45.00" in msg
    assert "112,50" in msg or "112.50" in msg
    assert "aliexpress.com/item/1234567890" in msg


MC_URL = "https://orchestrator.example.com"
MC_API_KEY = "test-api-key"


@pytest.mark.asyncio
async def test_mc_failure_does_not_raise():
    """Falha do MC (timeout) não levanta exceção — retorna False."""
    from app.reporters.telegram_reporter import send_daily_report

    with patch("app.reporters.telegram_reporter.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(side_effect=Exception("Connection timeout"))
        mock_cls.return_value = mock_client

        result = await send_daily_report(SAMPLE_PRODUCTS, mc_url=MC_URL, mc_api_key=MC_API_KEY)

    assert result is False


@pytest.mark.asyncio
async def test_mc_5xx_returns_false():
    """Resposta 5xx do MC retorna False sem levantar exceção."""
    from app.reporters.telegram_reporter import send_daily_report

    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.raise_for_status = MagicMock(side_effect=Exception("503 Service Unavailable"))

    with patch("app.reporters.telegram_reporter.httpx.AsyncClient") as mock_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_cls.return_value = mock_client

        result = await send_daily_report(SAMPLE_PRODUCTS, mc_url=MC_URL, mc_api_key=MC_API_KEY)

    assert result is False


def test_file_report_saved(tmp_path):
    """Relatório é salvo em data/reports/YYYY-MM-DD.md."""
    from app.reporters.file_reporter import save_daily_report

    report_date = date(2026, 5, 27)
    saved_path = save_daily_report(SAMPLE_PRODUCTS, report_date=report_date, base_dir=tmp_path)

    expected = tmp_path / "2026-05-27.md"
    assert saved_path == expected
    assert saved_path.exists()

    content = saved_path.read_text()
    assert "Fone Bluetooth TWS" in content
    assert "Relógio Smartwatch" in content
