from Greenhub.product_price_benchmarks import load_product_price_benchmarks, screening_tea_product_prices


def test_product_price_benchmarks_are_traceable_and_bounded():
    rows = load_product_price_benchmarks()
    assert len(rows) == 10
    assert {row.product for row in rows} >= {"Protein product", "Biomethane", "Press cake"}
    assert all(row.low <= row.screening_base <= row.high for row in rows)
    assert all(row.source_url for row in rows)
    assert all(row.evidence_class == "industrial_benchmark_screening_assumption" for row in rows)


def test_unlike_price_units_remain_explicit():
    rows = {row.product: row for row in load_product_price_benchmarks()}
    assert rows["Biomethane"].unit == "EUR/MWh"
    assert rows["Protein product"].unit == "EUR/t dry product"


def test_screening_tea_mapping_uses_direct_biomethane_basis_only():
    prices = screening_tea_product_prices()
    assert prices["dry_protein_product"]["value_eur_per_unit"] == 1.6
    assert prices["biomethane"]["value_eur_per_unit"] == 0.88
    assert prices["biomethane"]["reference_year"] == 2026
    assert prices["biomethane"]["reference_period"] == "2026"
