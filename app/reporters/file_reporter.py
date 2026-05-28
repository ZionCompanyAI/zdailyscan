from datetime import date
from pathlib import Path

from app.scoring.scorer import ProductScore

REPORTS_DIR = Path("data/reports")


def save_daily_report(results: list[ProductScore], reports_dir: Path = REPORTS_DIR) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    path = reports_dir / f"{today}.md"
    top10 = results[:10]
    lines = [
        f"# ZDailyScan — {today}",
        "",
        "Top 10 oportunidades AliExpress → LojaHi Select",
        "",
    ]
    for i, p in enumerate(top10, 1):
        product_url = f"https://www.aliexpress.com/item/{p.product_id}.html"
        lines += [
            f"## {i}. {p.title}",
            "",
            f"- **Score**: {p.score_total:.4f}",
            f"- **Custo importação**: R$ {p.import_cost_brl:.2f}",
            f"- **Sugestão de venda**: R$ {p.sell_price_suggestion_brl:.2f}",
            f"- **Demanda ML**: {p.demand_count} anúncios",
            f"- **Link**: {product_url}",
            "",
        ]
    path.write_text("\n".join(lines))
    return path
