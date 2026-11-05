from Greenhub.product_price_benchmarks import load_product_price_benchmarks, screening_tea_product_prices


def test_product_price_benchmarks_are_traceable_and_bounded():
    rows = load_product_price_benchmarks()
    assert len(rows) == 11
    assert {row.product for row in rows} >= {"Protein product", "Biomethane", "Press cake"}
    assert all(row.low <= row.screening_base <= row.high for row in rows)
    assert all(
        row.source_url or row.market_status.lower().startswith("user-supplied")
        for row in rows
    )
    assert all(row.evidence_class == "industrial_benchmark_screening_assumption" for row in rows)
    biomethane = next(row for row in rows if row.product == "Biomethane")
    assert biomethane.quality_class == biomethane.source_quality_class == "B"
    assert biomethane.source_id == "ACER-DATAITEM-1226"
    assert biomethane.source_location == "Slide 27; metric ‘TTF + GO price - Waste’, Average / Min / Max"
    assert next(row for row in rows if row.product == "Protein product").quality_class == "C"


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
    assert prices["biomethane"]["quality_class"] == "E"
    assert prices["biomethane"]["source_title"] == "User-provided TTF/GO benchmark table"
    assert prices["biomethane"]["source_url"] == "https://www.energievergelijk.nl/energieprijzen/gasprijs"
    assert prices["dry_protein_product"]["quality_class"] == "C"
    assert prices["dry_protein_product"]["source_quality_class"] == "B"
    from Greenhub.tea_finance import normalize_product_prices
    normalized = {row.product_id: row for row in normalize_product_prices(prices)}
    assert normalized["biomethane"].quality_class == "E"
    assert normalized["biomethane"].stable_identifier == "USER-GAS-GO-SCREEN-2026"
    assert normalized["dry_protein_product"].quality_class == "C"

    from Greenhub.product_price_benchmarks import product_price_source_references, screening_tea_product_price_ranges
    reference = product_price_source_references()
    assert reference["quality_class"] == "B"
    assert reference["value"] == 60.51
    assert reference["unit"] == "EUR/MWh"
    assert screening_tea_product_price_ranges()["biomethane"]["quality_class"] == "E"
