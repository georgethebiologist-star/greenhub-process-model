import csv
import json
from pathlib import Path


DATA = (
    Path(__file__).parents[1]
    / "Greenhub"
    / "data"
    / "Bigas production + upgrade"
    / "AD kinetics"
)
CSV_PATH = DATA / "grass_silage_adm1_biernacki_2013_reference.csv"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def test_grass_silage_adm1_fitted_rates_are_traceable_and_not_activated():
    rows = read_csv(CSV_PATH)
    source = json.loads(CSV_PATH.with_name(CSV_PATH.stem + ".source.json").read_text(encoding="utf-8"))
    register = read_csv(DATA / "source_register.csv")

    expected = {
        "k_dis": 1.7433,
        "k_hyd_ch": 0.7366,
        "k_hyd_pr": 0.0104,
        "k_hyd_li": 0.0149,
    }
    assert len(rows) == 4
    assert len({row["observation_id"] for row in rows}) == 4
    assert {row["activation_state"] for row in rows} == {"reference_only"}
    assert {row["source_id"] for row in rows} == {"SRC007"}
    assert source["article_doi"] == "10.1016/j.biortech.2012.09.128"
    assert source["numeric_table_source"]["table"] == "Table 17"
    assert source["numeric_table_source"]["page"] == 102
    assert source["methods"]["batch_temperature_c"] == 38
    assert source["methods"]["batch_duration_days"] == 15
    assert any(row["source_id"] == "SRC007" for row in register)

    for row in rows:
        assert float(row["reported_value"]) == expected[row["source_symbol"]]
        assert row["reported_unit"] == "d^-1"
        assert abs(float(row["normalized_value"]) - float(row["reported_value"]) / 86400) < 1e-15
        assert row["normalized_unit"] == "s^-1"
        assert row["uncertainty"] == ""
        assert "not a GreenHub" in row["transferability_limitations"]


def test_biernacki_article_doi_is_corrected_in_local_source_register():
    register = read_csv(DATA / "source_register.csv")
    article = next(row for row in register if row["source_id"] == "SRC005")
    assert article["doi_or_stable_id"] == "10.1016/j.biortech.2012.09.128"
    assert article["url"] == "https://doi.org/10.1016/j.biortech.2012.09.128"
