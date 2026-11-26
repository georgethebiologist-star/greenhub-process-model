from types import SimpleNamespace

import pytest

from Greenhub.application.material_fate import accumulate_material_fate, finalize_material_fate


def stream(name, aliases, components, *, terminal=True):
    return SimpleNamespace(
        stream_id=name,
        aliases=aliases,
        sink_unit=None if terminal else "NEXT_UNIT",
        components={key: SimpleNamespace(value=value) for key, value in components.items()},
    )


def test_annual_fate_uses_terminal_water_and_product_components_per_timestep():
    totals = {}
    first = [
        stream("raw_liquid_fraction", ["raw_liquid_fraction"], {"Water": 100, "Ammonium": 10}, terminal=False),
        stream("ammonium_product_stream", ["ammonium_product"], {"Water": 2, "Ammonium": 3}),
        stream("residual_liquor_stream", ["residual_liquor"], {"Water": 75, "Ammonium": 5}),
        stream("intermediate_wastewater", ["phase6_wastewater"], {"Water": 99}, terminal=False),
    ]
    second = [
        stream("raw_liquid_fraction", ["raw_liquid_fraction"], {"Water": 50, "Ammonium": 5}, terminal=False),
        stream("ammonium_product_stream", ["ammonium_product"], {"Water": 1, "Ammonium": 1}),
        stream("residual_liquor_stream", ["residual_liquor"], {"Water": 35, "Ammonium": 2}),
    ]
    accumulate_material_fate(totals, first, 2)
    accumulate_material_fate(totals, second, 3)
    report = finalize_material_fate(totals, "test")

    assert report["grass_juice"]["components_kg"]["Ammonium"] == 35
    assert report["products"][0]["components_kg"]["Ammonium"] == 9
    assert report["residual_water"]["components_kg"]["Ammonium"] == 16
    assert report["residual_water"]["components_kg"]["Water"] == 255
    assert report["residual_water"]["elements_kg"]["nitrogen"] > 0
    assert report["residual_water"]["mass_kg"] == pytest.approx(271)
    assert len(report["residual_water"]["streams"]) == 1
