import os
from typing import Literal
from pydantic import BaseModel


class ImportCost(BaseModel):
    price_usd: float
    freight_usd: float
    tax_brl: float
    total_cost_brl: float
    regime: Literal["remessa_conforme", "normal"]


def calculate_import_cost(price_usd: float, freight_usd: float) -> ImportCost:
    rate = float(os.environ.get("USD_BRL_RATE", "5.70"))

    total_usd = price_usd + freight_usd
    base_brl = total_usd * rate

    if total_usd <= 50.0:
        regime: Literal["remessa_conforme", "normal"] = "remessa_conforme"
        ii = 0.20 * base_brl
        icms = 0.17 * base_brl
    else:
        regime = "normal"
        ii = 0.60 * base_brl
        # ICMS por dentro: aliquota incide sobre base que já inclui o próprio imposto
        icms = (base_brl + ii) * 0.17 / (1 - 0.17)

    tax_brl = ii + icms

    return ImportCost(
        price_usd=price_usd,
        freight_usd=freight_usd,
        tax_brl=round(tax_brl, 2),
        total_cost_brl=round(base_brl + tax_brl, 2),
        regime=regime,
    )
