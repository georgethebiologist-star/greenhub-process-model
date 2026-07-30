"""Read-only feedstock proxy selection for roadside grass reference data.

This module does not activate model parameters. It only resolves a conservative
proxy inventory from CSV evidence so callers can inspect which source would win.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DATA_DIR = Path(__file__).resolve().parent / "data" / "Pre-treatment" / "Feedstock"
PRIMARY_FILE = DATA_DIR / "roadside_grass_composition_scientific.csv"
OLD_FILES = (
    DATA_DIR / "pretreatment_feed_composition.csv",
    DATA_DIR / "seasonal_feed_variability.csv",
    DATA_DIR / "pretreatment_feed_physical_properties.csv",
)
EXTENDED_CANDIDATE_FILE = DATA_DIR / "roadside_grass_missing_proxy_candidates_extended.csv"


@dataclass(frozen=True)
class FeedstockProxyValue:
    canonical_field: str
    value: float
    unit: str
    source_file: str
    parameter_id: str
    status: str
    direct_or_indirect: str
    notes: str = ""


@dataclass(frozen=True)
class FeedstockProxyCandidate:
    canonical_field: str
    source_priority: int
    readiness_category: str
    can_activate_by_default: bool
    requires_user_selection: bool
    requires_equation_mapping: bool
    requires_basis_conversion: bool
    value: float | None
    unit: str
    value_min: float | None
    value_max: float | None
    raw_value: str
    source_file: str
    parameter_id: str
    source_title: str
    doi_or_url: str
    evidence_quality: str
    direct_or_indirect: str
    limitation_note: str

    def to_dict(self) -> dict[str, object]:
        return {
            "canonical_field": self.canonical_field,
            "source_priority": self.source_priority,
            "readiness_category": self.readiness_category,
            "can_activate_by_default": self.can_activate_by_default,
            "requires_user_selection": self.requires_user_selection,
            "requires_equation_mapping": self.requires_equation_mapping,
            "requires_basis_conversion": self.requires_basis_conversion,
            "value": self.value,
            "unit": self.unit,
            "value_min": self.value_min,
            "value_max": self.value_max,
            "raw_value": self.raw_value,
            "source_file": self.source_file,
            "parameter_id": self.parameter_id,
            "source_title": self.source_title,
            "doi_or_url": self.doi_or_url,
            "evidence_quality": self.evidence_quality,
            "direct_or_indirect": self.direct_or_indirect,
            "limitation_note": self.limitation_note,
        }


PRIMARY_CANONICAL_FIELDS = {
    "fresh_moisture": ("moisture_wet_basis", "active_proxy"),
    "road_verge_moisture_as_received": ("moisture_wet_basis", "active_proxy"),
    "fresh_volatile_matter": ("volatile_solids_dry_basis", "active_proxy"),
    "fresh_ash": ("ash_dry_basis", "active_proxy"),
    "fresh_carbon": ("carbon_dry_basis", "active_proxy"),
    "fresh_hydrogen": ("hydrogen_dry_basis", "active_proxy"),
    "fresh_oxygen": ("oxygen_dry_basis", "active_proxy"),
    "fresh_nitrogen": ("nitrogen_dry_basis", "active_proxy"),
    "fresh_sulfur": ("sulfur_dry_basis", "active_proxy"),
    "fresh_cn_ratio": ("carbon_to_nitrogen_ratio", "active_proxy"),
    "bulk_density": ("bulk_density", "active_proxy"),
    "protein": ("total_protein_dry_basis", "active_proxy"),
    "extractive_sugars": ("extractive_sugars_dry_basis", "active_proxy"),
    "fresh_bmp_buswell": ("bmp_buswell", "reference_only"),
    "fresh_bmp_boyle": ("bmp_boyle", "reference_only"),
}

EXTENDED_CANONICAL_FIELDS = {
    "fresh_solid_ph": "solid_ph",
    "fresh_solid_ec": "solid_electrical_conductivity",
    "solid_cellulose": "cellulose_dry_basis",
    "solid_hemicellulose": "hemicellulose_dry_basis",
    "solid_lignin": "lignin_dry_basis",
    "solid_ndf": "neutral_detergent_fibre_dry_basis",
    "solid_adf": "acid_detergent_fibre_dry_basis",
    "solid_wsc": "water_soluble_carbohydrates_dry_basis",
    "solid_starch": "starch_dry_basis",
    "solid_lipids": "lipids_dry_basis",
    "solid_amino_acids": "amino_acid_profile",
    "solid_true_protein": "true_protein_dry_basis",
    "solid_npn": "non_protein_nitrogen_dry_basis",
    "solid_d50": "median_particle_size",
    "solid_porosity": "bulk_porosity",
    "solid_cp": "specific_heat_capacity",
    "solid_k": "thermal_conductivity",
    "solid_hhv": "higher_heating_value",
    "solid_lhv": "lower_heating_value",
    "solid_chlorine": "chlorine_dry_basis",
    "solid_silica": "silica_in_ash",
    "ensiled_sulfur": "ensiled_sulfur_dry_basis",
    "glf_ec": "liquid_electrical_conductivity",
    "glf_density": "liquid_density",
    "glf_viscosity": "liquid_viscosity",
    "glf_ts": "liquid_total_solids",
    "glf_vs": "liquid_volatile_solids",
    "glf_cod_t": "liquid_total_cod",
    "glf_cod_s": "liquid_soluble_cod",
    "glf_bod5": "liquid_bod5",
    "glf_tic": "liquid_total_inorganic_carbon",
    "glf_alkalinity": "liquid_alkalinity",
    "glf_tan": "liquid_total_ammoniacal_nitrogen",
    "glf_nh4": "liquid_ammonium_nitrogen",
    "glf_no3": "liquid_nitrate_nitrogen",
    "glf_total_p": "liquid_total_phosphorus",
    "glf_po4p": "liquid_orthophosphate_phosphorus",
    "glf_total_k": "liquid_total_potassium",
    "glf_vfa": "liquid_total_vfa",
    "glf_acetate": "liquid_acetate",
    "glf_propionate": "liquid_propionate",
    "glf_butyrate": "liquid_butyrate",
    "glf_lactate": "liquid_lactate",
    "glf_buffer_capacity": "liquid_buffer_capacity",
}

OLD_CANONICAL_FIELDS = {
    "feed_moisture_wb": "moisture_wet_basis",
    "feed_total_solids_wb": "total_solids_wet_basis",
    "feed_volatile_solids_dry": "volatile_solids_dry_basis",
    "feed_ash_dm": "ash_dry_basis",
    "feed_total_organic_carbon_dm": "carbon_dry_basis",
    "feed_total_kjeldahl_nitrogen_dm": "nitrogen_dry_basis",
    "feed_sulfur_dm": "sulfur_dry_basis",
    "feed_bulk_density": "bulk_density",
}

REFERENCE_ONLY_FIELDS = {
    "bmp_buswell",
    "bmp_boyle",
    "total_protein_dry_basis",
    "extractive_sugars_dry_basis",
}


def load_feedstock_proxies(
    primary_file: Path = PRIMARY_FILE,
    old_files: Iterable[Path] = OLD_FILES,
    include_reference: bool = False,
) -> dict[str, FeedstockProxyValue]:
    """Return conservative canonical proxy values.

    Direct numeric rows in the new roadside CSV win. Older Czubaszek/Wrobel rows
    are fallback-only for canonical fields with no usable primary value. Missing
    and indirect rows are never returned as active proxy values.
    """
    selected: dict[str, FeedstockProxyValue] = {}
    reference: dict[str, FeedstockProxyValue] = {}

    for row in _read_rows(primary_file):
        parameter_id = row.get("parameter_id", "")
        mapping = PRIMARY_CANONICAL_FIELDS.get(parameter_id)
        if mapping is None or not _usable_primary_row(row):
            continue
        canonical_field, status = mapping
        value = FeedstockProxyValue(
            canonical_field=canonical_field,
            value=float(row["value_si"]),
            unit=row.get("unit_si", ""),
            source_file=primary_file.name,
            parameter_id=parameter_id,
            status=status,
            direct_or_indirect=row.get("direct_or_indirect", ""),
            notes=row.get("limitation_note", "") or row.get("notes", ""),
        )
        if status == "reference_only":
            reference.setdefault(canonical_field, value)
        else:
            selected.setdefault(canonical_field, value)

    for old_file in old_files:
        for row in _read_rows(old_file):
            canonical_field = OLD_CANONICAL_FIELDS.get(row.get("python_variable", ""))
            if canonical_field is None or canonical_field in selected:
                continue
            if not _usable_old_row(row):
                continue
            selected[canonical_field] = FeedstockProxyValue(
                canonical_field=canonical_field,
                value=float(row["normalized_si_value"]),
                unit=row.get("normalized_si_unit", ""),
                source_file=old_file.name,
                parameter_id=row.get("parameter_id", ""),
                status="fallback_only",
                direct_or_indirect=row.get("transferability", ""),
                notes=row.get("notes", ""),
            )

    if include_reference:
        return {**selected, **reference}
    return selected


def classify_feedstock_proxy_evidence(
    primary_file: Path = PRIMARY_FILE,
    extended_candidate_file: Path = EXTENDED_CANDIDATE_FILE,
    old_files: Iterable[Path] = OLD_FILES,
) -> list[FeedstockProxyCandidate]:
    return feedstock_proxy_resolution_candidates(primary_file, extended_candidate_file, old_files)


def feedstock_proxy_resolution_candidates(
    primary_file: Path = PRIMARY_FILE,
    extended_candidate_file: Path = EXTENDED_CANDIDATE_FILE,
    old_files: Iterable[Path] = OLD_FILES,
) -> list[FeedstockProxyCandidate]:
    candidates: list[FeedstockProxyCandidate] = []
    for row in _read_rows(primary_file):
        candidates.append(_candidate_from_row(row, primary_file.name, "primary"))
    for old_file in old_files:
        for row in _read_rows(old_file):
            candidates.append(_candidate_from_row(row, old_file.name, "old"))
    for row in _read_rows(extended_candidate_file):
        candidates.append(_candidate_from_row(row, extended_candidate_file.name, "extended"))
    return candidates


def summarize_feedstock_proxy_evidence(
    candidates: Iterable[FeedstockProxyCandidate] | None = None,
) -> list[dict[str, object]]:
    items = list(candidates) if candidates is not None else feedstock_proxy_resolution_candidates()
    counts: dict[tuple[str, str], int] = {}
    for item in items:
        key = (item.readiness_category, item.source_file)
        counts[key] = counts.get(key, 0) + 1
    return [
        {"category": category, "count": count, "source_file": source_file}
        for (category, source_file), count in sorted(counts.items())
    ]


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _usable_primary_row(row: dict[str, str]) -> bool:
    if row.get("evidence_status") == "missing":
        return False
    if row.get("direct_or_indirect") != "direct":
        return False
    return _has_number(row.get("value_si", ""))


def _usable_old_row(row: dict[str, str]) -> bool:
    if row.get("data_status") == "missing":
        return False
    transferability = row.get("transferability", "")
    if transferability and transferability not in {"direct", "calculated_from_source_formula"}:
        return False
    return _has_number(row.get("normalized_si_value", ""))


def _candidate_from_row(row: dict[str, str], source_file: str, source_kind: str) -> FeedstockProxyCandidate:
    category = _readiness_category(row, source_kind)
    can_activate_by_default = _can_activate_by_default(row, source_kind, category)
    return FeedstockProxyCandidate(
        canonical_field=_canonical_field(row),
        source_priority=_source_priority(category),
        readiness_category=category,
        can_activate_by_default=can_activate_by_default,
        requires_user_selection=not can_activate_by_default and category not in {"below_detection_limit", "blocked_missing"},
        requires_equation_mapping=_requires_equation_mapping(row, category),
        requires_basis_conversion=_requires_basis_conversion(row, category),
        value=_optional_number(_value_text(row)),
        unit=_unit_text(row),
        value_min=_optional_number(row.get("value_min", "")),
        value_max=_optional_number(row.get("value_max", "")),
        raw_value=_raw_value_text(row),
        source_file=source_file,
        parameter_id=row.get("parameter_id", ""),
        source_title=row.get("source_title", ""),
        doi_or_url=row.get("doi", "") or row.get("doi_or_stable_identifier", "") or row.get("url", ""),
        evidence_quality=row.get("evidence_quality", "") or row.get("transferability", ""),
        direct_or_indirect=row.get("direct_or_indirect", "") or row.get("transferability", ""),
        limitation_note=row.get("limitation_note", "") or row.get("notes", ""),
    )


def _readiness_category(row: dict[str, str], source_kind: str) -> str:
    evidence_status = row.get("evidence_status", "")
    data_status = row.get("data_status", "")
    directness = row.get("direct_or_indirect", "")
    transferability = row.get("transferability", "")
    raw_value = _raw_value_text(row)

    if data_status == "project_measured":
        return "project_data_ready"
    if evidence_status == "missing" or data_status == "missing":
        return "blocked_missing"
    if raw_value.strip().upper() == "ND":
        return "below_detection_limit"
    if evidence_status == "equation_only":
        return "blocked_no_equation_mapping"
    if _basis_is_unclear(row):
        return "blocked_wrong_basis"
    if source_kind == "old" and _usable_old_row(row):
        return "fallback_literature_proxy"
    if directness == "indirect" or transferability == "comparable proxy":
        return "sensitivity_only_indirect_proxy"
    if _canonical_field(row) in {"bmp_buswell", "bmp_boyle"}:
        return "reference_only"
    if source_kind == "primary" and _usable_primary_row(row):
        return "direct_literature_proxy"
    if source_kind == "extended" and directness == "direct" and _has_value_or_range(row):
        return "direct_literature_proxy"
    if _has_value_or_range(row):
        return "reference_only"
    return "blocked_missing"


def _can_activate_by_default(row: dict[str, str], source_kind: str, category: str) -> bool:
    if category != "direct_literature_proxy" or source_kind != "primary":
        return False
    mapping = PRIMARY_CANONICAL_FIELDS.get(row.get("parameter_id", ""))
    return mapping is not None and mapping[1] == "active_proxy" and _usable_primary_row(row)


def _canonical_field(row: dict[str, str]) -> str:
    parameter_id = row.get("parameter_id", "")
    if parameter_id in PRIMARY_CANONICAL_FIELDS:
        return PRIMARY_CANONICAL_FIELDS[parameter_id][0]
    if parameter_id in EXTENDED_CANONICAL_FIELDS:
        return EXTENDED_CANONICAL_FIELDS[parameter_id]
    python_variable = row.get("python_variable", "")
    if python_variable in OLD_CANONICAL_FIELDS:
        return OLD_CANONICAL_FIELDS[python_variable]
    for suffix in (
        "_proxy_lolium_2017",
        "_proxy_lolium_2025",
        "_proxy_phleum_2025",
        "_proxy_phleum_secondary",
        "_proxy_perennial_grasses_range",
        "_proxy_napier",
        "_proxy_napier_context",
    ):
        if parameter_id.endswith(suffix):
            base = parameter_id[: -len(suffix)]
            return EXTENDED_CANONICAL_FIELDS.get(base, base)
    return python_variable or parameter_id


def _source_priority(category: str) -> int:
    priorities = {
        "project_data_ready": 0,
        "direct_literature_proxy": 10,
        "fallback_literature_proxy": 20,
        "sensitivity_only_indirect_proxy": 30,
        "reference_only": 40,
        "below_detection_limit": 50,
        "blocked_no_equation_mapping": 80,
        "blocked_wrong_basis": 85,
        "blocked_missing": 90,
    }
    return priorities.get(category, 99)


def _requires_equation_mapping(row: dict[str, str], category: str) -> bool:
    if category == "blocked_no_equation_mapping":
        return True
    return bool(row.get("equation_id", ""))


def _requires_basis_conversion(row: dict[str, str], category: str) -> bool:
    if category == "blocked_wrong_basis":
        return True
    original_unit = row.get("unit_original", "") or row.get("unit", "")
    si_unit = row.get("unit_si", "") or row.get("normalized_si_unit", "")
    return bool(original_unit and si_unit and original_unit != si_unit)


def _basis_is_unclear(row: dict[str, str]) -> bool:
    text = " ".join(
        [
            row.get("limitation_note", ""),
            row.get("applicability_note", ""),
            row.get("operating_conditions", ""),
        ]
    ).lower()
    return "basis" in text and ("unclear" in text or "confirm" in text or "requires confirmation" in text)


def _has_value_or_range(row: dict[str, str]) -> bool:
    return _has_number(_value_text(row)) or _has_number(row.get("value_min", "")) or _has_number(row.get("value_max", ""))


def _value_text(row: dict[str, str]) -> str:
    return row.get("value_si", "") or row.get("normalized_si_value", "")


def _raw_value_text(row: dict[str, str]) -> str:
    return row.get("value_original", "") or row.get("value", "")


def _unit_text(row: dict[str, str]) -> str:
    return row.get("unit_si", "") or row.get("normalized_si_unit", "") or row.get("unit", "")


def _optional_number(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _has_number(value: str) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True
