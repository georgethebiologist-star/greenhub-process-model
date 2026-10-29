"""Traceable industrial product-price benchmarks for screening TEA."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
import re

from Greenhub.settings import DATA_DIR


DEFAULT_PRICE_BENCHMARK_PATH = DATA_DIR / "tea" / "netherlands_industrial_product_price_benchmarks.csv"


@dataclass(frozen=True)
class ProductPriceBenchmark:
    product: str
    low: float
    high: float
    screening_base: float
    unit: str
    basis: str
    market_status: str
    price_date: str
    geography: str
    source_type: str
    source_url: str
    traceability: str
    limitations: str

    @property
    def evidence_class(self) -> str:
        return "industrial_benchmark_screening_assumption"

    @property
    def reference_year(self) -> int | None:
        """Return the first calendar year while retaining the full period label."""

        match = re.search(r"\b(19|20)\d{2}\b", self.price_date)
        return int(match.group(0)) if match else None


def load_product_price_benchmarks(
    path: Path = DEFAULT_PRICE_BENCHMARK_PATH,
) -> tuple[ProductPriceBenchmark, ...]:
    """Load normalized benchmarks without converting unlike price bases."""

    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {
        "product", "industrial_price_low", "industrial_price_high",
        "screening_base", "unit", "price_basis_or_grade", "source_url",
    }
    missing = required - set(rows[0] if rows else ())
    if missing:
        raise ValueError(f"Price benchmark file is missing columns: {sorted(missing)}")
    result = []
    for row in rows:
        low = float(row["industrial_price_low"])
        high = float(row["industrial_price_high"])
        base = float(row["screening_base"])
        if not low <= base <= high:
            raise ValueError(f"Screening price is outside range for {row['product']}")
        result.append(ProductPriceBenchmark(
            product=row["product"].strip(), low=low, high=high, screening_base=base,
            unit=row["unit"].strip(), basis=row["price_basis_or_grade"].strip(),
            market_status=row.get("market_status", "").strip(),
            price_date=row.get("price_date", "").strip(), geography=row.get("geography", "").strip(),
            source_type=row.get("source_type", "").strip(), source_url=row.get("source_url", "").strip(),
            traceability=(row.get("traceability_and_applicability") or "").strip(),
            limitations=(row.get("uncertainty_or_limitations") or "").strip(),
        ))
    return tuple(result)


_TEA_PRODUCT_IDS = {
    "Protein product": ("dry_protein_product", "EUR/kg"),
    "Press cake": ("press_cake", "EUR/kg"),
    "Ammonium product": ("ammonium_product", "EUR/kg"),
    "Phosphorus/struvite product": ("phosphorus_product", "EUR/kg"),
    "Potassium concentrate": ("potassium_concentrate", "EUR/kg"),
    "Recovered water": ("recovered_water", "EUR/m3"),
    "Nutrient-rich solids": ("nutrient_rich_solids", "EUR/kg"),
    "Ion-exchange product": ("ion_exchange_product", "EUR/kg"),
    "Biomethane (user all-in direct basis)": ("biomethane", "EUR/m3"),
}


def screening_tea_product_prices(
    path: Path = DEFAULT_PRICE_BENCHMARK_PATH,
) -> dict[str, dict[str, object]]:
    """Return explicitly labelled TEA price mappings where units are defensible.

    The sales-basis profile applies user-confirmed 20 C atmospheric gas pricing
    and dry chemical-equivalent fertilizer quantities after legacy benchmarks.
    USD fertilizer quotes use an explicitly assumed FX rate; wet carrier mass
    and unspeciated phosphorus never become saleable salt automatically.
    """

    output: dict[str, dict[str, object]] = {}
    for benchmark in load_product_price_benchmarks(path):
        mapping = _TEA_PRODUCT_IDS.get(benchmark.product)
        if mapping is None:
            continue
        product_id, unit = mapping
        divisor = 1000.0 if benchmark.unit.startswith("EUR/t") else 1.0
        output[product_id] = {
            "value_eur_per_unit": benchmark.screening_base / divisor,
            "unit": unit,
            "source_status": "industrial_benchmark_screening_assumption",
            "source_title": benchmark.source_type,
            "source_url": benchmark.source_url,
            "notes": benchmark.traceability,
            "basis": benchmark.basis,
            "geography": benchmark.geography,
            "reference_year": benchmark.reference_year,
            "reference_period": benchmark.price_date,
            "evidence_class": benchmark.evidence_class,
            "applicability": benchmark.market_status,
            "conversion_method": f"{benchmark.unit} to {unit}; divide by 1000 for EUR/t to EUR/kg" if divisor != 1.0 else "none",
            "uncertainty": f"{benchmark.low:g}-{benchmark.high:g} {benchmark.unit}",
            "quality_basis": "screening_assumption",
        }
    sales = json.loads((DATA_DIR / 'tea' / 'product_sales_basis.json').read_text())
    gas = output.get('biomethane')
    if gas is not None:
        gas.update(value_eur_per_unit=sales['gas']['price_eur_m3'],
                   gas_reference_temperature_k=sales['gas']['temperature_k'],
                   gas_reference_pressure_pa=sales['gas']['pressure_pa'],
                   basis='dry gas at 20 C and 101325 Pa',
                   notes=sales['gas']['warning'], conversion_method='component kmol × R × 293.15 K / 101325 Pa')
    for key, product, label in (('ammonium_sulfate', 'ammonium_product', 'Ammonium sulfate (dry equivalent)'), ('struvite', 'phosphorus_product', 'Solid struvite')):
        data = sales[key]
        output[product] = {
            'value_eur_per_unit': data['base_usd_t'] * sales['fx']['eur_per_usd'] / 1000,
            'unit': 'EUR/kg', 'quantity_component': data['quantity_component'], 'display_name': label,
            'source_status': 'user_provided_screening_assumption', 'source_title': data['status'],
            'source_url': data.get('sources', [''])[0], 'reference_year': 2026,
            'basis': 'dry pure-compound equivalent; no carrier water sold', 'quality_basis': 'screening_assumption',
            'notes': data['warning'] + ' FX: 0.92 EUR/USD is an explicit assumption, not a market quote.',
            'conversion_method': 'USD/t × 0.92 EUR/USD / 1000 kg/t',
            'uncertainty': f"{data['low_usd_t']}-{data['high_usd_t']} USD/t; FX unverified",
        }
    return output
