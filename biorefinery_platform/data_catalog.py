"""Build a traceable reuse index for Phase 3–7 datasets and runtime inputs."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPOSITORY_ROOT / "Greenhub" / "data"
PLATFORM_DATA_ROOT = DATA_ROOT / "platform"
PHASE_FAMILY = {
    "3": "pretreatment_fractionation",
    "4": "protein_recovery",
    "5": "anaerobic_digestion",
    "6": "biogas_upgrading",
    "7": "npk_recovery",
}
PHASE_LABEL = {
    "3": "Pretreatment and fractionation",
    "4": "Protein recovery",
    "5": "Anaerobic digestion",
    "6": "Biogas upgrading",
    "7": "NPK recovery",
}
PHASE_DATA_CATEGORIES = {
    "Pre-treatment",
    "Protein recovery",
    "Bigas production + upgrade",
    "Resource recovery",
    "Centrifuge",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _dataset_status_values(data_root: Path, dataset_path: str) -> str:
    """Read explicit observation-status values, falling back to activation labels."""
    path = data_root / Path(_normal_path(dataset_path))
    if path.suffix.lower() != ".csv" or not path.is_file():
        return ""
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            fields = reader.fieldnames or []
            explicit_fields = [
                key for key in (
                    "result_status", "record_status", "observation_status",
                    "measurement_status", "data_status",
                ) if key in fields
            ]
            activation_field = "activation_state" if "activation_state" in fields else None
            values: list[str] = []
            activation_values: list[str] = []
            for row in reader:
                for key in explicit_fields:
                    value = str(row.get(key) or "").strip()
                    if value and value not in values:
                        values.append(value)
                if activation_field:
                    value = str(row.get(activation_field) or "").strip()
                    if value and value not in activation_values:
                        activation_values.append(value)
            if not values:
                values = activation_values
    except (OSError, UnicodeError, csv.Error):
        return ""
    return ";".join(values)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list, tuple)) else value
                for key, value in row.items()
            })


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normal_path(value: str) -> str:
    return value.replace("\\", "/").strip("/")


def _source_asset_id(path: str) -> str:
    digest = hashlib.sha256(_normal_path(path).casefold().encode("utf-8")).hexdigest()[:20]
    return f"urn:greenhub:data-asset:{digest}"


def _phase_family(category: str, subgroup: str) -> tuple[str, str, str, str]:
    """Return family ID, legacy phase, portability class, and transfer warning."""
    if category == "Pre-treatment":
        portability = "feedstock_specific" if subgroup == "Feedstock" else "technology_and_feedstock_specific"
        return "pretreatment_fractionation", "3", portability, "Validate feed composition, equipment configuration, scale, and operating conditions before transfer."
    if category == "Protein recovery":
        return "protein_recovery", "4", "technology_and_feedstock_specific", "Validate juice composition, protein partition, operating conditions, product grade, and recovery basis before transfer."
    if category == "Bigas production + upgrade":
        if subgroup in {"AD assay validation", "BMP measurement quality"}:
            phase = "5"
            family = "anaerobic_digestion"
            scope = "technology_specific"
            warning = "This asset describes biochemical-methane-potential assay quality, not substrate methane yield or full-scale digester performance."
        elif subgroup in {"AD kinetics", "AD reactor", "Feed BMP"}:
            phase = "5"
            family = "anaerobic_digestion"
            scope = "substrate_and_operating_condition_specific"
            warning = "Substrate, inoculum, temperature, loading, retention time, and reactor configuration determine transferability."
        elif subgroup == "CHP_and_Utilities":
            phase = "cross-cutting"
            family = "crosscutting_utilities"
            scope = "equipment_and_site_specific"
            warning = "Equipment ratings may transfer within their envelope; site tariffs, grid factors, schedule, and ambient conditions do not."
        else:
            phase = "6"
            family = "biogas_upgrading"
            scope = "technology_and_feed_gas_specific"
            warning = "Validate inlet gas composition, scale, operating conditions, methane slip, utility duty, and consumables before transfer."
        return family, phase, scope, warning
    if category == "Resource recovery":
        return "npk_recovery", "7", "technology_and_digestate_specific", "Validate digestate speciation, concentration, contaminants, reagent basis, product grade, and local use conditions before transfer."
    if category == "Centrifuge":
        return "crosscutting_separation", "cross-cutting", "equipment_and_slurry_specific", "Validate slurry properties, particle distribution, throughput, and separation target; relevant to pretreatment and digestate recovery."
    raise ValueError(f"No Phase 3–7 family mapping for {category!r}/{subgroup!r}.")


def _source_links(dataset_path: str, source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    target = _normal_path(dataset_path).casefold()
    return [row for row in source_rows if _normal_path(row.get("dataset_path", "")).casefold() == target]


def _normalize_sidecar_source(
    source: dict[str, object],
    dataset_path: str,
    dataset_defaults: dict[str, object] | None = None,
) -> dict[str, object]:
    defaults = dataset_defaults or {}
    value = {**defaults, **source}
    related_identifiers = value.get("related_identifiers", [])
    if not isinstance(related_identifiers, list):
        related_identifiers = [related_identifiers]
    for key in (
        "persistent_identifier",
        "alternate_identifier",
        "doi_or_stable_id",
        "publication_doi",
        "related_article_doi",
        "article_doi",
        "dataset_doi",
        "dataset_identifier",
    ):
        identifier = value.get(key)
        if identifier:
            related_identifiers.append(identifier)
    related_identifiers = sorted({
        str(item.get("identifier", "")) if isinstance(item, dict) else str(item)
        for item in related_identifiers
        if (item.get("identifier") if isinstance(item, dict) else item)
    })
    authors = value.get("authors", "")
    if isinstance(authors, (list, tuple)):
        authors = "; ".join(str(author) for author in authors)
    related_families = value.get("related_technology_family_ids", [])
    if not isinstance(related_families, list):
        related_families = [related_families]
    return {
        "dataset_path": _normal_path(dataset_path),
        "source_id": str(value.get("source_id", "")),
        "source_title": str(value.get("source_title", value.get("dataset_title", value.get("title", "")))),
        "authors": str(authors),
        "year": str(value.get("reference_year", value.get("publication_year", value.get("year", "")))),
        "doi_or_stable_id": str(next((
            value.get(key) for key in (
                "persistent_identifier", "doi_or_stable_id", "publication_doi",
                "related_article_doi", "article_doi", "dataset_doi",
            ) if value.get(key)
        ), "")),
        "url": str(next((
            value.get(key) for key in ("source_url", "publication_url", "url", "author_manuscript_url")
            if value.get(key)
        ), "")),
        "source_type": str(value.get("source_type", value.get("evidence_class", ""))),
        "source_location": str(next((
            value.get(key) for key in ("source_location", "source_locator", "source_table")
            if value.get(key)
        ), "")),
        "license": str(value.get("license", value.get("source_license", value.get("reuse_license", "")))),
        "retrieval_date": str(value.get("retrieval_date", "")),
        "related_identifiers": json.dumps(related_identifiers, ensure_ascii=False),
        "applicability": str(value.get("applicability", "")),
        "measurement_basis": str(value.get("measurement_basis", "")),
        "uncertainty": str(value.get("uncertainty", "")),
        "activation_state": str(value.get("activation_state", "")),
        "conversion_and_scaling": str(value.get("conversion_and_scaling", "")),
        "related_technology_family_ids": json.dumps(related_families, ensure_ascii=False),
        "notes": str(value.get("provenance_note", value.get("notes", ""))),
    }


def _sidecar_sources(data_root: Path, dataset_path: str) -> list[dict[str, object]]:
    dataset_file = data_root / Path(_normal_path(dataset_path))
    # Both spellings already exist in the repository: ``name.source.json``
    # and the older ``name.csv.source.json``. Prefer the normalized form.
    sidecar_candidates = (
        dataset_file.with_suffix(".source.json"),
        dataset_file.with_name(dataset_file.name + ".source.json"),
    )
    sidecar_path = next((candidate for candidate in sidecar_candidates if candidate.exists()), None)
    if sidecar_path is None:
        return []
    try:
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(sidecar, dict):
        return []
    raw_sources = sidecar.get("source_records")
    if isinstance(raw_sources, list):
        return [
            _normalize_sidecar_source(source, dataset_path, sidecar)
            for source in raw_sources
            if isinstance(source, dict)
        ]
    source = _normalize_sidecar_source(sidecar, dataset_path)
    return [source] if any(str(source.get(key, "")).strip() for key in ("source_id", "source_title", "doi_or_stable_id", "url")) else []


def _data_scope(portability_class: str, context_independent: bool = False) -> str:
    """Give cross-project users a conservative, reviewable reuse scope."""
    if context_independent:
        return "context_independent"
    normalized = portability_class.strip().casefold().replace("-", "_").replace(" ", "_")
    if any(term in normalized for term in ("feedstock", "substrate", "digestate", "slurry", "material", "feed_gas")):
        if any(term in normalized for term in ("technology", "equipment", "operating_condition", "test_condition")):
            return "technology_and_material_specific"
        return "material_or_site_specific"
    if "site" in normalized:
        if "technology" in normalized or "equipment" in normalized:
            return "technology_and_material_specific"
        return "material_or_site_specific"
    if "technology" in normalized or "equipment" in normalized:
        return "technology_specific"
    return "context_specific_unclassified"


def build_dataset_reuse_catalog(
    data_root: Path = DATA_ROOT,
) -> list[dict[str, object]]:
    manifest = _read_csv(data_root / "global_audit_package" / "global_dataset_manifest.csv")
    sources = _read_csv(data_root / "global_audit_package" / "global_source_register.csv")
    records: list[dict[str, object]] = []
    for item in manifest:
        category = item.get("category", "")
        if category not in PHASE_DATA_CATEGORIES:
            continue
        subgroup = item.get("subgroup", "")
        family, phase, portability, warning = _phase_family(category, subgroup)
        linked_sources = _source_links(item.get("dataset_path", ""), sources)
        sidecar_sources = _sidecar_sources(data_root, item.get("dataset_path", ""))
        if sidecar_sources:
            if linked_sources:
                if len(sidecar_sources) == 1:
                    # Preserve the historical behavior for single-source sidecars:
                    # they fill metadata on every row linked to the data asset.
                    sidecar_source = sidecar_sources[0]
                    linked_sources = [
                        {**sidecar_source, **{key: value for key, value in row.items() if str(value).strip()}}
                        for row in linked_sources
                    ]
                else:
                    linked_source_indexes: set[int] = set()
                    enriched_sources: list[dict[str, object]] = []
                    for sidecar_source in sidecar_sources:
                        sidecar_id = str(sidecar_source.get("source_id", "")).strip().casefold()
                        sidecar_doi = str(sidecar_source.get("doi_or_stable_id", "")).strip().casefold()
                        matches = [
                            (index, row)
                            for index, row in enumerate(linked_sources)
                            if (sidecar_id and sidecar_id == str(row.get("source_id", "")).strip().casefold())
                            or (sidecar_doi and sidecar_doi == str(row.get("doi_or_stable_id", "")).strip().casefold())
                        ]
                        if matches:
                            for index, row in matches:
                                enriched_sources.append({
                                    **sidecar_source,
                                    **{key: value for key, value in row.items() if str(value).strip()},
                                })
                                linked_source_indexes.add(index)
                        else:
                            enriched_sources.append(sidecar_source)
                    enriched_sources.extend(
                        row for index, row in enumerate(linked_sources)
                        if index not in linked_source_indexes
                    )
                    linked_sources = enriched_sources
            else:
                linked_sources = sidecar_sources
        source_ids = sorted({row.get("source_id", "") for row in linked_sources if row.get("source_id")})
        identifiers: set[str] = {
            row.get("doi_or_stable_id", "")
            for row in linked_sources
            if row.get("doi_or_stable_id")
        }
        for row in linked_sources:
            raw_identifiers = row.get("related_identifiers", "")
            try:
                parsed_identifiers = json.loads(raw_identifiers) if raw_identifiers else []
            except json.JSONDecodeError:
                parsed_identifiers = [raw_identifiers]
            if isinstance(parsed_identifiers, list):
                identifiers.update(str(value) for value in parsed_identifiers if str(value).strip())
        dois = sorted(identifiers)
        metadata_gaps = {
            gap
            for row in linked_sources
            for key, gap in (
                ("doi_or_stable_id", "DOI or stable identifier"),
                ("url", "direct source URL"),
                ("year", "reference year"),
                ("source_location", "table/page/section locator"),
                ("license", "reuse license"),
                ("retrieval_date", "retrieval date"),
            )
            if not str(row.get(key, "")).strip()
        }
        if not linked_sources:
            metadata_gaps.add("linked source record")
        sidecar_statuses = sorted({
            row.get("activation_state", "").strip()
            for row in linked_sources
            if row.get("activation_state", "").strip()
        })
        manifest_status = item.get("standardized_status_values", "").strip()
        observed_statuses = _dataset_status_values(data_root, item.get("dataset_path", ""))
        data_status = manifest_status or observed_statuses or "; ".join(sidecar_statuses)
        related_families: set[str] = set()
        for row in linked_sources:
            raw_families = row.get("related_technology_family_ids", "")
            try:
                parsed_families = json.loads(raw_families) if raw_families else []
            except json.JSONDecodeError:
                parsed_families = [part.strip() for part in raw_families.split(";") if part.strip()]
            if isinstance(parsed_families, list):
                related_families.update(str(value) for value in parsed_families if str(value).strip())
        related_families.discard(family)
        records.append({
            "schema_version": "1.0.0",
            "data_asset_id": _source_asset_id(item.get("dataset_path", "")),
            "data_asset_id_status": "deterministic repository-local identifier; not publicly resolver-registered",
            "dataset_path": _normal_path(item.get("dataset_path", "")),
            "source_category": category,
            "technology_subgroup": subgroup,
            "filename": item.get("filename", ""),
            "technology_family_id": family,
            "technology_family_label": PHASE_LABEL.get(phase, "Cross-cutting separation or utility"),
            "technology_family_ids": sorted({family, *related_families}),
            "related_technology_family_ids": sorted(related_families),
            "legacy_phase": f"Phase {phase}" if phase in PHASE_FAMILY else "Cross-cutting",
            "project_id": "greenhub",
            "current_context": "GreenHub roadside-grass biorefinery; source-study context is retained in each linked record",
            "portability_class": portability,
            "data_scope_class": _data_scope(portability),
            "context_independent": False,
            "portability_review_status": "rule_inferred_review_required",
            "transferability_warning": warning,
            "row_count_observed": item.get("row_count_observed", ""),
            "detected_readiness": item.get("detected_readiness", ""),
            "data_status_values": data_status,
            "linked_source_count": len(linked_sources),
            "source_ids": source_ids,
            "source_titles": sorted({row.get("source_title", "") for row in linked_sources if row.get("source_title")}),
            "source_dois_or_stable_ids": dois,
            "source_urls": sorted({row.get("url", "") for row in linked_sources if row.get("url")}),
            "source_locations": sorted({row.get("source_location", "") for row in linked_sources if row.get("source_location")}),
            "source_licenses": sorted({row.get("license", "") for row in linked_sources if row.get("license")}),
            "source_retrieval_dates": sorted({row.get("retrieval_date", "") for row in linked_sources if row.get("retrieval_date")}),
            "source_types": sorted({row.get("source_type", "") for row in linked_sources if row.get("source_type")}),
            "source_notes": sorted({row.get("notes", "") for row in linked_sources if row.get("notes")}),
            "evidence_class": sorted({row.get("source_type", "") for row in linked_sources if row.get("source_type")}) or ["unclassified"],
            "activation_state": sidecar_statuses[0] if len(sidecar_statuses) == 1 else "mixed" if sidecar_statuses else "unclassified",
            "unit": None,
            "basis": None,
            "uncertainty": None,
            "applicability": sorted({row.get("applicability", "") for row in linked_sources if row.get("applicability")}),
            "conversion_and_scaling": sorted({row.get("conversion_and_scaling", "") for row in linked_sources if row.get("conversion_and_scaling")}),
            "provenance": [
                {
                    "source_id": row.get("source_id") or None,
                    "source_title": row.get("source_title") or None,
                    "authors": row.get("authors") or None,
                    "reference_year": row.get("year") or None,
                    "doi_or_stable_id": row.get("doi_or_stable_id") or None,
                    "related_identifiers": json.loads(row.get("related_identifiers", "[]")) if isinstance(row.get("related_identifiers", "[]"), str) else row.get("related_identifiers", []),
                    "source_url": row.get("url") or None,
                    "source_location": row.get("source_location") or None,
                    "retrieval_date": row.get("retrieval_date") or None,
                    "license": row.get("license") or None,
                    "evidence_class": row.get("source_type") or None,
                    "uncertainty": row.get("uncertainty") or None,
                    "measurement_basis": row.get("measurement_basis") or None,
                    "conversion_and_scaling": row.get("conversion_and_scaling") or None,
                    "applicability": row.get("applicability") or None,
                }
                for row in linked_sources
            ],
            "metadata_gaps": sorted(metadata_gaps),
            "source_metadata_gaps": sorted(metadata_gaps),
            "mapping_basis": "Global dataset manifest category/subgroup plus linked source-register records; no parameter values are promoted by this index.",
        })
    return sorted(records, key=lambda row: (str(row["technology_family_id"]), str(row["dataset_path"])))


def _input_phase(record_id: str) -> str | None:
    match = re.match(r"^phase([3-7])\.", record_id)
    return match.group(1) if match else None


def _metadata(value: str) -> dict[str, object]:
    try:
        parsed = json.loads(value or "{}")
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _input_portability(phase: str, original_class: str, metadata: dict[str, object]) -> tuple[str, str]:
    if original_class.strip():
        normalized = original_class.strip().casefold().replace("-", "_").replace(" ", "_")
        return normalized, "preserved_from_canonical_parameter_metadata"
    if phase == "5":
        return "substrate_and_operating_condition_specific", "inferred_from_process_family"
    if phase == "6":
        return "technology_and_feed_gas_specific", "inferred_from_process_family"
    if phase == "7":
        return "technology_and_digestate_specific", "inferred_from_process_family"
    if phase == "4":
        return "technology_and_feedstock_specific", "inferred_from_process_family"
    return "feedstock_or_technology_specific", "inferred_from_process_family"


def build_runtime_input_reuse_catalog(data_root: Path = DATA_ROOT) -> list[dict[str, object]]:
    source_rows = _read_csv(data_root / "fair_input_catalog" / "master_input_records.csv")
    records: list[dict[str, object]] = []
    for source in source_rows:
        phase = _input_phase(source.get("record_id", ""))
        if phase is None:
            continue
        metadata = _metadata(source.get("additional_metadata_json", ""))
        family = PHASE_FAMILY[phase]
        portability, assessment = _input_portability(
            phase, str(metadata.get("transferability_class", "")), metadata
        )
        record = dict(source)
        record.update({
            "technology_family_id": family,
            "technology_family_label": PHASE_LABEL[phase],
            "legacy_phase": f"Phase {phase}",
            "project_id": "greenhub",
            "portability_class": portability,
            "data_scope_class": _data_scope(portability, portability in {"context_independent", "context_independent_equation"}),
            "portability_assessment": assessment,
            "context_independent": portability in {"context_independent", "context_independent_equation"},
            "portability_review_required": True,
            "parameter_transfer_warning": "Do not reuse a value outside its recorded basis/applicability; this export does not activate or promote the parameter.",
        })
        records.append(record)
    return sorted(records, key=lambda row: str(row["record_id"]))


def _quality_counts(records: list[dict[str, object]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for row in records:
        phase_match = re.match(r"^Phase ([3-7])$", str(row.get("legacy_phase", "")))
        if not phase_match:
            continue
        phase = phase_match.group(1)
        quality = str(row.get("quality_class", "missing")).strip() or "missing"
        counts.setdefault(phase, {})[quality] = counts.setdefault(phase, {}).get(quality, 0) + 1
    return {phase: dict(sorted(values.items())) for phase, values in sorted(counts.items())}


def build_catalog_bundle(data_root: Path = DATA_ROOT) -> dict[str, object]:
    datasets = build_dataset_reuse_catalog(data_root)
    inputs = build_runtime_input_reuse_catalog(data_root)
    return {
        "schema_version": "1.0.0",
        "catalog_id": "greenhub:phase-3-7-reuse-index:1",
        "identifier_status": "Stable repository-local catalog identifier; no public DOI or resolver registration is claimed.",
        "data_sources": [
            "Greenhub/data/global_audit_package/global_dataset_manifest.csv",
            "Greenhub/data/global_audit_package/global_source_register.csv",
            "Greenhub/data/fair_input_catalog/master_input_records.csv",
        ],
        "counts": {
            "technology_dataset_assets": len(datasets),
            "canonical_phase_3_to_7_input_records": len(inputs),
            "phase_3_to_7_inputs_by_phase": {
                phase: sum(1 for row in inputs if row["legacy_phase"] == f"Phase {phase}")
                for phase in PHASE_FAMILY
            },
            "runtime_inputs_quality_by_phase": _quality_counts(inputs),
            "dataset_assets_without_linked_source": sum(1 for row in datasets if not row["linked_source_count"]),
            "dataset_assets_without_doi_or_stable_id": sum(1 for row in datasets if not row["source_dois_or_stable_ids"]),
            "dataset_assets_missing_source_metadata": sum(1 for row in datasets if row["source_metadata_gaps"]),
            "context_independent_empirical_assets": sum(1 for row in datasets if row["context_independent"]),
            "d4_promotions": 0,
        },
        "maturity_note": "This is a discoverability and transferability crosswalk. It neither fills missing measurements nor promotes staged datasets to calculation-ready status.",
        "datasets": datasets,
        "runtime_inputs": inputs,
    }


def write_catalog_bundle(data_root: Path = DATA_ROOT) -> dict[str, object]:
    bundle = build_catalog_bundle(data_root)
    output_root = data_root / "platform" / "catalogs"
    _write_csv(output_root / "phase_3_7_dataset_reuse_catalog.csv", bundle["datasets"])
    _write_csv(output_root / "phase_3_7_runtime_input_reuse_catalog.csv", bundle["runtime_inputs"])
    _write_json(output_root / "phase_3_7_dataset_reuse_catalog.json", bundle["datasets"])
    _write_json(output_root / "phase_3_7_runtime_input_reuse_catalog.json", bundle["runtime_inputs"])
    manifest = {key: value for key, value in bundle.items() if key not in {"datasets", "runtime_inputs"}}
    _write_json(output_root / "catalog_manifest.json", manifest)
    return manifest
