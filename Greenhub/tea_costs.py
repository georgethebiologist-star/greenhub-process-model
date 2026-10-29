"""Canonical, read-only access to the compact GreenHub TEA cost register.

The committed CSV is the runtime source.  ``normalize_cost_register_workbook``
is a maintenance helper that rebuilds it from the reviewed Excel workbook; it
does not participate in process simulation or TEA calculations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
from pathlib import Path
import re
from typing import Iterable


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_TEA_COST_REGISTER = PACKAGE_ROOT / "data" / "tea" / "tea_cost_register.csv"
DEFAULT_TEA_WORKBOOK = PACKAGE_ROOT / "data" / "GreenHub_TEA_Compact_Cost_Register (1).xlsx"

CANONICAL_COLUMNS = (
    "cost_id", "process_area", "process_step", "equipment_or_cost_item",
    "item_category", "scenario_or_route_tags", "alternative_group",
    "can_sum_by_default", "cost_type", "reference_value_eur", "reference_unit",
    "reference_capacity", "capacity_unit", "scaling_exponent", "installed_factor",
    "annual_unit_cost_eur", "lifetime_years", "replacement_frequency",
    "source_title", "source_url", "confidence", "notes", "source_status",
    "cost_boundary_includes", "cost_boundary_excludes", "package_group",
    "package_role", "rate_value", "rate_unit", "source_sheet", "source_row",
)


@dataclass(frozen=True)
class TEACostRecord:
    """One traceable screening-cost record, normalized without route decisions."""

    cost_id: str
    process_area: str
    process_step: str
    equipment_or_cost_item: str
    item_category: str
    scenario_or_route_tags: tuple[str, ...]
    alternative_group: str | None
    can_sum_by_default: bool
    cost_type: str
    reference_value_eur: float | None
    reference_unit: str | None
    reference_capacity: float | None
    capacity_unit: str | None
    scaling_exponent: float | None
    installed_factor: float | None
    annual_unit_cost_eur: float | None
    lifetime_years: float | None
    replacement_frequency: str | None
    source_title: str
    source_url: str
    confidence: str
    notes: str
    source_status: str = ""
    cost_boundary_includes: str = ""
    cost_boundary_excludes: str = ""
    package_group: str | None = None
    package_role: str | None = None
    rate_value: float | None = None
    rate_unit: str | None = None
    source_sheet: str = "Cost Inventory"
    source_row: int | None = None

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["scenario_or_route_tags"] = list(self.scenario_or_route_tags)
        return payload


def load_tea_cost_register(path: str | Path | None = None) -> tuple[TEACostRecord, ...]:
    """Load the committed normalized register without importing Excel tooling."""

    register_path = Path(path) if path is not None else DEFAULT_TEA_COST_REGISTER
    if not register_path.exists():
        raise FileNotFoundError(f"TEA cost register not found: {register_path}")
    records: list[TEACostRecord] = []
    with register_path.open("r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            records.append(
                TEACostRecord(
                    cost_id=row["cost_id"].strip(),
                    process_area=row["process_area"].strip(),
                    process_step=row["process_step"].strip(),
                    equipment_or_cost_item=row["equipment_or_cost_item"].strip(),
                    item_category=row["item_category"].strip(),
                    scenario_or_route_tags=_split_tags(row.get("scenario_or_route_tags", "")),
                    alternative_group=_optional_text(row.get("alternative_group")),
                    can_sum_by_default=_parse_bool(row.get("can_sum_by_default")),
                    cost_type=row["cost_type"].strip(),
                    reference_value_eur=_parse_float(row.get("reference_value_eur")),
                    reference_unit=_optional_text(row.get("reference_unit")),
                    reference_capacity=_parse_float(row.get("reference_capacity")),
                    capacity_unit=_optional_text(row.get("capacity_unit")),
                    scaling_exponent=_parse_float(row.get("scaling_exponent")),
                    installed_factor=_parse_float(row.get("installed_factor")),
                    annual_unit_cost_eur=_parse_float(row.get("annual_unit_cost_eur")),
                    lifetime_years=_parse_float(row.get("lifetime_years")),
                    replacement_frequency=_optional_text(row.get("replacement_frequency")),
                    source_title=row.get("source_title", "").strip(),
                    source_url=row.get("source_url", "").strip(),
                    confidence=row.get("confidence", "").strip(),
                    notes=row.get("notes", "").strip(),
                    source_status=row.get("source_status", "").strip(),
                    cost_boundary_includes=row.get("cost_boundary_includes", "").strip(),
                    cost_boundary_excludes=row.get("cost_boundary_excludes", "").strip(),
                    package_group=_optional_text(row.get("package_group")),
                    package_role=_optional_text(row.get("package_role")),
                    rate_value=_parse_float(row.get("rate_value")),
                    rate_unit=_optional_text(row.get("rate_unit")),
                    source_sheet=row.get("source_sheet", "Cost Inventory").strip(),
                    source_row=_parse_int(row.get("source_row")),
                )
            )
    _validate_register(records)
    return tuple(records)


def normalize_cost_register_workbook(
    workbook_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> Path:
    """Rebuild the canonical CSV from the workbook's compact inventory sheet.

    Route tags and anti-double-count metadata are a transparent GreenHub
    crosswalk.  Numeric source values, evidence text, and URLs are preserved.
    The generic upgrader row is expanded into method-specific source anchors
    from the workbook's Scenarios sheet so mutually exclusive routes can be
    priced independently.
    """

    try:
        from openpyxl import load_workbook
    except ImportError as error:  # pragma: no cover - maintenance environment only
        raise RuntimeError("openpyxl is required only to rebuild the TEA CSV.") from error

    source = Path(workbook_path) if workbook_path is not None else DEFAULT_TEA_WORKBOOK
    destination = Path(output_path) if output_path is not None else DEFAULT_TEA_COST_REGISTER
    workbook = load_workbook(source, read_only=True, data_only=True)
    sheet = workbook["Cost Inventory"]
    headers = [str(value or "").strip() for value in next(sheet.iter_rows(min_row=4, max_row=4, values_only=True))]
    rows: list[dict[str, object]] = []
    compact_index = 0
    for excel_row, values in enumerate(sheet.iter_rows(min_row=5, values_only=True), start=5):
        source_row = dict(zip(headers, values))
        if not source_row.get("equipment_or_cost_item"):
            continue
        compact_index += 1
        if compact_index == 17:
            rows.extend(_expanded_upgrader_rows(source_row, excel_row))
        else:
            rows.append(_canonicalize_row(source_row, compact_index, excel_row))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CANONICAL_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return destination


def _canonicalize_row(source: dict[str, object], index: int, excel_row: int) -> dict[str, object]:
    area = str(source.get("process_area") or "").strip()
    step = str(source.get("process_step") or "").strip()
    item = str(source.get("equipment_or_cost_item") or "").strip()
    category = str(source.get("item_category") or "").strip()
    cost_id = f"TEA-{index:03d}"
    tags, alternative_group, can_sum, package_group, package_role = _route_metadata(index)
    cost_type = _cost_type(category)
    source_value = _parse_float(source.get("converted_value_eur"))
    source_unit = _optional_text(source.get("converted_unit"))
    reference_value = source_value
    annual_unit_cost = source_value if cost_type in {
        "utility", "consumable", "labor", "logistics", "disposal"
    } else None
    rate_value = None
    rate_unit = None
    if index in {28, 30, 41}:
        reference_value = None
        annual_unit_cost = None
        rate_value = source_value
        rate_unit = source_unit
    reference_capacity, capacity_unit, adjusted_reference = _capacity_anchor(index, source_value)
    if adjusted_reference is not None:
        reference_value = adjusted_reference
    installed_factor = 1.0 if index in {13, 18} else None
    notes = " | ".join(
        str(value).strip()
        for value in (
            source.get("assumption / proxy notes"),
            source.get("NL_adjustment / price basis"),
            source.get("next quote / measurement needed"),
        )
        if value not in (None, "")
    )
    return {
        "cost_id": cost_id,
        "process_area": area,
        "process_step": step,
        "equipment_or_cost_item": item,
        "item_category": category,
        "scenario_or_route_tags": "|".join(tags),
        "alternative_group": alternative_group or "",
        "can_sum_by_default": str(can_sum).lower(),
        "cost_type": cost_type,
        "reference_value_eur": _csv_number(reference_value),
        "reference_unit": source_unit or "",
        "reference_capacity": _csv_number(reference_capacity),
        "capacity_unit": capacity_unit or _optional_text(source.get("capacity_basis")) or "",
        "scaling_exponent": _csv_number(source.get("scaling_exponent")),
        "installed_factor": _csv_number(installed_factor),
        "annual_unit_cost_eur": _csv_number(annual_unit_cost),
        "lifetime_years": _csv_number(source.get("expected_lifetime_years")),
        "replacement_frequency": source.get("replacement_frequency") or "",
        "source_title": source.get("source_title") or "",
        "source_url": source.get("source_url") or "",
        "confidence": source.get("confidence") or "",
        "notes": notes,
        "source_status": source.get("evidence_status") or "",
        "cost_boundary_includes": source.get("cost_boundary_includes") or "",
        "cost_boundary_excludes": source.get("cost_boundary_excludes") or "",
        "package_group": package_group or "",
        "package_role": package_role or "",
        "rate_value": _csv_number(rate_value),
        "rate_unit": rate_unit or "",
        "source_sheet": "Cost Inventory",
        "source_row": excel_row,
    }


def _expanded_upgrader_rows(source: dict[str, object], excel_row: int) -> list[dict[str, object]]:
    # Base prices and reference flows are stated in workbook Scenarios rows 14-16
    # and repeated in this compact row's included-boundary text.
    methods = (
        ("PSA", "psa", 1750.0, 1250.0, "BG4"),
        ("Water scrubbing", "water_scrubbing", 1500.0, 1000.0, "BG2"),
        ("Membrane", "membrane_upgrading", 2000.0, 800.0, "BG3"),
    )
    rows = []
    for suffix, method, unit_rate, capacity, scenario in methods:
        copied = dict(source)
        copied["equipment_or_cost_item"] = f"{suffix} upgrader package"
        copied["converted_value_eur"] = unit_rate * capacity
        copied["converted_unit"] = f"EUR/package at {capacity:g} Nm3/h raw gas"
        row = _canonicalize_row(copied, 17, excel_row)
        row.update(
            cost_id=f"TEA-017-{method.upper()}",
            scenario_or_route_tags=f"{scenario}|{method}",
            alternative_group="biogas_upgrading_method",
            reference_capacity=capacity,
            capacity_unit="Nm3/h raw gas",
            package_group="biogas_upgrader_package",
            package_role="package",
        )
        row["notes"] = (
            f"Derived package anchor = workbook base unit rate {unit_rate:g} EUR/(Nm3/h) "
            f"x stated base capacity {capacity:g} Nm3/h. | {row['notes']}"
        )
        rows.append(row)
    return rows


def _route_metadata(index: int) -> tuple[tuple[str, ...], str | None, bool, str | None, str | None]:
    metadata = {
        1: (("F1", "F2", "F3", "feedstock_reception"), None, True, "feed_reception_package", "package"),
        2: (("F1", "F2", "F3", "covered_storage"), None, False, "feed_storage_package", "package"),
        3: (("F1", "F2", "F3", "mechanical_preparation"), None, True, "feed_preparation_package", "package"),
        4: (("F1", "F2", "F3", "raw_press"), None, True, "raw_press_package", "package"),
        5: (("F2", "F3", "pef"), "pretreatment_method", True, "pef_package", "package"),
        6: (("ultrasound",), "pretreatment_method", True, "ultrasound_package", "package"),
        7: (("thermal_enzymatic",), "pretreatment_method", True, "thermal_enzymatic_package", "package"),
        8: (("PR1", "PR3", "isoelectric"), "protein_extraction_method", True, "precipitation_package", "package"),
        9: (("PR1", "PR2", "PR3", "isoelectric", "heat", "lactic_acid"), None, True, "protein_separator_package", "package"),
        10: (("PR6", "membrane_protein"), "protein_extraction_method", True, "protein_membrane_package", "package"),
        11: (("spray_drying", "spray_drying_proxy"), "protein_drying_method", True, "protein_dryer", "package"),
        12: (("freeze_drying", "freeze_drying_proxy"), "protein_drying_method", True, "protein_dryer", "package"),
        13: (("AD1", "AD2", "AD3", "AD4", "AD5", "bmp_material_conversion_proxy", "ad_plant_total"), "ad_capex_basis", True, "ad_plant_scope", "package"),
        14: (("ad_bottom_up",), "ad_capex_basis", False, "ad_plant_scope", "subcomponent"),
        15: (("BG1", "BG2", "BG3", "BG4", "BG5", "BG6", "common_conditioning"), None, True, "gas_conditioning_package", "package"),
        16: (("separate_gas_compression",), None, False, "biogas_upgrader_package", "subcomponent"),
        17: (("BG2", "BG3", "BG4", "water_scrubbing", "membrane_upgrading", "psa"), "biogas_upgrading_method", True, "biogas_upgrader_package", "package"),
        18: (("BG1", "chp", "chp_utilities"), "gas_product_route", True, "chp_package", "package"),
        19: (("NR1", "NR2", "NR3", "NR4", "NR5", "NR6", "NR7", "digestate_separation"), None, True, "digestate_separator_package", "package"),
        20: (("NR3", "NR4", "NR7", "ammonia_recovery"), "ammonia_recovery_method", True, "ammonia_recovery_package", "package"),
        21: (("NR6", "ion_exchange"), "ammonia_recovery_method", True, "ion_exchange_package", "package"),
        22: (("NR2", "NR4", "NR5", "NR7", "phosphorus_recovery"), None, True, "phosphorus_recovery_package", "package"),
        23: (("NR7", "potassium_water_concentration"), None, True, "water_concentration_package", "package"),
        24: (("boiler", "heat_pump", "external_heat"), "heat_supply_method", True, "heat_supply_package", "package"),
        25: (("cooling_required",), None, False, "cooling_package", "package"),
        26: (("site_buildings",), None, False, "site_development", "subcomponent"),
        27: (("land_purchase",), None, False, "site_development", "subcomponent"),
        28: (("engineering_epc",), None, False, "project_indirects", "package"),
        29: (("labor",), None, False, None, None),
        30: (("routine_maintenance",), "maintenance_basis", False, None, None),
        31: (("BG1", "chp", "chp_utilities"), "maintenance_basis", True, None, None),
        32: (("feedstock_logistics",), None, False, None, None),
        33: (("pit_storage",), None, False, None, None),
        34: (("wastewater_discharge",), None, False, None, None),
        35: (("residue_disposal",), None, False, None, None),
        36: (("electricity",), None, True, None, None),
        37: (("natural_gas",), "heat_utility_method", True, None, None),
        38: (("external_heat", "delivered_process_heat"), "heat_utility_method", True, None, None),
        39: (("process_water",), None, True, None, None),
        40: (("process_water", "tap_water_tax"), None, True, None, None),
        41: (("BG4", "psa"), None, False, None, None),
        42: (("water_balance_alias",), "water_price_basis", False, None, None),
        43: (("PR1", "PR3", "NR3", "NR4", "NR7", "acid_consumable"), None, True, None, None),
        44: (("thermal_enzymatic", "enzyme_consumable"), None, True, None, None),
        45: (("flocculant",), None, False, None, None),
        46: (("BG5", "mea", "mea_consumable"), None, True, None, None),
        47: (("BG2", "BG3", "BG4", "BG5", "gas_polishing"), None, True, None, None),
        48: (("BG4", "psa", "psa_adsorbent"), None, True, None, None),
        49: (("PR6", "BG3", "NR7", "membrane_replacement"), None, True, None, None),
        50: (("NR6", "ion_exchange", "ion_exchange_resin"), None, True, None, None),
        51: (("NR2", "NR4", "NR7", "phosphorus_recovery", "magnesium_reagent"), None, True, None, None),
        52: (("cip_chemicals",), None, False, None, None),
        53: (("F1", "F2", "F3", "mechanical_wear"), None, True, None, None),
    }
    return metadata[index]


def _capacity_anchor(index: int, value: float | None) -> tuple[float | None, str | None, float | None]:
    anchors: dict[int, tuple[float, str, float | None]] = {
        3: (1.0, "wet t/h", None),
        7: (5.0, "working volume m3", None),
        8: (5.0, "working volume m3", None),
        9: (2.0, "m3/h", None),
        11: (500.0, "kg water evaporated/h", None),
        12: (50.0, "kg water removed/batch", None),
        14: (1000.0, "working volume m3", None),
        15: (100.0, "Nm3/h raw gas", None),
        16: (100.0, "Nm3/h raw gas", None),
        18: (1121.0, "kW electric", 1121.0 * 2500.0),
        19: (2.0, "m3/h", None),
        20: (3.0, "m3/h digestate liquid", None),
        21: (5.0, "m3/h", None),
        22: (3.0, "m3/h", None),
        23: (5.0, "m3/h", None),
        24: (500.0, "kWth", None),
        25: (100.0, "kW cooling", None),
        26: (1.0, "m2 gross floor area", None),
        27: (1.0, "m2 plot", None),
    }
    return anchors.get(index, (None, None, None))


def _cost_type(category: str) -> str:
    return {
        "equipment": "capex",
        "installation": "capex",
        "indirect_cost": "indirect",
        "labor": "labor",
        "maintenance": "maintenance",
        "logistics": "logistics",
        "utility": "utility",
        "consumable": "consumable",
        "disposal": "disposal",
        "revenue": "revenue",
    }.get(category.strip().lower(), category.strip().lower())


def _validate_register(records: Iterable[TEACostRecord]) -> None:
    seen: set[str] = set()
    allowed = {"capex", "opex", "utility", "consumable", "labor", "maintenance", "logistics", "indirect", "disposal", "revenue"}
    for record in records:
        if not record.cost_id or record.cost_id in seen:
            raise ValueError(f"Duplicate or empty TEA cost_id: {record.cost_id!r}")
        if record.cost_type not in allowed:
            raise ValueError(f"Unsupported TEA cost_type '{record.cost_type}' for {record.cost_id}.")
        if record.reference_value_eur is not None and record.reference_value_eur < 0:
            raise ValueError(f"Negative cost value for {record.cost_id}.")
        seen.add(record.cost_id)


def _split_tags(value: object) -> tuple[str, ...]:
    return tuple(tag.strip() for tag in re.split(r"[|,;]", str(value or "")) if tag.strip())


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _parse_bool(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def _parse_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_int(value: object) -> int | None:
    parsed = _parse_float(value)
    return None if parsed is None else int(parsed)


def _csv_number(value: object) -> object:
    parsed = _parse_float(value)
    return "" if parsed is None else parsed


__all__ = (
    "DEFAULT_TEA_COST_REGISTER",
    "DEFAULT_TEA_WORKBOOK",
    "TEACostRecord",
    "load_tea_cost_register",
    "normalize_cost_register_workbook",
)
