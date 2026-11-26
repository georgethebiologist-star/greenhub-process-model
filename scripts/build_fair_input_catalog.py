"""Build a searchable FAIR-oriented index of GreenHub input assets.

The catalog indexes authoritative files; it does not store replacement parameter
values. Regenerate after changing input assets with:
    .venv/Scripts/python.exe scripts/build_fair_input_catalog.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import os
import re
from copy import copy
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'Greenhub' / 'data'
MASTER_WORKBOOK = DATA / 'greenhub_feed_inputs.xlsx'
OUT = DATA / 'fair_input_catalog'
CSV_OUT = OUT / 'master_input_catalog.csv'
JSON_OUT = OUT / 'master_input_catalog.json'
INPUTS_CSV = OUT / 'master_input_records.csv'
INPUTS_JSON = OUT / 'master_input_records.json'
SCHEMA_VERSION = '1.0.0'
DOI_PATTERN = re.compile(r'10\.\d{4,9}/[^\s;,]+', re.IGNORECASE)


def extract_dois(value: str) -> list[str]:
    """Extract DOI IDs, removing common landing-page suffixes like /full."""
    normalized = set()
    for match in DOI_PATTERN.findall(value or ''):
        doi = match.rstrip('.,')
        for opener, closer in (('(', ')'), ('[', ']'), ('{', '}')):
            while doi.endswith(closer) and doi.count(closer) > doi.count(opener):
                doi = doi[:-1]
        doi = re.sub(r'/(?:full|pdf)$', '', doi, flags=re.IGNORECASE)
        normalized.add(doi)
    return sorted(normalized)


def _pareto_reports_zeeland_monthly_supply() -> set[str]:
    """Return only supply records represented in a saved selectable monthly profile."""
    path = ROOT / 'Greenhub' / 'results' / 'pareto_rvo_2026' / 'latest_ui.json'
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return set()
    reported = set()
    for group in (payload.get('groups_payload') or {}).values():
        for candidate in group.get('scenario_catalog') or []:
            request = ((candidate.get('configuration') or {}).get('simulation') or {})
            schedule = request.get('biomass_schedule') or {}
            monthly = schedule.get('monthly_availability_tonnes')
            total = schedule.get('annual_available_biomass_tonnes')
            if (schedule.get('availability_source_id') == 'SRC-MOOV-VITO-2021'
                    and isinstance(monthly, list) and len(monthly) == 12
                    and total is not None
                    and abs(sum(float(value) for value in monthly) - float(total)) < 1e-6):
                if abs(float(total) - 42300.0) < 1e-6:
                    reported.update({'ZL-TWO-CUT-SUMMER', 'ZL-TWO-CUT-AUTUMN', 'ZL-TWO-CUT-TOTAL'})
                elif abs(float(total) - 25300.0) < 1e-6:
                    reported.add('ZL-ONE-CUT-POTENTIAL')
    return reported


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def role_for(path: Path) -> tuple[str, str, str]:
    rel = path.relative_to(DATA).as_posix().lower()
    if re.fullmatch(r'greenhub_feed_inputs_phase[1-6]_backup\.xlsx', path.name.lower()):
        return ('archived_workbook_backup', 'Historical workbook snapshot retained for audit/compatibility; not an active input or runtime default.', 'legacy workbook sheets; see the active master workbook for current inputs')
    if rel.endswith('greenhub_feed_composition_defaults.json'):
        return ('feed_composition_profile', 'Shared backend and frontend feed-composition baseline.', 'wet mass fraction; source class is recorded per component')
    if rel.endswith('weather/knmi_rotterdam_344_2021_2025.json'):
        return ('weather_input_observations', 'Official station observations; five-year monthly means provide the seasonal digester-ambient proxy unless the user overrides it.', 'source 0.1 degC; derived degC; month and station explicit')
    if rel.endswith('frontend/preview_parameter_defaults.json'):
        return ('frontend_preview_parameters', 'Read-only planning references for the bundled offline preview; not backend inputs.', 'parameter-specific unit; preview-only values and provenance are recorded per row')
    if 'kurhan_2025_biorefinery_reference' in rel and path.name.lower().endswith('.source.json'):
        return ('source_workbook_metadata', 'Provenance sidecar for an archived primary research workbook; not an input parameter file.', 'see source workbook and adjacent sheet inventory')
    if 'kurhan_2025_biorefinery_reference' in rel and path.name.lower().endswith('.xlsx'):
        return ('reference_source_workbook', 'Original open research workbook preserved unchanged; evidence only, not the active master workbook or a runtime input.', 'sheet-specific; consult associated article and companion sheet inventory for bases and interpretation')
    if 'kurhan_2025_biorefinery_reference' in rel and 'sheet_inventory' in path.name.lower():
        return ('source_workbook_inventory', 'Structural inventory of source workbook sheets and formula/cache counts; not experimental observations or runtime inputs.', 'sheet dimensions and counts; see original source workbook for values and units')
    if 'kurhan_2025_biorefinery_reference' in rel and 'source_workbook_cells' in path.name.lower():
        return ('reference_cell_level_source_extract', 'Cell-addressed transcription of source workbook contents; formulas and cached outputs are separate, and no values are runtime inputs.', 'source workbook, sheet, cell address; no unit or experimental meaning is inferred at cell level')
    if 'duczkowska_2026' in rel and path.name.lower().endswith('.source.json'):
        return ('source_metadata', 'Provenance sidecar for a published Polish roadside-biomass planning comparator; not a GreenHub input.', 'see article Table 2 or cited capacity-allocation figure')
    if 'duczkowska_2026' in rel and path.name.lower().endswith('.csv'):
        return ('spatial_supply_scenario_reference', 'Published Polish roadside-biomass and capacity-allocation scenarios; external comparator only, not Dutch supply or a runtime input.', 'reported unit, municipality/scenario, and cited article table/figure')
    if 'road_verge_standing_biomass_bakker_2026_source' in rel and path.name.lower().endswith('.source.json'):
        return ('source_metadata', 'FAIR metadata and checksum sidecar for an exact Zenodo dataset asset; not a model input.', 'Zenodo version DOI, source asset, and asset checksum')
    if 'road_verge_standing_biomass_bakker_2026_source' in rel and path.name.lower() == 'biomass.csv':
        return ('reference_source_data', 'Exact, byte-verifiable Zenodo roadside-biomass source CSV; measurement evidence only, not harvested supply or a runtime input.', 'source row and field; units are clarified by the companion article and analysis script')
    if 'road_verge_standing_biomass_bakker_2026_source' in rel and path.name.lower() == 'analysis.r':
        return ('reference_analysis_script', 'Original authors’ analysis code preserved for unit-conversion and methods provenance; not executed by GreenHub.', 'source code line; consult article methods and exact data CSV')
    if rel.endswith('.xlsx'):
        return ('master_input_workbook', 'Named-sheet input workbook; sheet names and existing precedence remain authoritative.', 'sheet-specific; see workbook metadata and units')
    if 'parameter_registry' in rel or 'activation_registry' in rel:
        return ('parameter_registry', 'Canonical registry/index; parameters are resolved through the registry service.', 'parameter-specific canonical unit and basis')
    if '/tea/' in rel or '/tea' in rel:
        return ('tea_input_or_evidence', 'TEA cost, price, finance, and provenance evidence; only explicitly activated entries affect calculations.', 'record-specific; see column metadata')
    if '/lca/' in rel:
        return ('lca_input_or_evidence', 'LCA inventory/factor input or supporting evidence; activation and boundary are configuration-dependent.', 'record-specific; see factor unit and basis')
    if '/storage/' in rel:
        return ('storage_input_or_evidence', 'Storage kinetics, conditions, or source evidence; check activation/readiness fields.', 'record-specific; commonly kg, day, °C, or fraction')
    if '/global_audit_package/' in rel:
        return ('provenance_or_audit', 'Source, dataset, issue, or maturity register; audit outputs are not automatically calculation inputs.', 'field-specific')
    if rel.endswith('.csv'):
        return ('process_input_or_evidence', 'Process data, parameters, evidence, or staged candidates; activation/readiness is explicit in the source file.', 'record-specific; inspect unit and basis columns')
    if rel.endswith(('.json', '.yaml', '.yml')):
        return ('configuration_or_metadata', 'Configuration or data package; runtime use depends on the consuming module.', 'field-specific')
    return ('supporting_asset', 'Supporting source asset; not presumed calculation-active.', 'not inferred')


def embedded_sources(path: Path) -> tuple[list[str], list[str]]:
    urls: set[str] = set()
    dois: set[str] = set()

    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                lowered = str(key).lower()
                if isinstance(item, str) and ('url' in lowered or 'doi' in lowered or lowered in {'href', 'stable_identifier'}):
                    urls.update(re.findall(r'https?://[^\s;|]+', item))
                    dois.update(extract_dois(item))
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
        elif isinstance(value, str):
            dois.update(extract_dois(value))

    try:
        if path.suffix.lower() == '.json':
            visit(json.loads(path.read_text(encoding='utf-8-sig')))
        elif path.suffix.lower() == '.csv':
            with path.open(encoding='utf-8-sig', newline='') as handle:
                for row in csv.DictReader(handle):
                    for key, value in row.items():
                        if value and (key and any(token in key.lower() for token in ('url', 'doi', 'stable_identifier', 'source'))):
                            urls.update(re.findall(r'https?://[^\s;|]+', value))
                            dois.update(extract_dois(value))
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error):
        pass
    return sorted(urls), sorted(dois)


def asset_activation_state(path: Path, local_record: dict[str, str]) -> str:
    """Return an explicit activation label without treating maturity as activation."""
    for key in ("activation_state", "activation"):
        value = str(local_record.get(key) or "").strip()
        if value:
            return value
    if path.suffix.lower() == ".csv":
        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if "activation_state" in (reader.fieldnames or []):
                    states = {str(row.get("activation_state") or "").strip()
                              for row in reader if str(row.get("activation_state") or "").strip()}
                    if len(states) == 1:
                        return next(iter(states))
                    if len(states) > 1:
                        return "mixed"
        except (OSError, UnicodeError, csv.Error):
            pass
    return ""


def embedded_source_ids(path: Path) -> set[str]:
    """Return source IDs explicitly attached to an asset, where present."""
    found: set[str] = set()

    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).lower() in {'source_id', 'source_ids'}:
                    values = item if isinstance(item, list) else str(item or '').split(';')
                    found.update(str(value).strip() for value in values if str(value).strip())
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    try:
        if path.suffix.lower() == '.json':
            visit(json.loads(path.read_text(encoding='utf-8-sig')))
        elif path.suffix.lower() == '.csv':
            with path.open(encoding='utf-8-sig', newline='') as handle:
                for row in csv.DictReader(handle):
                    found.update(value.strip() for value in (row.get('source_id') or '').split(';') if value.strip())
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error):
        pass
    return found


def main() -> None:
    source_register = read_rows(DATA / 'global_audit_package' / 'global_source_register.csv')
    manifest = read_rows(DATA / 'global_audit_package' / 'global_dataset_manifest.csv')
    sources_by_path: dict[str, list[dict[str, str]]] = {}
    sources_by_global_id: dict[str, list[dict[str, str]]] = {}
    for row in source_register:
        key = (row.get('dataset_path') or '').replace('\\', '/').strip()
        if key:
            sources_by_path.setdefault(key.lower(), []).append(row)
        source_id = str(row.get('source_id') or '').strip()
        if source_id:
            sources_by_global_id.setdefault(source_id, []).append(row)
    sources_by_dir: dict[str, list[dict[str, str]]] = {}
    source_file_by_dir: dict[str, str] = {}
    for register_path in DATA.rglob('source_register.csv'):
        if register_path == DATA / 'global_audit_package' / 'global_source_register.csv':
            continue
        key = register_path.parent.relative_to(DATA).as_posix().lower()
        sources_by_dir[key] = read_rows(register_path)
        source_file_by_dir[key] = register_path.relative_to(DATA).as_posix()
    manifest_by_path = {(row.get('dataset_path') or '').replace('\\', '/').lower(): row for row in manifest}
    local_manifest_by_asset: dict[tuple[str, str], dict[str, str]] = {}
    for local_manifest_path in DATA.rglob('dataset_manifest.csv'):
        if local_manifest_path.parent == DATA / 'global_audit_package':
            continue
        parent_key = local_manifest_path.parent.relative_to(DATA).as_posix().lower()
        for row in read_rows(local_manifest_path):
            filename = (row.get('filename') or row.get('file_name') or '').strip().lower()
            if filename:
                local_manifest_by_asset[(parent_key, filename)] = row
    local_records_by_source = {}
    for record_path in DATA.rglob('*.json'):
        try:
            record = json.loads(record_path.read_text(encoding='utf-8-sig'))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if isinstance(record, dict):
            source_reference = (
                record.get('source_file')
                or record.get('source_asset_path')
                or record.get('source_asset')
            )
            if not source_reference:
                continue
            reference_path = Path(str(source_reference))
            candidates = []
            if reference_path.is_absolute():
                candidates.append(reference_path)
            else:
                normalized_reference = reference_path.as_posix()
                if normalized_reference.startswith('Greenhub/data/'):
                    candidates.append(ROOT / reference_path)
                elif normalized_reference.startswith('Pre-treatment/') or normalized_reference.startswith('Bigas production + upgrade/'):
                    candidates.append(DATA / reference_path)
                candidates.extend((record_path.parent / reference_path, DATA / reference_path))
            source_path = next((candidate.resolve() for candidate in candidates if candidate.exists()), None)
            if source_path is None:
                continue
            try:
                source_key = source_path.relative_to(DATA.resolve()).as_posix().lower()
            except ValueError:
                continue
            local_records_by_source[source_key] = (record_path, record)

    rows = []
    for path in sorted((p for p in DATA.rglob('*') if p.is_file()), key=lambda p: p.relative_to(DATA).as_posix().casefold()):
        rel = path.relative_to(DATA).as_posix()
        if rel.startswith('fair_input_catalog/') or path.name.endswith(('.pyc', '.tmp')) or path.name.startswith('~$'):
            continue
        # The catalog snapshot is embedded in this workbook, so hashing the
        # workbook inside that snapshot creates an unavoidable self-hash cycle.
        # Its underlying datasets and normalized input records remain indexed.
        if path.resolve() == MASTER_WORKBOOK.resolve():
            continue
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        role, usage, unit_basis = role_for(path)
        local_record_pair = local_records_by_source.get(rel.lower())
        local_record = local_record_pair[1] if local_record_pair else {}
        local_source_id = str(local_record.get('source_id') or '').strip()
        explicit_source_ids = embedded_source_ids(path)
        embedded_urls, embedded_dois = embedded_sources(path)
        declared_source_ids = ({local_source_id} if local_source_id else set()) | explicit_source_ids
        exact_candidates = sources_by_path.get(rel.lower(), [])
        parent_key = path.parent.relative_to(DATA).as_posix().lower()
        if exact_candidates:
            candidates = list(exact_candidates)
            linkage = 'direct_dataset_path'
            source_file_names = ['global_audit_package/global_source_register.csv']
            # Global exact-path entries identify the asset, but can be sparse.
            # Enrich them from the asset's folder register only when the source
            # ID matches and any overlapping identity fields agree. This keeps
            # path-level provenance authoritative while retaining the fuller
            # local citation and stable URL.
            exact_by_id: dict[str, list[dict[str, str]]] = {}
            for source in exact_candidates:
                source_id = str(source.get('source_id') or '').strip()
                if source_id:
                    exact_by_id.setdefault(source_id, []).append(source)
            local_enrichment = []
            for source in sources_by_dir.get(parent_key, []):
                source_id = str(source.get('source_id') or '').strip()
                if source_id not in exact_by_id:
                    continue
                local_title = str(source.get('source_title') or '').strip().casefold()
                local_doi = str(source.get('doi_or_stable_id') or source.get('doi_or_stable_identifier') or '').strip().casefold()
                local_year = str(source.get('year') or '').strip()
                for exact in exact_by_id[source_id]:
                    exact_title = str(exact.get('source_title') or '').strip().casefold()
                    exact_doi = str(exact.get('doi_or_stable_id') or exact.get('doi_or_stable_identifier') or '').strip().casefold()
                    exact_year = str(exact.get('year') or '').strip()
                    identity_fields = ((local_title, exact_title), (local_doi, exact_doi), (local_year, exact_year))
                    if any(left and right and left != right for left, right in identity_fields):
                        continue
                    if any(left and right and left == right for left, right in identity_fields):
                        local_enrichment.append(source)
                        break
            if local_enrichment:
                candidates.extend(local_enrichment)
                local_register = source_file_by_dir[parent_key]
                if local_register not in source_file_names:
                    source_file_names.append(local_register)
        elif declared_source_ids:
            # A folder register describes a package, not each file inside it.
            # Join only source IDs declared by the asset or its sidecar.
            candidates = [source for source in sources_by_dir.get(parent_key, [])
                          if str(source.get('source_id') or '').strip() in declared_source_ids]
            linkage = 'declared_source_id_local_register' if candidates else 'not_found'
            source_file_names = [source_file_by_dir[parent_key]] if candidates else []
            if not candidates:
                # Source IDs can legitimately cross process-stage folders.
                # Resolve only a globally unambiguous study identity; generic
                # IDs such as SRC001 are reused by different packages.
                globally_resolved = []
                for source_id in sorted(declared_source_ids):
                    rows_for_id = sources_by_global_id.get(source_id, [])
                    identities = {(
                        row.get('source_title') or '',
                        row.get('doi_or_stable_id') or '',
                        row.get('year') or '',
                    ) for row in rows_for_id}
                    if len(identities) == 1:
                        globally_resolved.append(rows_for_id[0])
                if globally_resolved and len(globally_resolved) == len(declared_source_ids):
                    candidates = globally_resolved
                    linkage = 'declared_source_id_global_register'
                    source_file_names = ['global_audit_package/global_source_register.csv']
        elif embedded_dois and path.suffix.lower() in {'.csv', '.json'}:
            # A DOI printed in a data file provides a qualified cross-reference,
            # weaker than an exact dataset-path or source-ID registration.
            dois_in_asset = set(embedded_dois)
            candidates = [source for source in sources_by_dir.get(parent_key, [])
                          if dois_in_asset.intersection(extract_dois(' '.join((
                              source.get('doi_or_stable_id') or source.get('doi_or_stable_identifier') or '',
                              source.get('url') or source.get('stable_url') or '',
                          ))))]
            linkage = 'embedded_doi_local_register' if candidates else 'not_found'
            source_file_names = [source_file_by_dir[parent_key]] if candidates else []
        else:
            candidates = []
            linkage = 'not_found'
            source_file_names = []
        if declared_source_ids and candidates:
            # A conflicting explicit ID must not silently inherit another
            # source merely because a path or directory was registered.
            candidates = [source for source in candidates
                          if str(source.get('source_id') or '').strip() in declared_source_ids]
            if not candidates:
                linkage = 'not_found'
                source_file_names = []
        if local_record_pair:
            if not candidates:
                linkage = 'direct_local_source_record'
            source_file_names.append(local_record_pair[0].relative_to(DATA).as_posix())
            # Sidecars often carry the most precise dataset/version DOI and
            # retrieval URL. Include those links on the indexed data asset as
            # well as on the sidecar's own catalog row.
            local_urls, local_dois = embedded_sources(local_record_pair[0])
            embedded_urls = sorted(set(embedded_urls) | set(local_urls))
            embedded_dois = sorted(set(embedded_dois) | set(local_dois))
        unique = {}
        for source in candidates:
            identifier = (source.get('doi_or_stable_id') or source.get('doi_or_stable_identifier')
                          or source.get('persistent_identifier') or '')
            key = (source.get('source_id') or '', identifier)
            unique[key] = source
        source_ids = sorted(
            {s.get('source_id', '') for s in unique.values() if s.get('source_id')}
            | declared_source_ids
        )
        unresolved_declared_ids = declared_source_ids - {
            str(source.get('source_id') or '').strip() for source in candidates
        }
        dois = sorted({doi for s in unique.values()
                       for doi in extract_dois(s.get('doi_or_stable_id')
                                               or s.get('doi_or_stable_identifier')
                                               or s.get('persistent_identifier') or '')})
        urls = sorted({(s.get('url') or s.get('stable_url') or s.get('source_url') or '')
                       for s in unique.values()
                       if s.get('url') or s.get('stable_url') or s.get('source_url')})
        urls = sorted(set(urls) | set(embedded_urls))
        if local_record.get('source_url'):
            urls = sorted(set(urls) | {str(local_record['source_url'])})
        record_dois = {doi for field in ('dataset_id', 'persistent_identifier')
                       for doi in extract_dois(str(local_record.get(field) or ''))}
        dois = sorted(set(dois) | set(embedded_dois) | record_dois)
        man = manifest_by_path.get(rel.lower(), {})
        local_man = local_manifest_by_asset.get((path.parent.relative_to(DATA).as_posix().lower(), path.name.lower()), {})
        if not local_man:
            # Nested source packages often keep one authoritative manifest at their package root.
            # Walk upward from the asset directory and use the nearest manifest row for its filename.
            parent = path.parent
            while parent != DATA and not local_man:
                parent_key = parent.relative_to(DATA).as_posix().lower()
                local_man = local_manifest_by_asset.get((parent_key, path.name.lower()), {})
                parent = parent.parent
        local_readiness = (local_man.get('integration_readiness') or local_man.get('integration_status')
                           or local_man.get('readiness') or '')
        local_maturity = re.search(r"(?<![A-Za-z0-9])D[0-4](?![0-9])", local_readiness, flags=re.IGNORECASE)
        maturity = (local_maturity.group(0).upper() if local_maturity
                    else man.get('detected_readiness', ''))
        # Keep the established readiness label for compatibility, while exposing
        # maturity and activation as separate explicit catalog dimensions.
        readiness = ('reference_only' if 'reference_only' in local_readiness.lower()
                     else local_readiness or maturity)
        media_type = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        if path.suffix.lower() == '.csv':
            media_type = 'text/csv'
        elif path.suffix.lower() == '.xlsx':
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        activation_state = asset_activation_state(path, local_record)
        if local_record_pair:
            linkage = 'direct_local_source_record'
        rows.append({
            'dataset_id': f'urn:greenhub:dataset:sha256:{digest}',
            'title': path.stem.replace('_', ' ').replace('-', ' '),
            'relative_path': f'Greenhub/data/{rel}',
            'file_format': path.suffix.lstrip('.').lower() or 'unknown',
            'media_type': media_type,
            'file_size_bytes': len(content),
            'sha256': digest,
            'role': role,
            'runtime_usage_and_precedence': usage,
            'expected_unit_or_basis': unit_basis,
            'observed_rows': man.get('row_count_observed', ''),
            'readiness': readiness,
            'maturity': maturity,
            'activation_state': activation_state,
            'source_ids': ';'.join(source_ids),
            'source_dois': ';'.join(dois),
            'doi_urls': ';'.join(f'https://doi.org/{doi}' for doi in dois),
            'source_urls': ';'.join(urls),
            'source_register_paths': ';'.join(source_file_names),
            'source_metadata_linkage': linkage if candidates else 'not_found',
            'source_metadata_status': ('partially_linked_source_register' if candidates and unresolved_declared_ids
                                       else 'linked_to_source_register' if candidates
                                       else 'linked_to_local_source_record' if local_record_pair
                                       else 'inline_source_metadata_only' if embedded_urls or embedded_dois
                                       else 'file_metadata_only_source_link_not_found'),
            'license_or_rights': local_record.get('license') or 'Not inferred; retain source-specific rights and repository LICENSE terms.',
            'repository_access_url': f'https://github.com/georgethebiologist-star/greenhub-process-model/blob/main/Greenhub/data/{quote(rel, safe="/")}',
            'access_protocol': 'Machine-readable CSV/JSON or native source format; repository/HTTPS checkout. External source links are recorded separately.',
            'provenance': 'File content SHA-256; source links are joined to source registers or an explicit local source-record JSON where available.',
        })

    input_records = build_input_records()
    OUT.mkdir(parents=True, exist_ok=True)
    record_fields = list(input_records[0]) if input_records else []
    with INPUTS_CSV.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=record_fields)
        writer.writeheader()
        writer.writerows(input_records)
    INPUTS_JSON.write_text(json.dumps({
        'dataset_id': 'urn:greenhub:dataset:master-input-records:v1',
        'schema_version': SCHEMA_VERSION,
        'title': 'GreenHub normalized master input records (read-only generated snapshot)',
        'authority_note': 'Generated from authoritative source files for discovery and comparison. Do not feed this snapshot back into runtime; edit the authoritative file and regenerate.',
        'record_count': len(input_records),
        'records': input_records,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    fields = list(rows[0]) if rows else []
    with CSV_OUT.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        'catalog_id': 'urn:greenhub:catalog:master-inputs:v1',
        'title': 'GreenHub master input asset catalog',
        'schema_version': SCHEMA_VERSION,
        'generated_from': 'Greenhub/data/** source assets except the embedded master workbook (excluded to avoid self-hash recursion); source joins from global_audit_package registers',
        'authoritative_value_policy': 'This is an index, not an override layer. Runtime values remain in each authoritative input and are resolved by existing services and explicit UI overrides.',
        'override_precedence': 'Existing request/UI overrides and parameter-registry resolution remain authoritative; this catalog does not change precedence.',
        'identifier_policy': 'Each file version receives a content-addressed SHA-256 URN; it is unique but not a registered DOI. The repository URL is the access locator; archive releases to obtain externally persistent DOIs.',
        'normalized_master_input_records': {'csv': 'Greenhub/data/fair_input_catalog/master_input_records.csv', 'json': 'Greenhub/data/fair_input_catalog/master_input_records.json', 'record_count': len(input_records), 'authority_note': 'Generated read-only snapshot, not a runtime override layer.'},
        'counts': {'assets': len(rows), 'master_input_records': len(input_records), 'source_linked_assets': sum(r['source_metadata_status'] in {'linked_to_source_register','linked_to_local_source_record'} for r in rows),
                   'assets_with_doi': sum(bool(r['source_dois']) for r in rows),
                   'assets_without_source_register_link': sum(r['source_metadata_status'] != 'linked_to_source_register' for r in rows)},
        'assets': rows,
    }
    JSON_OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if os.environ.get('GREENHUB_SKIP_FAIR_WORKBOOK_REFRESH') != '1':
        refresh_workbook_snapshots(rows, input_records)
    print(json.dumps(payload['counts'], indent=2))


def refresh_workbook_snapshots(asset_rows: list[dict], input_records: list[dict]) -> None:
    """Refresh only the two generated FAIR snapshot tabs; leave source tabs intact."""
    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter

    workbook_path = MASTER_WORKBOOK
    if not workbook_path.exists():
        return
    workbook = load_workbook(workbook_path)
    for title, rows, keys, count_label in (
        ('FAIR_Catalog', asset_rows, list(asset_rows[0]), 'indexed source assets'),
        ('Master_Inputs', input_records, list(input_records[0]), 'normalized records'),
    ):
        if title not in workbook.sheetnames:
            continue
        sheet = workbook[title]
        sheet.cell(2, 1, f'GreenHub FAIR snapshot · {len(rows)} {count_label}')
        # Retain title/metadata/header styling and formatting; clear only old body cells.
        for row_idx in range(7, sheet.max_row + 1):
            for col_idx in range(1, max(sheet.max_column, len(keys)) + 1):
                sheet.cell(row_idx, col_idx).value = None
        for col_idx, key in enumerate(keys, 1):
            sheet.cell(6, col_idx, key)
        template_row = 7
        for row_idx, row in enumerate(rows, 7):
            for col_idx, key in enumerate(keys, 1):
                cell = sheet.cell(row_idx, col_idx)
                if row_idx != template_row and template_row <= sheet.max_row:
                    source_cell = sheet.cell(template_row, col_idx)
                    if source_cell.has_style:
                        cell._style = copy(source_cell._style)
                value = row.get(key, '')
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, sort_keys=True)
                cell.value = value
        expected_last_row = 6 + len(rows)
        if sheet.max_row > expected_last_row:
            sheet.delete_rows(expected_last_row + 1, sheet.max_row - expected_last_row)
        sheet.freeze_panes = 'A7'
        sheet.auto_filter.ref = f'A6:{get_column_letter(len(keys))}{expected_last_row}'
    workbook.save(workbook_path)


def build_input_records() -> list[dict]:
    records: list[dict] = []
    zeeland_monthly_reported = _pareto_reports_zeeland_monthly_supply()

    def add(record_id, source_dataset, name, value, unit='', basis='', quality_class='', status='',
            source_title='', stable_identifier='', source_url='', source_location='', geography='',
            reference_year='', uncertainty='', applicability='', runtime_usage='', override_route='', metadata=None):
        raw_quality = str(quality_class or '').strip().upper()
        doi_context = ' '.join((str(stable_identifier or ''), str(source_url or ''),
                                json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)))
        has_doi = bool(extract_dois(doi_context))
        # Keep unsupported defaults in class E. A DOI string by itself does
        # not upgrade a value to C: that promotion requires explicit source,
        # basis, and applicability review upstream. The legacy D label is
        # deprecated for normalized inputs; unverified assumptions map to E.
        normalized_quality = (
            'E' if raw_quality in {'D', 'E'} else
            'E' if raw_quality == 'C' and not has_doi else
            raw_quality
        )
        normalized_metadata = dict(metadata or {})
        quality_mapping_note = (
            'Unverified or no-DOI assumptions are recorded as E. This is not an evidence upgrade: '
            'class C requires explicit review of source, basis, and applicability. Numeric value and '
            'activation state are unchanged.'
        )
        if normalized_quality == 'E':
            # Provenance remains in the row; the obsolete class label does
            # not. This prevents an old export label from being mistaken for
            # a current evidence class.
            normalized_metadata.pop('legacy_quality_class', None)
            if normalized_quality != raw_quality:
                normalized_metadata['quality_class_mapping'] = quality_mapping_note
            else:
                normalized_metadata.setdefault('quality_class_mapping', quality_mapping_note)
        records.append({
            'record_id': str(record_id), 'source_dataset': source_dataset, 'name': name,
            'value': '' if value is None else value, 'unit': unit, 'basis': basis,
            'quality_class': normalized_quality, 'status': status, 'source_title': source_title,
            'stable_identifier': stable_identifier, 'source_url': source_url,
            'source_location': source_location, 'geography': geography,
            'reference_year': reference_year, 'uncertainty': uncertainty,
            'applicability': applicability, 'runtime_usage': runtime_usage,
            'override_route': override_route,
            'additional_metadata_json': json.dumps(normalized_metadata, ensure_ascii=False, sort_keys=True),
        })

    canonical_parameter_rows = read_rows(DATA / 'advanced_model' / 'canonical_parameter_registry.csv')
    canonical_by_id = {row.get('parameter_id', ''): row for row in canonical_parameter_rows}
    for row in canonical_parameter_rows:
        pid = row.get('parameter_id', '')
        is_water_scrubber_recycle = (
            pid == 'phase6.water_scrubber_flash_gas_recycle_fraction'
        )
        add(pid, row.get('source_dataset') or 'Greenhub/data/advanced_model/canonical_parameter_registry.csv',
            row.get('display_name') or pid, row.get('normalized_value') or row.get('value'),
            row.get('normalized_unit') or row.get('unit'),
            'Reported 0.20–0.30 fraction of incoming raw dry gas flow; default selects the reported lower endpoint.'
            if is_water_scrubber_recycle else row.get('basis'), row.get('quality_class'),
            f"{row.get('activation_state','')}; {row.get('readiness_state','')}; literature range selected at reported lower bound"
            if is_water_scrubber_recycle else
            f"{row.get('activation_state','')}; {row.get('readiness_state','')}",
            'Biogas upgrading – Review of commercial technologies' if is_water_scrubber_recycle else row.get('source_title'),
            'SGC Rapport 2013:270' if is_water_scrubber_recycle else row.get('stable_identifier'),
            'https://vav.griffel.net/filer/C_SGC2013-270.pdf' if is_water_scrubber_recycle else ';'.join(
                f'https://doi.org/{doi}' for doi in extract_dois(row.get('stable_identifier') or '')
            ),
            'Section 2.4, p.39' if is_water_scrubber_recycle else row.get('exact_source_location'),
            'Sweden / European commercial-technology review' if is_water_scrubber_recycle else '',
            '2013' if is_water_scrubber_recycle else '',
            ('The source reports a 0.20–0.30 range but no statistical uncertainty; 0.20 is the selected lower endpoint.'
             if is_water_scrubber_recycle else row.get('uncertainty')),
            row.get('applicability_conditions'), 'Canonical registry; resolved by parameter service when applicable.',
            'SimulationRequest overrides and existing registry selectors; see runtime flow documentation.',
            {**{k: row.get(k) for k in ('process_area','unit_operation','unit_id','scenario_ids','component','material_type','evidence_class','transferability_class','physical_lower_bound','physical_upper_bound','recommended_range','editability_category','editable_mode','rebuild_required','dependency_parameter_ids','warnings','model_parameter_name')},
             **({'evidence_class': 'direct technical-report statement; 0.20 selected as the reported lower endpoint of 0.20–0.30',
                 'parameter_basis': 'fraction of incoming conditioned raw dry gas flow; actual recycle is capped by available flash gas',
                 'source_dataset': 'Greenhub/data/Bigas production + upgrade/Water_Scrubbing/recycle_data.csv; WS_REC_001–002',
                 'source_record_ids': ['WS_REC_001', 'WS_REC_002'],
                 'maturity_class': 'D4',
                 'maturity_basis': 'Selected source rows are calculation-connected in the BG2 raw-gas-ratio splitter, covered by water-scrubbing regression tests, and reported in the Phase 6 assumption register and unit design/metric outputs.'}
                if is_water_scrubber_recycle else {})})

    # Keep scenario/mode-qualified literature candidates visible beside the
    # canonical defaults. A canonical fallback can remain class E while a
    # route-specific candidate is C/B; dropping candidates here would make
    # the FAIR snapshot disagree with runtime resolution and hide provenance.
    def parse_json_field(value, default):
        try:
            return json.loads(value) if value else default
        except (TypeError, json.JSONDecodeError):
            return default

    activation_rows = read_rows(DATA / 'advanced_model' / 'parameter_activation_registry.csv')
    for candidate in activation_rows:
        quality = str(candidate.get('quality_class') or '').strip().upper()
        raw_value = str(candidate.get('value') or '').strip()
        if quality not in {'A', 'B', 'C'} or not raw_value:
            continue
        stable_identifier = str(candidate.get('stable_identifier') or '').strip()
        dois = extract_dois(stable_identifier)
        source_url = f'https://doi.org/{dois[0]}' if dois else (
            stable_identifier if stable_identifier.startswith(('http://', 'https://')) else ''
        )
        if not source_url:
            continue
        try:
            value = json.loads(raw_value)
        except json.JSONDecodeError:
            value = raw_value
        parameter_id = candidate.get('parameter_id', '')
        parameter = canonical_by_id.get(parameter_id, {})
        scenario_ids = parse_json_field(candidate.get('scenario_ids'), [])
        months = parse_json_field(candidate.get('months'), [])
        calculation_modes = parse_json_field(candidate.get('calculation_modes'), [])
        warnings = parse_json_field(candidate.get('warnings'), [])
        candidate_id = candidate.get('candidate_id', '')
        add(
            f"candidate:{candidate_id}",
            candidate.get('source_dataset') or 'Greenhub/data/advanced_model/parameter_activation_registry.csv',
            f"{parameter.get('display_name') or parameter_id} — {', '.join(scenario_ids) or 'all scenarios'} candidate",
            value,
            candidate.get('unit') or parameter.get('normalized_unit') or parameter.get('unit') or '',
            candidate.get('basis') or '; '.join(warnings) or parameter.get('basis') or '',
            quality,
            f"{candidate.get('activation_state', '')}; {candidate.get('readiness_state', '')}; {candidate.get('value_status', '')}",
            candidate.get('source_title') or '',
            stable_identifier,
            source_url,
            candidate.get('exact_source_location') or candidate.get('source_row_id') or '',
            '',
            '',
            candidate.get('uncertainty') or 'No parameter-specific statistical uncertainty was reported; no interval inferred.',
            f"scenarios={scenario_ids}; months={months}; calculation_modes={calculation_modes}",
            'Scenario/mode-qualified candidate; eligible only when existing parameter selectors match.',
            'Existing request/UI overrides retain precedence over registry candidate selection.',
            {
                'candidate_id': candidate_id,
                'parameter_id': parameter_id,
                'source_row_id': candidate.get('source_row_id'),
                'source_kind': candidate.get('source_kind'),
                'value_status': candidate.get('value_status'),
                'evidence_class': candidate.get('evidence_class'),
                'transferability_class': candidate.get('transferability_class'),
                'scenario_ids': scenario_ids,
                'months': months,
                'calculation_modes': calculation_modes,
                'readiness_state': candidate.get('readiness_state'),
                'selection_priority': candidate.get('selection_priority'),
                'provenance_chain': parse_json_field(candidate.get('provenance_chain'), []),
                'warnings': warnings,
            },
        )

    # Row-level wet raw-press evidence is indexed for traceability, not injected
    # as a new runtime layer. Only the existing policy's selected IDs are marked
    # calculation-connected; unresolved markers stay explicitly valueless.
    press_path = DATA / 'Pre-treatment' / 'Mechanical' / 'greenhub_direct_raw_press_component_partitioning.csv'
    source_meta = {
        'S01_PEDERSEN_2025': {'identifier': '10.3390/proteomes13010008', 'url': 'https://doi.org/10.3390/proteomes13010008', 'year': '2025', 'geography': 'Denmark', 'quality': 'B', 'status': 'verified_primary_literature'},
        'S02_SANTAMARIA_PATENT_RED_CLOVER': {'identifier': 'WO2015197078A1', 'url': 'https://patents.google.com/patent/WO2015197078A1/en', 'year': '2015', 'geography': 'Not established from the record', 'quality': 'C', 'status': 'patent_source; values remain staged'},
        'S03_SANTAMARIA_FERNANDEZ_2019': {'identifier': '10.1002/bbb.1957', 'url': 'https://doi.org/10.1002/bbb.1957', 'year': '2019', 'geography': 'Denmark', 'quality': 'B', 'status': 'verified_primary_literature'},
        'S04_DCA_2017': {'identifier': 'ISBN 978-87-93398-66-5', 'url': 'https://dcapub.au.dk/djfpdf/DCArapport093.pdf', 'year': '2017', 'geography': 'Denmark', 'quality': 'B', 'status': 'verified_institutional_report'},
        'S05_GUNDERSEN_2022_CASSAVA': {'identifier': '10.1016/j.jclepro.2022.134730', 'url': 'https://doi.org/10.1016/j.jclepro.2022.134730', 'year': '2022', 'geography': 'Taastrup, Denmark (greenhouse-grown cassava cultivar TME12)', 'quality': 'B', 'status': 'verified_primary_literature_reference_only'},
        'S13_SANDOVAL_2026': {'identifier': '10.1038/s41538-026-00831-6', 'url': 'https://doi.org/10.1038/s41538-026-00831-6', 'year': '2026', 'geography': 'Aberystwyth, United Kingdom', 'quality': 'B', 'status': 'verified_primary_literature'},
    }
    active_press_ids = {'RAW_0001','RAW_0002','RAW_0003','RAW_0010','RAW_0011','RAW_0012','RAW_0013','RAW_0014','RAW_0015','RAW_0016'}
    for row in read_rows(press_path):
        source = source_meta.get(row.get('source_id', ''), {})
        normalized_value = row.get('normalized_value', '')
        quality = source.get('quality', '') if source.get('status', '').startswith('verified_') and normalized_value else ''
        if row.get('source_id') == 'S01_PEDERSEN_2025' and normalized_value:
            quality = 'B'
        record_status = ('calculation_connected_existing_dynamic_policy' if row.get('record_id') in active_press_ids
                         else 'missing_source_or_value' if not normalized_value or not source.get('url')
                         else source.get('status', 'staged_evidence'))
        add(f"mechanical.raw_press.{row.get('record_id')}", press_path.relative_to(ROOT).as_posix(),
            f"{row.get('product_stream')} — {row.get('response_parameter')}", normalized_value,
            row.get('normalized_unit'), row.get('basis'), quality, record_status,
            row.get('source_title'), source.get('identifier', ''), source.get('url', ''),
            row.get('page_or_table'), source.get('geography', ''), source.get('year', ''),
            'No row-specific numeric uncertainty reported; do not interpret replicates or source notes as an interval.',
            f"{row.get('species_or_feedstock')}; transferability={row.get('transferability_class')}; confidence={row.get('confidence_class')}; applicability must be evaluated separately from evidence quality.",
            'Existing dynamic raw-press policy consumes only its explicitly selected record IDs; all other rows are discovery/staging only.',
            'No override introduced. Existing UI/request overrides, canonical registry and static baseline precedence are unchanged.',
            {**row, 'transferability_class': row.get('transferability_class'), 'source_resolution_status': source.get('status', 'unresolved'),
             'runtime_selected': row.get('record_id') in active_press_ids,
             'unresolved_value_is_not_zero': not bool(normalized_value),
             'uncertainty_note': 'Not reported per row; no synthetic interval assigned.'})

    preview_path = DATA / 'frontend' / 'preview_parameter_defaults.json'
    preview_profile = json.loads(preview_path.read_text(encoding='utf-8'))
    for row in preview_profile.get('parameters', []):
        add(row.get('parameter_id'), preview_path.relative_to(ROOT).as_posix(), row.get('name'),
            row.get('default_value'), row.get('unit'), row.get('basis') or row.get('notes'),
            row.get('quality_class'), 'preview_only_not_backend_authority', row.get('source_title'),
            row.get('stable_identifier'), row.get('source_url'), row.get('source_location'),
            row.get('geography', 'Project preview reference; source geography is recorded where applicable.'),
            row.get('reference_year', ''),
            row.get('uncertainty'), row.get('notes'),
            'Bundled offline/initial preview only; not submitted as a backend parameter override.',
            'No backend override path. The canonical parameter registry, SimulationRequest and explicit user inputs retain existing precedence.',
            {k: row.get(k) for k in ('category','process_area','current_value','min_value','max_value','is_editable','notes','retrieval_date')})

    profile_path = DATA / 'Pre-treatment' / 'Feedstock' / 'greenhub_feed_composition_defaults.json'
    profile = json.loads(profile_path.read_text(encoding='utf-8'))
    for component, row in profile.get('compounds', {}).items():
        source = row.get('source') or {}
        doi = source.get('doi', '')
        source_url = source.get('source_url') or source.get('url') or (f'https://doi.org/{doi}' if doi else '')
        add(f'feed.{component}', profile_path.relative_to(ROOT).as_posix(), row.get('label') or component,
            row.get('wet_mass_fraction'), 'kg/kg wet feed', 'Wet mass fraction; profile mass balance closes to one.',
            row.get('data_class'), 'active_ui_feed_profile', source.get('source_title') or source.get('source'), doi,
            source_url, source.get('source_location') or component,
            source.get('geography') or 'Netherlands roadside grass profile',
            source.get('reference_year', ''), source.get('uncertainty'),
            source.get('applicability') or source.get('basis'), 'Shared UI composition profile; normalized fractions sent with SimulationRequest.',
            'Explicit UI feed composition overrides; workbook resolver remains available in its existing pathway.',
            {'profile_id': profile.get('profile_id'), 'record_role': row.get('record_role'),
             'value_status': row.get('value_status'),
             'input_status': row.get('input_status'),
             'model_baseline_percent': row.get('model_baseline_percent'), **source})

    recovery_dir = DATA / 'Protein recovery' / 'Isoelectric'
    recovery_path = recovery_dir / 'recovery.csv'
    recovery_metadata = json.loads((recovery_dir / 'recovery_metadata.json').read_text(encoding='utf-8'))
    for row in read_rows(recovery_path):
        metadata = recovery_metadata['records'].get(row.get('parameter_id'), {})
        if not metadata:
            continue
        add(f"protein_recovery.{row['parameter_id']}", recovery_path.relative_to(ROOT).as_posix(),
            row.get('parameter_name') or row.get('python_variable'), row.get('normalized_si_value') or row.get('value'),
            row.get('normalized_si_unit') or row.get('unit'), row.get('basis'), metadata.get('quality_class', ''),
            row.get('data_status', ''), row.get('source_title'), metadata.get('source_doi'), metadata.get('source_url'),
            metadata.get('source_location') or row.get('source_location'), metadata.get('geography'),
            metadata.get('reference_year'), metadata.get('uncertainty'), metadata.get('applicability'),
            metadata.get('runtime_mapping'), 'Literature evidence is selected only by existing registry resolution rules; explicit run overrides retain precedence.',
            {**row, **metadata, 'dataset_id': recovery_metadata.get('dataset_id'),
             'metadata_source': 'Greenhub/data/Protein recovery/Isoelectric/recovery_metadata.json'})

    operating_path = DATA / 'Pre-treatment' / 'Mechanical' / 'literature_operating_candidates.csv'
    operating_metadata_path = DATA / 'Pre-treatment' / 'Mechanical' / 'literature_operating_candidates_metadata.json'
    operating_metadata = json.loads(operating_metadata_path.read_text(encoding='utf-8'))
    for row in read_rows(operating_path):
        metadata = operating_metadata['records'].get(row.get('candidate_id'), {})
        if not metadata:
            raise ValueError(f"Missing operating-candidate FAIR metadata: {row.get('candidate_id')}")
        add(
            f"literature.operating.{row['candidate_id']}",
            operating_path.relative_to(ROOT).as_posix(),
            row.get('parameter_id'), row.get('value'), row.get('unit'),
            row.get('measurement_basis'), row.get('quality_class'),
            'active_opt_in_literature_candidate', row.get('source_title'),
            row.get('doi'), row.get('source_url'), row.get('source_location'),
            row.get('geography'), row.get('year'), row.get('uncertainty'),
            row.get('conditions'),
            'Selectable through the canonical parameter registry only in literature_default or expert_override mode; workbook structural defaults remain unchanged.',
            'Explicit run/project parameter overrides retain precedence; see the resolved-parameter report for the selected source.',
            {**row, **metadata, 'dataset_id': operating_metadata.get('dataset_id'),
             'metadata_source': operating_metadata_path.relative_to(ROOT).as_posix()},
        )

    economic_path = DATA / 'greenhub_economic_defaults.json'
    economic = json.loads(economic_path.read_text(encoding='utf-8'))
    unit_map = {'staffingPeople':'people','paidHoursPerPerson':'h/person/year','laborCostEurPerHour':'EUR/person/h','electricityCostEurMWh':'EUR/MWh','heatCostEurMWh':'EUR/MWh','coolingCostEurMWh':'EUR/MWh','logisticsCostEurTkm':'EUR/(wet t·km)','logisticsDistanceKm':'km','projectLifetimeYears':'year','discountRate':'fraction','taxRate':'fraction','workingCapitalEur':'EUR','residualValueEur':'EUR','capexGrantFraction':'fraction','grassUtilizationBonusEurPerT':'EUR/wet t','grassUtilizationBonusYears':'year','biomethaneBonusEnabled':'boolean','biomethaneBonusEurM3':'EUR/m³','biomethaneBonusYears':'year','additionalBenefitEurYear':'EUR/year','additionalBenefitYears':'year'}
    for key, value in economic['economics'].items():
        evidence = economic.get('input_evidence', {}).get(key, {})
        add(f'economics.{key}', economic_path.relative_to(ROOT).as_posix(), key, value, unit_map.get(key, ''),
            evidence.get('basis', economic['basis']['runtime_policy']), evidence.get('quality_class', 'E'),
            evidence.get('source_status', 'active_ui_default'), evidence.get('source_title', economic['title']),
            evidence.get('stable_identifier', economic['dataset_id']), evidence.get('source_url', ''),
            evidence.get('source_location', key), evidence.get('geography', economic['basis']['geography']),
            evidence.get('reference_year', economic['basis']['price_year']),
            evidence.get('uncertainty', economic['basis']['uncertainty']),
            evidence.get('applicability', economic['basis']['evidence_class_definition']),
            'Configure default; passed as post-route economic override.',
            'User edit in Configure takes precedence for the next reported run.',
            {'version': economic['version'], 'source_status': evidence.get('source_status', economic['basis']['source_status']),
             **evidence})
    for key, record in economic.get('physical_constants', {}).items():
        add(f'physical_constants.{key}', economic_path.relative_to(ROOT).as_posix(), key,
            record.get('value'), record.get('unit'), record.get('basis'),
            record.get('evidence_class', 'D'), 'traceable_physical_reference',
            record.get('source_title', economic['title']), '', record.get('source_url', ''),
            record.get('source_table_page', key), record.get('geography', 'Reference condition'),
            record.get('reference_year'), record.get('uncertainty'), record.get('applicability'),
            'Used by Pareto and UI post-route TEA to normalize biomethane product mass to Nm3.',
            'Source and reference-condition metadata are embedded in the economic defaults dataset.',
            {**record, 'dataset_id': economic['dataset_id'], 'source_file': economic_path.relative_to(ROOT).as_posix()})
    for product, row in economic['product_prices'].items():
        add(f'price.{product}', economic_path.relative_to(ROOT).as_posix(), product, row['value_eur_per_unit'],
            row['unit'], row['basis'], 'E', 'active_ui_price_override', economic['title'], economic['dataset_id'],
            '', product, economic['basis']['geography'], economic['basis']['price_year'], economic['basis']['uncertainty'],
            row['basis'], 'UI explicit product-price override over selected benchmark records.',
            'User edit in Configure > Economics > product prices.', {'source_file': row['source_file']})
    for factor, row in economic['environment'].items():
        add(f'environment.{factor}', economic_path.relative_to(ROOT).as_posix(), factor, row['value'], row['unit'],
            row['basis'], row['evidence_class'], 'active_ui_lca_screening_factor', economic['title'], economic['dataset_id'],
            '; '.join(row['source_urls']), factor, row['geography'], row['reference_year'], row['uncertainty'],
            row['basis'], 'UI screening factor supplied to post-route LCA.', 'User edit in Configure > Environment.', row)

    tea_quality_path = DATA / 'tea' / 'tea_cost_quality_review.json'
    tea_quality_review = json.loads(tea_quality_path.read_text(encoding='utf-8'))
    tea_quality_by_id = {row['cost_id']: row for row in tea_quality_review.get('records', [])}
    tea_cost_rows = read_rows(DATA / 'tea' / 'tea_cost_register.csv')
    tea_cost_ids = {row.get('cost_id', '') for row in tea_cost_rows}
    if tea_cost_ids != set(tea_quality_by_id):
        raise ValueError(f"TEA quality review IDs do not match the cost register: missing={sorted(tea_cost_ids - set(tea_quality_by_id))}, extra={sorted(set(tea_quality_by_id) - tea_cost_ids)}")
    for row in tea_cost_rows:
        status = row.get('source_status', '')
        review = tea_quality_by_id[row['cost_id']]
        quality = review['quality_class']
        source_url = row.get('source_url', '')
        doi_ids = extract_dois(source_url)
        add(row.get('cost_id'), 'Greenhub/data/tea/tea_cost_register.csv', row.get('equipment_or_cost_item'),
            row.get('reference_value_eur') or row.get('rate_value'), row.get('reference_unit') or row.get('rate_unit'),
            row.get('notes'), quality, status, row.get('source_title'), doi_ids[0] if len(doi_ids) == 1 else '; '.join(doi_ids), source_url,
            f"{row.get('source_sheet','')} row {row.get('source_row','')}", 'Netherlands/EU applicability varies', '',
            f"Qualitative source confidence: {row.get('confidence') or 'not recorded'}; no numeric interval is stated here. {review['basis']}",
            row.get('cost_boundary_includes'), 'TEA cost register; activated by route/cost service and completeness gates.',
            'Post-route TEA selection rules; not a process chemistry override.', {**row, 'quality_review': review, 'review_date': tea_quality_review.get('review_date')})

    product_price_review = json.loads((DATA / 'tea' / 'product_price_quality_review.json').read_text(encoding='utf-8'))
    for row in read_rows(DATA / 'tea' / 'netherlands_industrial_product_price_benchmarks.csv'):
        review = product_price_review['benchmarks'].get(row.get('product', ''))
        if review is None:
            raise ValueError(f"Product-price benchmark has no quality review: {row.get('product', '')}")
        add(f"benchmark.{row.get('product','')}", 'Greenhub/data/tea/netherlands_industrial_product_price_benchmarks.csv',
            row.get('product'), row.get('screening_base'), row.get('unit'), row.get('price_basis_or_grade'), review['quality_class'],
            row.get('market_status'), review['source_title'], review['source_id'], review.get('source_url') or row.get('source_url'), review.get('source_location') or row.get('price_date'),
            row.get('geography'), row.get('price_date'), review.get('uncertainty') or row.get('uncertainty_or_limitations'),
            row.get('traceability_and_applicability'), 'Screening benchmark; not automatically active unless selected by TEA configuration.',
            'Explicit product_prices take precedence over activated screening benchmarks.',
            {**row, 'quality_review': review, 'review_date': product_price_review['review_date']})

    # Storage reaction-package inputs are an opt-in calculation package, not
    # canonical registry defaults. Index each parameter without changing its
    # activation or the seasonal controller's existing precedence.
    storage_path = DATA / 'storage' / 'grass_degradation_reactions.csv'
    storage_sources = {
        '10.1042/bj0291116': ('Studies on the anaerobic decomposition of plant materials: comparison of rice-straw decomposition under anaerobic, aerobic and partially aerobic conditions', 1935),
        '10.3389/fmicb.2022.1072140': ('Characteristics of lactic acid bacteria, microbial community and fermentation dynamics of native grass silage prepared in Inner Mongolian Plateau', 2023),
        '10.1002/fes3.475': ('Designing agricultural grasses to help mitigate proteolysis during ensiling to optimize protein feed provisions for livestock', 2023),
        '10.1128/aem.67.1.125-132.2001': ('Anaerobic conversion of lactic acid to acetic acid and 1,2-propanediol by Lactobacillus buchneri', 2001),
        '10.3168/jds.2012-5672': ('Effects of natural and simulated rainfall on indicators of ensilability and nutritive value for wilting alfalfa forages sampled before preservation as silage', 2012),
    }
    for row in read_rows(storage_path):
        source_url = row.get('source_url', '')
        source_dois = extract_dois(source_url)
        doi = source_dois[0] if source_dois else ''
        if not doi and '00641-8' in source_url:
            doi = '10.3168/jds.2012-5672'
        source_title, reference_year = storage_sources.get(doi.lower(),
            (f"Unresolved source locator for {row.get('reaction_id', 'storage reaction')}", ''))
        rate_evidence = row.get('rate_evidence', '')
        # Under the current A-D scale, these DOI-linked kinetic assumptions are
        # class C, not measured/literature-quoted B values. Their source notes
        # and limited transferability remain explicit.
        add(f"storage.reaction.{row.get('reaction_id')}", storage_path.relative_to(ROOT).as_posix(),
            f"{row.get('reaction_id')} {row.get('substrate')} ({row.get('environment')})",
            row.get('k_ref_d_inv'), '1/day',
            'First-order rate on substrate molar pool at reference temperature; rate evidence and limitations are recorded in metadata.',
            'C' if doi else 'D', f"opt-in package; enabled_default={row.get('enabled_default')}; {rate_evidence}",
            source_title, doi, source_url, row.get('source_locator'),
            'Source experiment; transfer to roadside grass is unvalidated', reference_year,
            f"scenario bounds {row.get('k_low_d_inv')}–{row.get('k_high_d_inv')} 1/day ({row.get('range_type')}); not a confidence interval",
            row.get('transfer_warning'),
            'Used only by Greenhub.storage_reactions when the storage reaction package is explicitly selected and assumptions are allowed.',
            'No UI/default override is implied; canonical seasonal storage parameter and existing request precedence remain unchanged.',
            {**row, 'rate_is_direct_measurement': rate_evidence.startswith('measured'),
             'rate_quality_note': ('C: DOI-linked assumed or indirectly transferred kinetics; citation supports source context/mechanism, not a validated roadside-grass rate.' if doi else 'D: uncertain rate without a resolved DOI; not validated for roadside grass.'),
             'source_relevance_note': ('This paper supports the anaerobic lactate-to-acetate/1,2-propanediol pathway; it does not supply the package rate constant.' if row.get('reaction_id') == 'R20' else 'This paper does not support the aerobic reoxidation route or its rate.' if row.get('reaction_id') in {'R17', 'R18', 'R19'} else 'Source is contextual; it does not validate this reaction rate for roadside grass.' if doi else 'Source locator not fully resolved to a persistent identifier; rate remains D.'),
             'stable_identifier': doi, 'source_title_resolution': 'verified DOI metadata' if doi.lower() in storage_sources else 'unresolved; title not inferred'})

    climate = json.loads((DATA / 'lca' / 'climate_factors.json').read_text(encoding='utf-8'))
    for row in climate.get('factors', []):
        q = str(row.get('evidence_class') or '').strip().upper()
        if q not in {'A', 'B', 'C', 'D', 'E'}:
            q = 'B' if row.get('source_status') == 'official_dataset' else ''
        doi = extract_dois(row.get('source_url') or '')
        add(row.get('factor_id'), 'Greenhub/data/lca/climate_factors.json', row.get('factor_id'), row.get('value'),
            row.get('quantity_unit'), row.get('basis'), q, row.get('source_status'), row.get('source_title'),
            ';'.join(doi) or row.get('source_id', ''), row.get('source_url'), row.get('source_table_page'), row.get('geography'), row.get('reference_year'),
            row.get('uncertainty'), row.get('applicability'), 'LCA factor; active only where selected in the declared boundary and inventory.',
            'User climate_factors override is separate from registered background characterization factors.', row)

    # Dutch roadside-grass availability and mowing-schedule literature is
    # searchable in the master records but is intentionally not a runtime
    # harvest-yield/default layer. Standing biomass is not collected yield.
    availability_path = DATA / 'Pre-treatment' / 'Feedstock' / 'roadside_grass_availability_evidence.csv'
    availability_sources = {row.get('source_id'): row for row in read_rows(DATA / 'Pre-treatment' / 'Feedstock' / 'source_register.csv')}
    for row in read_rows(availability_path):
        source = availability_sources.get(row.get('source_id'), {})
        if row.get('observation_type') == 'standing_dry_biomass':
            value = f"{row.get('value_min')}–{row.get('value_max')}"
            unit = row.get('unit')
            basis = row.get('measurement_basis')
        else:
            value = row.get('value')
            unit = row.get('unit')
            basis = row.get('measurement_basis')
        add(row.get('record_id'), availability_path.relative_to(ROOT).as_posix(),
            row.get('observation_type'), value, unit, basis, row.get('quality_class'),
            row.get('evidence_status'), source.get('source_title'), row.get('doi'), row.get('source_url'),
            row.get('source_location'), row.get('geography'), row.get('reference_year'), row.get('limitations'),
            row.get('applicability'),
            'Literature evidence only; not connected to the active feedstock availability calculation or default harvest yield.',
            'No UI or API override added; explicit user configuration and existing model precedence remain unchanged.',
            {**row, 'source_authors': source.get('authors'), 'source_type': source.get('source_type'),
             'activation_state': row.get('activation_state'), 'source_metadata_path': 'Greenhub/data/Pre-treatment/Feedstock/source_register.csv'})
    feedstock_dir = DATA / 'Pre-treatment' / 'Feedstock'
    source_register = {row.get('source_id'): row for row in read_rows(feedstock_dir / 'source_register.csv')}
    biomass_summaries = feedstock_dir / 'mowing_regime_biomass_summary.csv'
    for row in read_rows(biomass_summaries):
        source = source_register.get(row.get('source_id'), {})
        add(
            f"availability.{row.get('record_id')}", biomass_summaries.relative_to(ROOT).as_posix(),
            f"{row.get('mowing_treatment')} treatment {row.get('sampling_month')} standing biomass",
            row.get('mean_standing_biomass_t_dm_per_ha'), 't DM/ha',
            '2023 standing dry biomass summarized from source-reported g/m² values using the authors’ conversion: ×10/1000 to t DM/ha.',
            row.get('quality_class'), f"{row.get('evidence_status')}; n={row.get('n')}; {row.get('activation_state')}",
            source.get('source_title'), row.get('doi'), f"https://doi.org/{row.get('doi')}",
            row.get('source_location'), 'Netherlands; ten roadside grasslands', row.get('study_year'),
            f"Sample SD {row.get('sd_t_dm_per_ha')} t DM/ha; range {row.get('min_t_dm_per_ha')}–{row.get('max_t_dm_per_ha')} t DM/ha; n={row.get('n')}. {row.get('limitations')}",
            'Measured standing biomass before mowing at the study sites; it is not harvested annual yield, accessible area, or delivered feed.',
            'Staged source evidence only; not connected to model availability, defaults, or Pareto calculations.',
            'No override or default changed; existing SimulationRequest and UI precedence remain authoritative.',
            {**row, 'source_id': row.get('source_id'), 'source_authors': source.get('authors'),
             'source_type': source.get('source_type'), 'source_url': source.get('stable_url'),
             'source_dataset_doi': row.get('doi'), 'source_metadata_path': 'Greenhub/data/Pre-treatment/Feedstock/source_register.csv'},
        )
    zeeland_scenarios = feedstock_dir / 'zeeland_availability_scenarios.csv'
    pareto_connected_zeeland_ids = {
        'ZL-ONE-CUT-POTENTIAL', 'ZL-TWO-CUT-SUMMER', 'ZL-TWO-CUT-AUTUMN', 'ZL-TWO-CUT-TOTAL',
    }
    for row in read_rows(zeeland_scenarios):
        source = source_register.get(row.get('source_id'), {})
        connected = row.get('record_id') in pareto_connected_zeeland_ids
        reported_in_pareto = row.get('record_id') in zeeland_monthly_reported
        activation = (
            'calculation_connected_tested_reported_in_pareto' if connected and reported_in_pareto else
            'calculation_connected_tested_reporting_pending' if connected else row.get('activation_state')
        )
        runtime_usage = (
            'Loaded by scripts/run_rvo_pareto_analysis.py as the Pareto seasonal availability input; '
            'carried in SimulationRequest.biomass_schedule.monthly_availability_tonnes and exposed in the saved UI scenario.'
            if connected else
            'Evidence is catalogued only; no default, runtime calculation, or Pareto scenario consumes this row.'
        )
        applicability = (
            'Zeeland two-cut future 100%-collection technical-potential screening case only; not current contracted supply or a national default.'
            if connected else
            'Zeeland-specific evidence only; not a national supply default or current contracted feedstock.'
        )
        override_route = (
            'Pareto scenario configuration only; explicit SimulationRequest biomass schedule remains authoritative, and global/UI defaults are unchanged.'
            if connected else
            'No runtime override; existing user-configured supply and default precedence remain authoritative.'
        )
        add(
            f"availability.{row.get('record_id')}", zeeland_scenarios.relative_to(ROOT).as_posix(),
            f"Zeeland roadside-grass availability: {row.get('regime')} / {row.get('season_period')}",
            row.get('quantity'), row.get('unit'),
            f"Published regional scenario estimate; regime={row.get('regime')}; season={row.get('season_period')}; geographic scope={row.get('geography')}.",
            row.get('quality_class'), f"{row.get('evidence_status')}; {row.get('activation_state')}",
            source.get('source_title'), source.get('doi_or_stable_identifier'),
            source.get('stable_url') or row.get('source_url'),
            row.get('source_location'), row.get('geography'), row.get('reference_year'),
            f"Statistical uncertainty is not quantified in the source. {row.get('limitations')}",
            applicability,
            runtime_usage,
            override_route,
            {**row, 'source_authors': source.get('authors'), 'source_type': source.get('source_type'),
             'source_metadata_path': 'Greenhub/data/Pre-treatment/Feedstock/source_register.csv',
             'activation_state': activation,
             'maturity_class': 'D4' if connected and reported_in_pareto else 'D3' if connected else 'D2',
             'maturity_note': ('Calculation-connected, covered by seasonal-supply and request-round-trip tests, and reported in a saved selectable Pareto scenario.'
                               if connected and reported_in_pareto else
                               'Calculation-connected and tested; publication of a saved monthly-profile Pareto scenario is pending.'
                               if connected else 'Evidence catalogued but not calculation-connected.')},
        )
    profile_status = ('calculation_connected_tested_reported_in_pareto' if zeeland_monthly_reported
                      else 'calculation_connected_tested_reporting_pending')
    add(
        'availability.ZL-TWO-CUT-MONTHLY-ALLOCATION',
        'scripts/run_rvo_pareto_analysis.py',
        'Monthly split of reported Zeeland one-cut or two-cut technical-potential totals',
        'Even allocation across one-cut experimental mowing windows or calendar-day weighting within broad two-cut summer/autumn windows',
        'allocation method',
        'Explicit monthly distribution assumption; seasonal totals come from MooV/VITO Table 11, while the timing window is informed by Dutch roadside mowing studies. Neither source reports measured monthly delivered supply.',
        'C',
        profile_status,
        'Grassland management in a changing climate: insights from a Dutch road verge study',
        '10.1111/avsc.70085',
        'https://doi.org/10.1111/avsc.70085',
        'Study methods and mowing-window results; no measured monthly supply allocation',
        'Zeeland, Netherlands',
        '2021 regional potential report; mowing-window study published 2026 (field data from 2023)',
        'No measured month-by-month delivered supply; monthly values are allocated by the documented even/calendar-day rule.',
        'Zeeland regional technical-potential screening scenarios only; not contracted or accessible plant supply.',
        'Pareto runner reads seasonal totals from the Zeeland evidence CSV and applies the stated weights to the monthly SimulationRequest profile.',
        'Pareto-only scenario configuration; does not replace UI defaults or explicit user supply settings.',
        {
            'source_dataset_doi': '10.1111/avsc.70085',
            'source_data_doi': '10.5281/zenodo.15349657',
            'regional_total_source_id': 'SRC-MOOV-VITO-2021',
            'maturity_class': 'D4' if zeeland_monthly_reported else 'D3',
            'maturity_note': ('Calculation-connected, tested, and reported in saved Pareto scenario profiles.'
                              if zeeland_monthly_reported else
                              'Calculation-connected and tested; saved Pareto reporting is pending.'),
            'quality_class_mapping': 'C denotes a literature-informed allocation assumption; it is not a measured profile.',
        },
    )
    site_productivity_path = DATA / 'Pre-treatment' / 'Feedstock' / 'roadside_grass_site_productivity_2023.csv'
    for row in read_rows(site_productivity_path):
        add(
            f"availability.{row['record_id']}", site_productivity_path.relative_to(ROOT).as_posix(),
            row['site'], row['productivity_t_dm_ha'], 't DM/ha',
            f"Measured site-productivity summary converted from {row['productivity_reported_g_dm_m2']} g DM/m²; standing biomass averaged across mid-June and late-August 2023.",
            row['quality_class'], 'published_measured_site_summary',
            'Grassland management in a changing climate: Insights from a Dutch road verge study',
            f"{row['source_article_doi']}; {row['source_dataset_doi']}", row['source_url'],
            row['source_location'], row['geography'], row['reference_year'],
            row['limitations'], row['applicability'],
            'Literature context for site standing-biomass ranges; not an annual harvest or delivered-feed calculation.',
            'Not used as a GreenHub default or annual-availability value. User/API supply assumptions and overrides retain precedence.',
            row,
        )
    return records


if __name__ == '__main__':
    main()
