"""Read-only evidence adapters for report-only dynamic process policies.

The source CSV files remain authoritative.  This module normalizes their
different schemas into JSON-safe records without editing source values or
silently converting ranges, bounds, or incompatible bases.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


DATA_ROOT = Path(__file__).resolve().parent / "data"

EVIDENCE_CLASSES = {
    "direct_usable",
    "proxy_usable",
    "proxy_scenario_bound",
    "alternative_method_only",
    "metadata_only",
    "blocked_missing",
    "blocked_wrong_boundary",
    "blocked_wrong_basis",
}


@dataclass(frozen=True)
class DynamicUnitEvidence:
    """One source row normalized without changing its scientific meaning."""

    dataset: str
    source_file: str
    parameter_id: str
    record_id: str
    python_variable: str
    raw_value: str
    normalized_value: float | None
    unit: str
    normalized_unit: str
    basis: str
    process: str
    material_feed_type: str
    data_status: str
    evidence_class: str
    blocker_reasons: tuple[str, ...]
    proxy_class: str
    transferability_to_greenhub: str
    source_id: str
    source_title: str
    doi_or_url: str
    source_location: str
    original_material: str
    original_process_boundary: str
    notes: str
    raw_record: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DynamicUnitEvidenceLoadResult:
    """Typed result for one evidence package."""

    dataset: str
    records: tuple[DynamicUnitEvidence, ...]
    source_files: tuple[str, ...]
    warnings: tuple[str, ...]

    def by_parameter_id(self, parameter_id: str) -> DynamicUnitEvidence | None:
        return next((row for row in self.records if row.parameter_id == parameter_id), None)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def load_centrifuge_policy_evidence() -> DynamicUnitEvidenceLoadResult:
    """Load capture evidence; digestate rows remain wrong-boundary records."""

    return _load_package(
        "centrifuge",
        DATA_ROOT / "Centrifuge",
        ("centrifuge_component_capture.csv",),
    )


def load_direct_raw_press_evidence() -> DynamicUnitEvidenceLoadResult:
    """Load direct-grass and optional red-clover raw-press evidence."""

    return _load_package(
        "raw_press_direct",
        DATA_ROOT / "Pre-treatment" / "Mechanical",
        ("greenhub_direct_raw_press_component_partitioning.csv",),
    )


def load_centrifuge_debris_capture_evidence() -> DynamicUnitEvidenceLoadResult:
    """Load raw-juice debris capture evidence and unresolved direct markers."""

    return _load_package(
        "centrifuge_debris",
        DATA_ROOT / "Centrifuge",
        ("greenhub_centrifuge_debris_suspended_protein_capture.csv",),
    )


def load_second_centrifuge_capture_evidence() -> DynamicUnitEvidenceLoadResult:
    """Load post-precipitation cake-state and protein-recovery evidence."""

    return _load_package(
        "second_centrifuge",
        DATA_ROOT / "Centrifuge",
        ("greenhub_second_centrifuge_protein_capture.csv",),
    )


def load_isoelectric_recovery_evidence() -> DynamicUnitEvidenceLoadResult:
    """Load isoelectric recovery, losses, pH, capture, and cake-moisture rows."""

    return _load_package(
        "isoelectric",
        DATA_ROOT / "Protein recovery" / "Isoelectric",
        (
            "recovery.csv",
            "protein_losses.csv",
            "acid_base_demand.csv",
            "separation_efficiency.csv",
            "product_moisture.csv",
        ),
    )


def load_lactic_acid_recovery_evidence() -> DynamicUnitEvidenceLoadResult:
    """Load alternative lactic-acid protein-recovery evidence."""

    return _load_package(
        "lactic_acid",
        DATA_ROOT / "Protein recovery" / "Lactic_Acid",
        ("protein_recovery_response.csv", "fermentation_time_series.csv"),
    )


def load_membrane_recovery_evidence() -> DynamicUnitEvidenceLoadResult:
    """Load membrane rejection and energy evidence."""

    return _load_package(
        "membrane",
        DATA_ROOT / "Protein recovery" / "Membrane",
        ("rejection_data_by_component.csv", "flux_time_series.csv", "energy_data.csv"),
    )


def load_drying_policy_evidence() -> DynamicUnitEvidenceLoadResult:
    """Load spray/freeze drying observations and required parameter rows."""

    return _load_package(
        "drying",
        DATA_ROOT / "Protein recovery" / "Drying",
        (
            "spray_drying_observations.csv",
            "spray_drying_parameters.csv",
            "freeze_drying_observations.csv",
            "freeze_drying_parameters.csv",
        ),
    )


def load_ad_bmp_evidence() -> DynamicUnitEvidenceLoadResult:
    """Load BMP observations for residual-stream metadata only."""

    return _load_package(
        "ad_bmp",
        DATA_ROOT / "Bigas production + upgrade" / "Feed BMP",
        ("ad_bmp_observations.csv",),
    )


def summarize_dynamic_unit_evidence(
    results: Iterable[DynamicUnitEvidenceLoadResult],
) -> dict[str, object]:
    """Return a compact JSON-safe count summary for future API/dashboard use."""

    summary: dict[str, object] = {}
    for result in results:
        counts = {name: 0 for name in sorted(EVIDENCE_CLASSES)}
        for row in result.records:
            counts[row.evidence_class] += 1
        summary[result.dataset] = {
            "record_count": len(result.records),
            "classification_counts": counts,
            "source_files": list(result.source_files),
            "warnings": list(result.warnings),
        }
    return summary


def _load_package(
    dataset: str,
    root: Path,
    filenames: tuple[str, ...],
) -> DynamicUnitEvidenceLoadResult:
    source_ids = _source_id_map(root)
    records: list[DynamicUnitEvidence] = []
    source_files: list[str] = []
    warnings: list[str] = []
    for filename in filenames:
        path = root / filename
        if not path.exists():
            warnings.append(f"missing_source_file:{filename}")
            continue
        source_files.append(_relative(path))
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                warnings.append(f"empty_source_file:{filename}")
                continue
            for raw in reader:
                row = {str(key): str(value or "").strip() for key, value in raw.items() if key}
                records.append(_normalize_row(dataset, filename, row, source_ids))
    return DynamicUnitEvidenceLoadResult(
        dataset=dataset,
        records=tuple(records),
        source_files=tuple(source_files),
        warnings=tuple(warnings),
    )


def _normalize_row(
    dataset: str,
    filename: str,
    row: dict[str, str],
    source_ids: dict[str, str],
) -> DynamicUnitEvidence:
    parameter_id = _first(row, "parameter_id", "record_id", "observation_id")
    record_id = _first(row, "record_id", "observation_id", "parameter_id")
    raw_value = _first(row, "value", "reported_value")
    normalized_raw = _first(row, "normalized_si_value", "normalized_value")
    normalized_value = _scalar(normalized_raw) if normalized_raw else _scalar(raw_value)
    source_title = _first(row, "source_title", "title")
    evidence_class, blockers, proxy_class = _classify(
        dataset,
        filename,
        parameter_id,
        row,
        normalized_value,
    )
    source_id = _first(row, "source_id") or source_ids.get(source_title.casefold(), "")
    doi = _first(row, "doi_or_stable_identifier", "doi_or_stable_id")
    url = _first(row, "source_url", "source_url_or_doi", "url")
    process = _first(row, "process", "drying_method", "process_step")
    material = _first(
        row,
        "material_feed_type",
        "material_scope",
        "material_class",
        "material",
        "species_or_feedstock",
    )
    transferability = _first(
        row,
        "transferability_to_greenhub",
        "transferability_to_grass",
        "transferability",
        "transferability_class",
    )
    notes = " ".join(
        part for part in (_first(row, "notes"), _first(row, "transferability_explanation")) if part
    )
    return DynamicUnitEvidence(
        dataset=dataset,
        source_file=_relative(DATA_ROOT / _dataset_folder(dataset) / filename),
        parameter_id=parameter_id,
        record_id=record_id,
        python_variable=_first(row, "python_variable"),
        raw_value=raw_value,
        normalized_value=normalized_value,
        unit=_first(row, "unit", "reported_unit"),
        normalized_unit=_first(row, "normalized_si_unit", "normalized_unit"),
        basis=_first(row, "basis"),
        process=process,
        material_feed_type=material,
        data_status=_first(row, "data_status"),
        evidence_class=evidence_class,
        blocker_reasons=blockers,
        proxy_class=proxy_class,
        transferability_to_greenhub=transferability,
        source_id=source_id,
        source_title=source_title,
        doi_or_url=url or doi,
        source_location=_first(
            row,
            "exact_source_location",
            "source_location",
            "page_or_table",
        ),
        original_material=material,
        original_process_boundary=_first(row, "process_boundary") or process,
        notes=notes,
        raw_record=row,
    )


def _classify(
    dataset: str,
    filename: str,
    parameter_id: str,
    row: dict[str, str],
    normalized_value: float | None,
) -> tuple[str, tuple[str, ...], str]:
    status = _first(row, "data_status").casefold()
    material = _first(row, "material_feed_type").casefold()
    basis = _first(row, "basis").casefold()
    proxy = _first(row, "proxy_class")
    if status == "missing" or parameter_id.endswith("M01") or "-M0" in parameter_id:
        return "blocked_missing", ("source_value_missing",), proxy or "none"

    if dataset == "raw_press_direct":
        transferability = _first(row, "transferability_class").casefold()
        if parameter_id.startswith("RAW_00") and normalized_value is not None:
            if "legume" in transferability:
                return "proxy_usable", ("red_clover_legume_proxy",), "red_clover_raw_press_proxy"
            return "direct_usable", (), "direct_grass_source"
        return "metadata_only", (), "raw_press_validation_metadata"

    if dataset == "centrifuge_debris":
        if parameter_id in {"CEN_0011", "CEN_0013"} and normalized_value is not None:
            return "proxy_usable", ("alfalfa_proxy",), "alfalfa_raw_debris_proxy"
        if parameter_id.startswith("CEN_003"):
            return "blocked_missing", ("direct_fresh_grass_value_unresolved",), "none"
        return "metadata_only", (), "centrifuge_context_or_validation_metadata"

    if dataset == "second_centrifuge":
        if parameter_id == "PCEN_0003" and normalized_value is not None:
            return "direct_usable", (), "direct_grass_source"
        if parameter_id == "PCEN_0010":
            return "proxy_scenario_bound", (
                "combined_precipitation_and_centrifugation_boundary",
                "lower_bound_not_point_measurement",
            ), "combined_recovery_lower_bound"
        if parameter_id.startswith("PCEN_002"):
            return "blocked_missing", ("direct_value_unresolved",), "none"
        return "metadata_only", (), "second_centrifuge_context_or_validation_metadata"

    if dataset == "centrifuge":
        if parameter_id == "CAP-ALF-001":
            return "proxy_scenario_bound", ("alfalfa_proxy", "lower_bound_not_point_measurement"), "alfalfa_green_juice_proxy"
        if "digestate" in material:
            return "blocked_wrong_boundary", ("digestate_not_grass_juice",), "digestate_proxy_rejected"
        return "metadata_only", (), proxy or "equipment_or_validation_metadata"

    if dataset == "isoelectric":
        if parameter_id == "REC-001":
            return "proxy_usable", ("nitrogen_basis_requires_explicit_protein_proxy",), "n_to_soluble_protein_proxy"
        if parameter_id == "REC-004":
            return "proxy_usable", ("alfalfa_extract_proxy",), "alfalfa_acid_precipitation_proxy"
        if parameter_id.startswith("REC-"):
            return "blocked_wrong_boundary", ("overall_route_includes_fiber_or_wrong_material",), "route_boundary_proxy_rejected"
        return "metadata_only", (), proxy or "process_metadata"

    if dataset == "lactic_acid":
        if parameter_id == "PR-005":
            return "proxy_scenario_bound", ("whole_plant_basis_not_clarified_juice_basis",), "alfalfa_plant_basis_recovery_proxy"
        if parameter_id.startswith("PR-"):
            return "alternative_method_only", (), proxy or "lactic_acid_alternative"
        return "metadata_only", (), proxy or "fermentation_metadata"

    if dataset == "membrane":
        if parameter_id == "REJ-001":
            return "proxy_usable", ("crude_protein_rejection_not_species_recovery",), "crude_protein_rejection_proxy"
        if parameter_id.startswith("REJ-"):
            return "metadata_only", (), proxy or "membrane_component_metadata"
        return "metadata_only", (), proxy or "membrane_operating_metadata"

    if dataset == "drying":
        if normalized_value is None:
            return "metadata_only", (), proxy or "drying_envelope_metadata"
        if proxy and proxy != "none":
            return "proxy_scenario_bound", ("not_a_grass_product_moisture_or_energy_value",), proxy
        return "metadata_only", (), proxy or "drying_metadata"

    if dataset == "ad_bmp":
        if parameter_id.startswith("BMP_DFOS"):
            return "proxy_usable", ("de_fos_whey_proxy_for_supernatant_like_residual",), "de_fos_whey_residual_proxy"
        if parameter_id.startswith("BMP_PC"):
            return "metadata_only", ("press_cake_outside_project_ad_boundary",), "external_press_cake_metadata"
        return "metadata_only", (), proxy or "ad_metadata"

    if normalized_value is None and ("fraction" in basis or "fraction" in _first(row, "unit").casefold()):
        return "blocked_wrong_basis", ("non_scalar_or_unparseable_value",), proxy or "none"
    return "metadata_only", (), proxy or "none"


def _source_id_map(root: Path) -> dict[str, str]:
    candidates = sorted(root.glob("*source_register.csv"))
    mapping: dict[str, str] = {}
    for path in candidates:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                title = str(row.get("source_title") or row.get("title") or "").strip()
                source_id = str(row.get("source_id") or "").strip()
                if title and source_id:
                    mapping[title.casefold()] = source_id
    return mapping


def _dataset_folder(dataset: str) -> Path:
    return {
        "raw_press_direct": Path("Pre-treatment") / "Mechanical",
        "centrifuge_debris": Path("Centrifuge"),
        "second_centrifuge": Path("Centrifuge"),
        "centrifuge": Path("Centrifuge"),
        "isoelectric": Path("Protein recovery") / "Isoelectric",
        "lactic_acid": Path("Protein recovery") / "Lactic_Acid",
        "membrane": Path("Protein recovery") / "Membrane",
        "drying": Path("Protein recovery") / "Drying",
        "ad_bmp": Path("Bigas production + upgrade") / "Feed BMP",
    }[dataset]


def _first(row: dict[str, str], *names: str) -> str:
    return next((row.get(name, "").strip() for name in names if row.get(name, "").strip()), "")


def _scalar(value: str) -> float | None:
    text = value.strip().replace(",", ".")
    if not text or any(marker in text for marker in ("–", "—", "<", ">", "to ")):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path(__file__).resolve().parents[1]).as_posix()
    except ValueError:
        return path.as_posix()
