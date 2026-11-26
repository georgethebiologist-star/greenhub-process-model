"""Transcribe source-reported grass silage composition/proteolysis tables.

The experimental grasses are cultivated UK ryegrass and Festulolium. This is
reference evidence only; it is not a GreenHub roadside-grass calibration.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "storage"
AUDIT = DATA / "global_audit_package"
FILENAME = "cultivated_ryegrass_festulolium_ensiling_proteolysis_muhandiram_2023_reference.csv"
CSV_PATH = FOLDER / FILENAME
SIDECAR_PATH = CSV_PATH.with_suffix(".source.json")
SOURCE_ID = "SRC-MUHANDIRAM-GRASS-ENSILING-2023-REFERENCE"
DOI = "10.1002/fes3.475"
URL = "https://pmc.ncbi.nlm.nih.gov/articles/PMC10909542/"
DOI_URL = f"https://doi.org/{DOI}"
RETRIEVED = "2026-11-08"
TIMEPOINTS = (("0 h", 0), ("9 h", 9), ("1 d", 24), ("2 d", 48), ("3 d", 72), ("14 d", 336), ("90 d", 2160))
GRASSES = {
    "Ryegrass": "perennial ryegrass (Lolium perenne cv AberMagic)",
    "Lp × Fg": "Festulolium (Lolium perenne × Festuca arundinacea var. glaucescens cv Lp × Fg)",
}
FIELDS = [
    "record_id", "source_id", "phase_relevance", "source_table", "source_row_type",
    "harvest_cut", "cultivar", "material_stage", "ensiling_time_label",
    "elapsed_hours_from_ensiling", "metric", "value", "unit", "basis",
    "reported_mean_over_time", "sem_grass_effect", "p_grass_effect",
    "sem_time_effect", "p_time_effect", "sem_grass_by_time_interaction",
    "p_grass_by_time_interaction", "source_significance_group", "source_annotation",
    "replicates_or_sample_design", "source_location", "method_summary",
    "evidence_class", "quality_class", "activation_state", "transferability", "limitations",
]

SOURCE = {
    "source_id": SOURCE_ID,
    "source_title": "Designing agricultural grasses to help mitigate proteolysis during ensiling to optimize protein feed provisions for livestock",
    "authors": "Nuwan P. K. Muhandiram; Michael W. Humphreys; Rhun Fychan; John W. Davies; Ruth Sanderson; Christina L. Marley",
    "year": "2023",
    "source_type": "peer-reviewed primary experimental article; open-access measured data transcription",
    "doi_or_stable_identifier": DOI,
    "stable_url": URL,
    "material": "Cultivated UK perennial ryegrass cv AberMagic and Festulolium cv Lp × Fg, wilted and laboratory ensiled",
    "quality_notes": (
        "Tables 1–3 transcribed as printed, including mean, SEM, p-values and significance annotations. "
        "The paper reports cultivated forage and controlled 21 C laboratory silos, not Dutch roadside/VARTA feed. "
        "Time-series values are concentrations or pH, not retained mass, effluent, emissions, or a closed component balance."
    ),
    "accessed_date": RETRIEVED,
}

# Each table series stores cultivar values, the article's marginal time means,
# means across time, significance annotations, and its reported factorial SEMs/p.
TABLES = {
    "Table 2": {
        "cut": "Cut 2 (May 2016)",
        "metric_data": {
            "FD-DM": {
                "unit": "g/kg", "basis": "as printed; forage dry-matter concentration",
                "cultivar": {"Ryegrass": ["346.1", "355.4", "357.8", "360.0", "353.1", "346.8", "347.3"], "Lp × Fg": ["327.6", "332.2", "333.4", "331.7", "331.3", "326.6", "327.3"]},
                "means": ["336.8", "343.3", "345.6", "345.8", "342.2", "336.7", "337.3"],
                "cultivar_mean": {"Ryegrass": "352.3", "Lp × Fg": "330.0"},
                "groups": {"Ryegrass": ["", "", "", "", "", "", ""], "Lp × Fg": ["", "", "", "", "", "", ""], "Mean": ["b", "ab", "a", "ab", "ab", "b", "ab"]},
                "annotations": {}, "sem": ("1.14", "2.14", "3.03"), "p": ("<0.001", "0.007", "0.732"),
            },
            "pH": {
                "unit": "pH", "basis": "aqueous silage extract; source method citation",
                "cultivar": {"Ryegrass": ["6.00", "6.03", "4.88", "4.01", "3.80", "3.54", "3.58"], "Lp × Fg": ["6.04", "5.82", "4.61", "4.04", "3.82", "3.57", "3.62"]},
                "means": ["6.02", "5.93", "4.74", "4.02", "3.81", "3.56", "3.60"],
                "cultivar_mean": {"Ryegrass": "4.55", "Lp × Fg": "4.50"},
                "groups": {"Ryegrass": ["a", "a", "b", "c", "d", "e", "e"], "Lp × Fg": ["a", "b", "c", "d", "e", "f", "f"], "Mean": ["", "", "", "", "", "", ""]},
                "annotations": {}, "sem": ("0.005", "0.009", "0.013"), "p": ("<0.001", "<0.001", "<0.001"),
            },
            "WSC": {
                "unit": "g/kg FD DM", "basis": "freeze-dried dry-matter basis, as printed",
                "cultivar": {"Ryegrass": ["144.8", "124.7", "104.1", "81.0", "76.4", "49.6", "37.7"], "Lp × Fg": ["130.9", "128.1", "96.8", "71.6", "66.9", "32.9", "33.1"]},
                "means": ["137.8", "127.0", "100.2", "76.8", "72.2", "41.4", "36.5"],
                "cultivar_mean": {"Ryegrass": "88.8", "Lp × Fg": "80.3"},
                "groups": {"Ryegrass": ["a", "b", "c", "d", "d", "e", "f"], "Lp × Fg": ["a", "b", "c", "d", "e", "f", "f"], "Mean": ["", "", "", "", "", "", ""]},
                "annotations": {}, "sem": ("1.22", "2.29", "3.24"), "p": ("<0.001", "<0.001", "0.027"),
            },
            "TN": {
                "unit": "g/kg FD DM", "basis": "freeze-dried dry-matter basis, as printed",
                "cultivar": {"Ryegrass": ["26.3", "28.2", "27.8", "27.2", "26.5", "27.8", "28.3"], "Lp × Fg": ["26.5", "28.0", "27.6", "27.8", "27.6", "28.1", "28.8"]},
                "means": ["26.4", "28.1", "27.7", "27.5", "27.1", "28.0", "28.6"],
                "cultivar_mean": {"Ryegrass": "27.4", "Lp × Fg": "27.8"},
                "groups": {"Ryegrass": ["", "", "", "", "", "", ""], "Lp × Fg": ["", "", "", "", "", "", ""], "Mean": ["d", "ab", "abc", "bc", "cd", "ab", "a"]},
                "annotations": {}, "sem": ("0.14", "0.25", "0.36"), "p": ("0.092", "<0.001", "0.540"),
            },
            "Soluble N": {
                "unit": "g/kg TN", "basis": "total-nitrogen basis, as printed",
                "cultivar": {"Ryegrass": ["532", "512", "569", "603", "637", "590", "640"], "Lp × Fg": ["453", "474", "497", "576", "603", "611", "605"]},
                "means": ["493", "493", "533", "589", "620", "600", "623"],
                "cultivar_mean": {"Ryegrass": "583", "Lp × Fg": "545"},
                "groups": {"Ryegrass": ["a", "a", "ab", "ab", "abc", "bc", "bc"], "Lp × Fg": ["a", "a", "a", "a", "b", "c", "c"], "Mean": ["", "", "", "", "", "", ""]},
                "annotations": {"Ryegrass": {0: "A" , 2: "A"}, "Lp × Fg": {0: "B", 2: "B"}}, "sem": ("5.2", "9.8", "13.8"), "p": ("<0.001", "<0.001", "0.028"),
            },
            "Ammonia-N": {
                "unit": "g/kg TN", "basis": "total-nitrogen basis, as printed",
                "cultivar": {"Ryegrass": ["33.8", "46.8", "59.3", "60.9", "44.8", "48.7", "77.2"], "Lp × Fg": ["32.9", "41.2", "53.3", "55.4", "46.2", "53.1", "84.3"]},
                "means": ["33.4", "44.2", "56.1", "57.9", "45.4", "51.0", "83.4"],
                "cultivar_mean": {"Ryegrass": "53.3", "Lp × Fg": "52.8"},
                "groups": {"Ryegrass": ["", "", "", "", "", "", ""], "Lp × Fg": ["", "", "", "", "", "", ""], "Mean": ["a", "bc", "b", "b", "bc", "b", "a"]},
                "annotations": {}, "sem": ("1.87", "3.5", "4.95"), "p": ("0.869", "<0.001", "0.726"),
            },
        },
    },
    "Table 3": {
        "cut": "Cut 4 (August 2016)",
        "metric_data": {
            "FD-DM": {
                "unit": "g/kg", "basis": "as printed; forage dry-matter concentration",
                "cultivar": {"Ryegrass": ["438.4", "442.1", "440.8", "443.7", "448.2", "448.9", "429.4"], "Lp × Fg": ["319.3", "327.0", "330.5", "315.8", "329.5", "327.9", "314.2"]},
                "means": ["378.8", "384.5", "385.6", "379.8", "388.8", "388.4", "371.8"],
                "cultivar_mean": {"Ryegrass": "441.6", "Lp × Fg": "323.5"},
                "groups": {"Ryegrass": ["", "", "", "", "", "", ""], "Lp × Fg": ["", "", "", "", "", "", ""], "Mean": ["ab", "ab", "ab", "ab", "a", "a", "b"]},
                "annotations": {}, "sem": ("1.85", "3.47", "4.90"), "p": ("<0.001", "0.018", "0.696"),
            },
            "pH": {
                "unit": "pH", "basis": "aqueous silage extract; source method citation",
                "cultivar": {"Ryegrass": ["6.14", "6.16", "6.11", "5.17", "4.49", "3.84", "3.97"], "Lp × Fg": ["6.21", "6.28", "5.30", "4.28", "4.04", "3.78", "3.93"]},
                "means": ["6.18", "6.22", "5.71", "4.72", "4.26", "3.81", "3.95"],
                "cultivar_mean": {"Ryegrass": "5.12", "Lp × Fg": "4.83"},
                "groups": {"Ryegrass": ["a", "a", "a", "b", "c", "d", "d"], "Lp × Fg": ["a", "a", "b", "c", "d", "e", "e"], "Mean": ["", "", "", "", "", "", ""]},
                "annotations": {"Ryegrass": {1: "A", 2: "A", 3: "A"}, "Lp × Fg": {1: "B", 2: "B", 3: "B"}}, "sem": ("0.015", "0.029", "0.041"), "p": ("<0.001", "<0.001", "<0.001"),
            },
            "WSC": {
                "unit": "g/kg FD DM", "basis": "freeze-dried dry-matter basis, as printed",
                "cultivar": {"Ryegrass": ["142.1", "133.1", "122.9", "108.8", "100.4", "71.8", "68.9"], "Lp × Fg": ["126.9", "106.6", "90.3", "55.1", "48.2", "24.6", "22.2"]},
                "means": ["134.5", "119.8", "106.6", "81.9", "74.3", "48.2", "45.6"],
                "cultivar_mean": {"Ryegrass": "106.9", "Lp × Fg": "67.7"},
                "groups": {"Ryegrass": ["a", "ab", "b", "c", "c", "d", "d"], "Lp × Fg": ["a", "b", "c", "d", "e", "f", "f"], "Mean": ["", "", "", "", "", "", ""]},
                "annotations": {"Ryegrass": {i: "A" for i in range(7)}, "Lp × Fg": {i: "B" for i in range(7)}}, "sem": ("0.92", "1.73", "2.45"), "p": ("<0.001", "<0.001", "<0.001"),
            },
            "TN": {
                "unit": "g/kg FD DM", "basis": "freeze-dried dry-matter basis, as printed",
                "cultivar": {"Ryegrass": ["30.6", "30.6", "31.2", "31.0", "30.8", "30.6", "30.8"], "Lp × Fg": ["31.2", "32.1", "32.2", "32.0", "32.0", "32.4", "32.2"]},
                "means": ["30.9", "31.4", "31.7", "31.5", "31.4", "31.5", "31.5"],
                "cultivar_mean": {"Ryegrass": "30.8", "Lp × Fg": "32.0"},
                "groups": {"Ryegrass": ["", "", "", "", "", "", ""], "Lp × Fg": ["", "", "", "", "", "", ""], "Mean": ["", "", "", "", "", "", ""]},
                "annotations": {"Ryegrass": {0: "B"}, "Lp × Fg": {0: "A"}}, "sem": ("0.13", "0.24", "0.34"), "p": ("<0.001", "0.451", "0.677"),
            },
            "Soluble N": {
                "unit": "g/kg TN", "basis": "total-nitrogen basis, as printed",
                "cultivar": {"Ryegrass": ["350", "410", "463", "521", "548", "604", "650"], "Lp × Fg": ["360", "409", "490", "503", "528", "597", "662"]},
                "means": ["355", "409", "477", "512", "538", "600", "656"],
                "cultivar_mean": {"Ryegrass": "507", "Lp × Fg": "507"},
                "groups": {"Ryegrass": ["", "", "", "", "", "", ""], "Lp × Fg": ["", "", "", "", "", "", ""], "Mean": ["f", "e", "d", "c", "c", "b", "a"]},
                "annotations": {}, "sem": ("6.2", "11.6", "16.4"), "p": ("0.987", "<0.001", "0.782"),
            },
            "Ammonia-N": {
                "unit": "g/kg TN", "basis": "total-nitrogen basis, as printed",
                "cultivar": {"Ryegrass": ["17.6", "15.9", "22.6", "35.8", "40.1", "55.5", "63.5"], "Lp × Fg": ["14.1", "18.9", "23.3", "43.6", "36.7", "52.2", "73.0"]},
                "means": ["15.9", "17.4", "23.0", "39.7", "38.4", "53.8", "68.3"],
                "cultivar_mean": {"Ryegrass": "35.9", "Lp × Fg": "37.4"},
                "groups": {"Ryegrass": ["", "", "", "", "", "", ""], "Lp × Fg": ["", "", "", "", "", "", ""], "Mean": ["d", "d", "d", "c", "c", "b", "a"]},
                "annotations": {}, "sem": ("1.76", "3.28", "4.64"), "p": ("0.545", "<0.001", "0.660"),
            },
        },
    },
}

FRESH_TABLE = {
    ("Cut 2 (May 2016)", "FD-DM"): {"values": {"Ryegrass": "203.3", "Lp × Fg": "177.9"}, "unit": "g/kg", "basis": "as printed; fresh forage prior to wilting", "sem": "0.89", "p": "<0.001"},
    ("Cut 2 (May 2016)", "WSC"): {"values": {"Ryegrass": "161.9", "Lp × Fg": "162.9"}, "unit": "g/kg FD DM", "basis": "freeze-dried dry-matter basis, as printed", "sem": "4.20", "p": "0.882"},
    ("Cut 2 (May 2016)", "TN"): {"values": {"Ryegrass": "24.9", "Lp × Fg": "26.2"}, "unit": "g/kg FD DM", "basis": "freeze-dried dry-matter basis, as printed", "sem": "0.61", "p": "0.213"},
    ("Cut 4 (August 2016)", "FD-DM"): {"values": {"Ryegrass": "174.2", "Lp × Fg": "173.7"}, "unit": "g/kg", "basis": "as printed; fresh forage prior to wilting", "sem": "17.34", "p": "0.983"},
    ("Cut 4 (August 2016)", "WSC"): {"values": {"Ryegrass": "151.7", "Lp × Fg": "144.1"}, "unit": "g/kg FD DM", "basis": "freeze-dried dry-matter basis, as printed", "sem": "12.49", "p": "0.686"},
    ("Cut 4 (August 2016)", "TN"): {"values": {"Ryegrass": "31.4", "Lp × Fg": "32.1"}, "unit": "g/kg FD DM", "basis": "freeze-dried dry-matter basis, as printed", "sem": "1.53", "p": "0.763"},
}


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _upsert(path: Path, key: str, entries: list[dict[str, str]]) -> None:
    fields, rows = _read_csv(path)
    keys = key.split("|")
    index = {tuple(row.get(field, "") for field in keys): row for row in rows}
    for entry in entries:
        identity = tuple(entry.get(field, "") for field in keys)
        if identity in index:
            index[identity].update(entry)
        else:
            rows.append(entry)
            index[identity] = rows[-1]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(entries[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _row(table: str, cut: str, metric: str, row_type: str, cultivar_code: str, value: str, *,
         unit: str, basis: str, time_index: int | None = None, reported_mean: str = "",
         groups: str = "", annotation: str = "", sem: tuple[str, str, str] = ("", "", ""),
         p: tuple[str, str, str] = ("", "", ""), replicate_design: str = "") -> dict[str, str]:
    time_label, elapsed_hours = TIMEPOINTS[time_index] if time_index is not None else ("", "")
    table_number = table[-1]
    row_num = time_index if time_index is not None else 0
    cultivar = GRASSES.get(cultivar_code, "pooled marginal mean across the two grasses")
    source_location = f"Article {table}; {cut}; {metric} row"
    method_summary = (
        "Table 1 fresh-forage values before wilting; four field plots per treatment were bulked before subsampling."
        if table == "Table 1"
        else "Harvested at 5 cm; 24 h wilt; Lactobacillus plantarum inoculant; chopped to target mean 30 mm; 100 g portions in 160 mL glass silos, dark at 21 C; triplicate silos opened destructively at each ensiling time. Assays: freeze-dried DM, WSC, total N, ammonia-N, soluble N, pH."
    )
    limits = (
        "Cultivated UK forage, not Dutch roadside/VARTA or GreenHub feed. Concentration/pH change is not component retention, "
        "fresh-matter loss, effluent, emissions, or a closed mass balance; do not fit roadside kinetics from this comparator."
    )
    return {
        "record_id": f"MUH23-T{table_number}-{cut.split()[1]}-{metric.upper().replace(' ', '_')}-{row_type}-{cultivar_code.replace(' ', '').replace('×', 'X')}-{row_num:02d}",
        "source_id": SOURCE_ID,
        "phase_relevance": "2;3;4",
        "source_table": table,
        "source_row_type": row_type,
        "harvest_cut": cut,
        "cultivar": cultivar,
        "material_stage": "pre-wilting fresh forage" if table == "Table 1" else "wilted forage/silage in sealed laboratory tube silo",
        "ensiling_time_label": time_label,
        "elapsed_hours_from_ensiling": str(elapsed_hours),
        "metric": metric,
        "value": value,
        "unit": unit,
        "basis": basis,
        "reported_mean_over_time": reported_mean,
        "sem_grass_effect": sem[0],
        "p_grass_effect": p[0],
        "sem_time_effect": sem[1],
        "p_time_effect": p[1],
        "sem_grass_by_time_interaction": sem[2],
        "p_grass_by_time_interaction": p[2],
        "source_significance_group": groups,
        "source_annotation": annotation,
        "replicates_or_sample_design": replicate_design,
        "source_location": source_location,
        "method_summary": method_summary,
        "evidence_class": "B_measured_literature",
        "quality_class": "B",
        "activation_state": "reference_only",
        "transferability": "Cultivated UK perennial ryegrass/Festulolium comparator; not roadside/VARTA/GreenHub feed; species, wilting, inoculant, silo geometry and storage conditions differ.",
        "limitations": limits,
    }


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for (cut, metric), data in FRESH_TABLE.items():
        for cultivar_code, value in data["values"].items():
            rows.append(_row(
                "Table 1", cut, metric, "fresh_forage_cultivar_value", cultivar_code, value,
                unit=data["unit"], basis=data["basis"], sem=(data["sem"], "", ""), p=(data["p"], "", ""),
                replicate_design="Four field plots per treatment were bulked before subsampling; analytical n for Table 1 is not separately reported.",
            ))
    for table, section in TABLES.items():
        cut = section["cut"]
        for metric, data in section["metric_data"].items():
            for cultivar_code in ("Ryegrass", "Lp × Fg"):
                for time_index, value in enumerate(data["cultivar"][cultivar_code]):
                    rows.append(_row(
                        table, cut, metric, "cultivar_time_series", cultivar_code, value,
                        unit=data["unit"], basis=data["basis"], time_index=time_index,
                        reported_mean=data["cultivar_mean"][cultivar_code],
                        groups=data["groups"][cultivar_code][time_index],
                        annotation=data.get("annotations", {}).get(cultivar_code, {}).get(time_index, ""),
                        sem=data["sem"], p=data["p"],
                        replicate_design="Three replicate 100 g laboratory silos per grass treatment and destructive-sampling time point.",
                    ))
            for time_index, value in enumerate(data["means"]):
                rows.append(_row(
                    table, cut, metric, "pooled_mean_time_series", "Mean", value,
                    unit=data["unit"], basis=data["basis"], time_index=time_index,
                    groups=data["groups"]["Mean"][time_index], sem=data["sem"], p=data["p"],
                    replicate_design="Marginal time mean across the two grass treatments; source table reports three replicate silos per treatment/time.",
                ))
    return rows


def _register(rows: list[dict[str, str]]) -> None:
    _upsert(FOLDER / "source_register.csv", "source_id", [SOURCE])
    _upsert(FOLDER / "dataset_manifest.csv", "filename", [{
        "filename": FILENAME,
        "description": "Tables 1–3: fresh-forage and 0 h–90 d laboratory ensiling DM, pH, WSC, total N, soluble N and ammonia-N for cultivated ryegrass and Festulolium; reference-only.",
        "row_count": str(len(rows)), "schema_version": "1.0", "encoding": "UTF-8", "delimiter": ",",
        "integration_status": "traceable_reference_only_not_runtime_eligible", "primary_key": "record_id",
    }])
    rel = f"storage/{FILENAME}"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [{
        "dataset_path": rel, "dataset_group": "storage", "source_id": SOURCE_ID,
        "source_title": SOURCE["source_title"], "authors": SOURCE["authors"], "year": SOURCE["year"],
        "doi_or_stable_id": DOI, "url": URL, "source_type": SOURCE["source_type"], "notes": SOURCE["quality_notes"],
    }])
    numeric_rows = sum(_is_number(row["value"]) for row in rows)
    _upsert(AUDIT / "global_dataset_manifest.csv", "dataset_path", [{
        "dataset_path": rel, "category": "storage", "subgroup": "cultivated-grass ensiling and protein-quality comparator; Phases 2–4",
        "filename": FILENAME, "row_count_observed": str(len(rows)), "header_count": str(len(FIELDS)),
        "headers": "; ".join(FIELDS), "standardized_status_values": "B;reference_only", "detected_readiness": "D3",
        "notes": "Exact Tables 1–3; 21 C laboratory silage. No whole-material mass loss, leachate, emissions, or full component balance; not GreenHub roadside grass.",
    }])
    _upsert(AUDIT / "global_dataset_readiness.csv", "dataset_path", [{
        "dataset_path": rel, "category": "storage", "subgroup": "cultivated-grass ensiling and protein-quality comparator; Phases 2–4",
        "readiness": "D3", "duplicate_ids": "0", "duplicate_rows": "0", "numeric_rows": str(numeric_rows),
        "unsourced_numeric_rows": "0", "numeric_rows_missing_exact_location": "0", "unit_conflicts": "0",
        "basis_conflicts": "0", "cross_reference_issues": "0", "equation_missing_inputs": "0",
        "equation_symbol_mismatches": "0", "notes": "Each value points to its article table/row and harvest cut; source annotations and factorial statistics retained; no runtime connection.",
    }])
    checksums = [{"dataset_path": f"storage/{path.name}", "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "byte_size": str(path.stat().st_size)} for path in (CSV_PATH, SIDECAR_PATH)]
    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", checksums)
    summary_path = AUDIT / "global_validation_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    _, manifests = _read_csv(AUDIT / "global_dataset_manifest.csv")
    _, readiness = _read_csv(AUDIT / "global_dataset_readiness.csv")
    counts: dict[str, int] = {}
    for item in readiness:
        label = item.get("readiness", "")
        counts[label] = counts.get(label, 0) + 1
    summary["dataset_count"] = len(manifests)
    summary["readiness_counts"] = counts
    summary["generated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def main() -> None:
    rows = build_rows()
    if len(rows) != 264 or len({row["record_id"] for row in rows}) != len(rows):
        raise ValueError(f"Expected 264 unique source-table records, got {len(rows)}")
    _write_csv(CSV_PATH, rows)
    digest = hashlib.sha256(CSV_PATH.read_bytes()).hexdigest()
    sidecar = {
        "dataset_id": "urn:greenhub:dataset:storage:muhandiram-cultivated-grass-ensiling-2023:v1",
        "persistent_identifier_status": "Repository-local URN identifies this transcription; DOI identifies the source article, not this derivative dataset.",
        "dataset_version": "1.0.0", "title": "Cultivated ryegrass and Festulolium ensiling composition/proteolysis time series",
        "source_ids": [SOURCE_ID],
        "citation": "Muhandiram, N. P. K. et al. (2023). Designing agricultural grasses to help mitigate proteolysis during ensiling to optimize protein feed provisions for livestock. Food and Energy Security, 12(4), e475. https://doi.org/10.1002/fes3.475",
        "doi": DOI, "source_url": URL, "retrieval_date": RETRIEVED,
        "source_locations": ["Table 1: fresh forage before wilting", "Table 2: Cut 2 time course", "Table 3: Cut 4 time course", "Methods sections 2.1–2.4"],
        "reference_year": 2023, "experiment_year": 2016, "geography": "Aberystwyth, Wales, United Kingdom",
        "material_scope": "Cultivated perennial ryegrass cv AberMagic and Festulolium cv Lp × Fg; two harvest cuts; wilted and ensiled in laboratory tube silos.",
        "experimental_conditions": "Harvested 31 May 2016 and 9 August 2016; wilted 24 h; Lactobacillus plantarum inoculated; target chop length 30 mm; 100 g per 160 mL tube; dark storage at 21 C; triplicate silos opened destructively at 0 h, 9 h, 1 d, 2 d, 3 d, 14 d, and 90 d.",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0), stated on the open-access article.",
        "evidence_class": "B_measured", "quality_class": "B", "activation_state": "reference_only", "calculation_connected": False,
        "row_count": len(rows), "sha256_csv": digest,
        "transcription_policy": "Tables 1–3 values, units, marginal means, SEM, p-values and significance annotations transcribed without conversion. Reported time labels are retained and converted to elapsed hours using 1 d = 24 h only for machine-readable sorting. No kinetic fit, retention calculation, or interpolated time point is added.",
        "fair_metadata": {
            "findable": "Repository-local URN, article DOI, title, authors, year, source tables and registers are provided.",
            "accessible": "UTF-8 CSV and JSON metadata sidecar in the repository; source is open access.",
            "interoperable": "Long-form rows include material, cut, cultivar, time, metric, value, unit, basis, statistics and table locator.",
            "reusable": "CC BY 4.0, extraction/transcription approach, cultivar, geography, laboratory settings, assay summary, and transfer limits are recorded.",
        },
        "limitations": [
            "Cultivated UK ryegrass/Festulolium is not Dutch roadside/VARTA biomass; no direct GreenHub calibration is claimed.",
            "Silo concentrations and pH do not identify fresh-matter loss, effluent, emissions, or retained component mass.",
            "No raw replicate-level observations are supplied in the paper; the extract contains reported means and pooled factorial statistics only.",
            "The two harvest cuts have strongly different material DM; comparisons must retain the cut and cultivar context.",
            "The source used a silage inoculant and laboratory tube silos at 21 C; these are not necessarily GreenHub storage conditions.",
            "No data have been used to replace a runtime kinetic parameter or alter model outputs.",
        ],
    }
    SIDECAR_PATH.write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _register(rows)
    print(json.dumps({"file": str(CSV_PATH), "rows": len(rows), "sha256": digest}, indent=2))


if __name__ == "__main__":
    main()
