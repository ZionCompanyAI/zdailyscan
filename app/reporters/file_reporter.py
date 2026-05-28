from datetime import date
from pathlib import Path

from app.models import ProductScore

DEFAULT_BASE_DIR = Path("data/reports")


def save_daily_report(
    results: list[ProductScore],
    report_date: date | None = None,
    base_dir: Path | None = None,
) -> Path:
    today = report_date or date.today()
    output_dir = base_dir if base_dir is not None else DEFAULT_BASE_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"{today.strftime('%Y-%m-%d')}.md"

    lines = [
        f"# ZDailyScan — {today.strftime('%Y-%m-%d')}",
        "",
        "## Top oportunidades AliExpress → LojaHi Select",
        "",
    ]
    for i, p in enumerate(results, start=1):
        lines += [
            f"### {i}. {p.name}",
            f"- **Score:** {p.score:.2f}",
            f"- **Custo importação:** R$ {p.import_cost_brl:.2f}",
            f"- **Sugestão de venda:** R$ {p.suggested_price_brl:.2f}",
            f"- **Demanda ML:** {p.ml_listing_count} anúncios",
            f"- **Link:** {p.aliexpress_url}",
            "",
        ]

    file_path.write_text("\n".join(lines), encoding="utf-8")
    return file_path
