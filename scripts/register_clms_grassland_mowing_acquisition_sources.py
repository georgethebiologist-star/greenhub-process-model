"""Register official Copernicus grassland mowing products as Phase 1 leads.

This script records source metadata only. It does not download, crop, or
interpret any GRAME/GRAMD raster pixels as roadside-grass harvest data.
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "Greenhub" / "data"
FOLDER = DATA / "Pre-treatment" / "Feedstock"
AUDIT = DATA / "global_audit_package"
RETRIEVED = "2026-11-08"

GRAME_ID = "SRC-CLMS-GRAME-GRASSLAND-MOWING-EVENTS"
GRAMD_ID = "SRC-CLMS-GRAMD-GRASSLAND-MOWING-DATES"
GRAME_DOI = "10.2909/114e8cae-1cd7-4adc-8c5f-a04863fc6af9"
GRAMD_DOI = "10.2909/660d00f1-c6de-4db6-9979-0be124ceb7f0"
PRODUCT_URL = "https://land.copernicus.eu/en/products/high-resolution-layer-grasslands?tab=grassland_mowing_events"
EEA_URL = "https://www.eea.europa.eu/en/datahub/datahubitem-view/69a59cd8-d22f-4b76-a672-867ce92e1855"
RELEASE_URL = "https://land.copernicus.eu/en/news/hrl-grasslands-releases-new-mowing-datasets"
WMS_CAPABILITIES_URL = "https://geoserver.vlcc.geoville.com/geoserver/ows?request=GetCapabilities&service=WMS&version=1.3.0"


def _read(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        return list(reader.fieldnames or []), list(reader)


def _write(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _upsert(path: Path, key: str, entries: list[dict[str, str]]) -> list[dict[str, str]]:
    fields, rows = _read(path)
    columns = key.split("|")
    indexed = {tuple(row.get(column, "") for column in columns): row for row in rows}
    for entry in entries:
        identity = tuple(entry.get(column, "") for column in columns)
        if identity in indexed:
            indexed[identity].update(entry)
        else:
            rows.append(entry)
            indexed[identity] = rows[-1]
    _write(path, fields or list(entries[0]), rows)
    return rows


def main() -> None:
    local_source_path = FOLDER / "source_register.csv"
    sources = [
        {
            "source_id": GRAME_ID,
            "source_title": "Grassland Mowing Events 2017–present (GRAME), Europe, yearly, 10 m",
            "authors": "Copernicus Land Monitoring Service; European Environment Agency; European Commission Joint Research Centre",
            "year": "2024",
            "source_type": "official satellite-derived annual land-cover event-classification product and metadata",
            "doi_or_stable_identifier": GRAME_DOI,
            "stable_url": f"https://doi.org/{GRAME_DOI}",
            "material": "Detected number of mowing events (1, 2, 3, or 4+) within mapped temporary/permanent herbaceous grassland across EEA38; 10 m annual raster product.",
            "quality_notes": (
                "Phase 1 acquisition lead only: no raster payload or pixel observations were downloaded into GreenHub. "
                "Product documentation describes annual 10 m pixels, 100 km tiles, a 0.25 ha minimum mapping unit, and a confidence layer. "
                "Official CLMS announcement confirms 2022–2023 mowing datasets were released on 2025-12-02; the EEA metadata record exposes older WMS layers, so exact available years/files must be checked at acquisition. "
                "Satellite detections are not roadside-specific, do not measure biomass/yield or material removal, and do not prove collection/access/contracts. "
                "The minimum mapping unit may omit narrow verge strips. License is full/open/free subject to Copernicus attribution and modification notice. Reference metadata only; not a model input."
            ),
            "accessed_date": RETRIEVED,
        },
        {
            "source_id": GRAMD_ID,
            "source_title": "Grassland Mowing Dates 2017–present (GRAMD), Europe, yearly, 10 m, four event layers",
            "authors": "Copernicus Land Monitoring Service; European Environment Agency; European Commission Joint Research Centre",
            "year": "2024",
            "source_type": "official satellite-derived annual land-cover event-date classification product and metadata",
            "doi_or_stable_identifier": GRAMD_DOI,
            "stable_url": f"https://doi.org/{GRAMD_DOI}",
            "material": "Day-of-year for up to four detected mowing events within mapped temporary/permanent herbaceous grassland across EEA38; four 10 m annual raster layers.",
            "quality_notes": (
                "Phase 1 acquisition lead only: no raster payload or pixel observations were downloaded into GreenHub. "
                "Product documentation describes annual 10 m pixels, 100 km tiles, a 0.25 ha minimum mapping unit, four event-date bands, and DOY values with product-specific no-detection/non-herbaceous flags. "
                "Official CLMS announcement confirms 2022–2023 mowing datasets were released on 2025-12-02; the EEA metadata record exposes older WMS layers, so exact available years/files must be checked at acquisition. "
                "Satellite detections are not roadside-specific, do not measure biomass/yield or material removal, and do not prove collection/access/contracts. "
                "The minimum mapping unit may omit narrow verge strips. License is full/open/free subject to Copernicus attribution and modification notice. Reference metadata only; not a model input."
            ),
            "accessed_date": RETRIEVED,
        },
    ]
    local_rows = _upsert(local_source_path, "source_id", sources)
    source_digest = hashlib.sha256(local_source_path.read_bytes()).hexdigest()
    source_fields, _ = _read(local_source_path)

    manifest_path = FOLDER / "dataset_manifest.csv"
    manifest_fields, manifest_rows = _read(manifest_path)
    manifest_index = {row.get("file_name", ""): row for row in manifest_rows}
    if "source_register.csv" in manifest_index:
        manifest_index["source_register.csv"].update({
            "description": "Local bibliographic/provenance register, including official Copernicus GRAME/GRAMD Phase 1 acquisition leads; no product raster payload is staged.",
            "row_count": str(len(local_rows)),
        })
        _write(manifest_path, manifest_fields, manifest_rows)
    manifest_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    relative_source = "Pre-treatment/Feedstock/source_register.csv"
    _upsert(AUDIT / "global_source_register.csv", "dataset_path|source_id", [
        {
            "dataset_path": relative_source,
            "dataset_group": "Pre-treatment/Feedstock",
            "source_id": item["source_id"],
            "source_title": item["source_title"],
            "authors": item["authors"],
            "year": item["year"],
            "doi_or_stable_id": item["doi_or_stable_identifier"],
            "url": item["stable_url"],
            "source_type": item["source_type"],
            "notes": item["quality_notes"],
        }
        for item in sources
    ])
    global_manifest_path = AUDIT / "global_dataset_manifest.csv"
    global_fields, global_rows = _read(global_manifest_path)
    global_index = {row.get("dataset_path", ""): row for row in global_rows}
    if relative_source in global_index:
        global_index[relative_source].update({
            "row_count_observed": str(len(local_rows)),
            "header_count": str(len(source_fields)),
            "headers": "; ".join(source_fields),
            "notes": "Bibliographic register includes GRAME/GRAMD official seasonal mowing product acquisition leads; no raster observations are staged or activated.",
        })
        _write(global_manifest_path, global_fields, global_rows)

    _upsert(AUDIT / "source_dataset_checksums.csv", "dataset_path", [
        {
            "dataset_path": relative_source,
            "sha256": source_digest,
            "byte_size": str(local_source_path.stat().st_size),
        },
        {
            "dataset_path": "Pre-treatment/Feedstock/dataset_manifest.csv",
            "sha256": manifest_digest,
            "byte_size": str(manifest_path.stat().st_size),
        },
    ])

    print(f"sources={len(sources)} local_register_rows={len(local_rows)} sha256={source_digest}")
    print(f"product={PRODUCT_URL}")
    print(f"eea_metadata={EEA_URL}")
    print(f"2022_2023_release={RELEASE_URL}")
    print(f"published_wms_capabilities={WMS_CAPABILITIES_URL}")


if __name__ == "__main__":
    main()
