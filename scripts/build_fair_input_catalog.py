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
OUT = DATA / 'fair_input_catalog'
CSV_OUT = OUT / 'master_input_catalog.csv'
JSON_OUT = OUT / 'master_input_catalog.json'
INPUTS_CSV = OUT / 'master_input_records.csv'
INPUTS_JSON = OUT / 'master_input_records.json'
SCHEMA_VERSION = '1.0.0'
DOI_PATTERN = re.compile(r'10\.\d{4,9}/[^\s;,)]+', re.IGNORECASE)


def extract_dois(value: str) -> list[str]:
    """Extract DOI IDs, removing common landing-page suffixes like /full."""
    normalized = set()
    for match in DOI_PATTERN.findall(value or ''):
        doi = match.rstrip('.,')
        doi = re.sub(r'/(?:full|pdf)$', '', doi, flags=re.IGNORECASE)
        normalized.add(doi)
    return sorted(normalized)


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
    if rel.endswith('frontend/preview_parameter_defaults.json'):
        return ('frontend_preview_parameters', 'Read-only planning references for the bundled offline preview; not backend inputs.', 'parameter-specific unit; preview-only values and provenance are recorded per row')
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


def main() -> None:
    source_register = read_rows(DATA / 'global_audit_package' / 'global_source_register.csv')
    manifest = read_rows(DATA / 'global_audit_package' / 'global_dataset_manifest.csv')
    sources_by_path: dict[str, list[dict[str, str]]] = {}
    for row in source_register:
        key = (row.get('dataset_path') or '').replace('\\', '/').strip()
        if key:
            sources_by_path.setdefault(key.lower(), []).append(row)
    sources_by_dir: dict[str, list[dict[str, str]]] = {}
    source_file_by_dir: dict[str, str] = {}
    for register_path in DATA.rglob('source_register.csv'):
        if register_path == DATA / 'global_audit_package' / 'global_source_register.csv':
            continue
        key = register_path.parent.relative_to(DATA).as_posix().lower()
        sources_by_dir[key] = read_rows(register_path)
        source_file_by_dir[key] = register_path.relative_to(DATA).as_posix()
    manifest_by_path = {(row.get('dataset_path') or '').replace('\\', '/').lower(): row for row in manifest}
    local_records_by_source = {}
    for record_path in DATA.rglob('*.json'):
        try:
            record = json.loads(record_path.read_text(encoding='utf-8-sig'))
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if isinstance(record, dict) and record.get('source_file'):
            source_path = (record_path.parent / str(record['source_file'])).resolve()
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
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        role, usage, unit_basis = role_for(path)
        candidates = sources_by_path.get(rel.lower(), [])
        linkage = 'direct_dataset_path'
        source_file_names = ['global_audit_package/global_source_register.csv'] if candidates else []
        if not candidates:
            parent_key = path.parent.relative_to(DATA).as_posix().lower()
            candidates = sources_by_dir.get(parent_key, [])
            if candidates:
                linkage = 'directory_level_register_not_asset_specific'
                source_file_names = [source_file_by_dir[parent_key]]
        local_record_pair = local_records_by_source.get(rel.lower())
        local_record = local_record_pair[1] if local_record_pair else {}
        if local_record_pair:
            linkage = 'direct_local_source_record'
            source_file_names.append(local_record_pair[0].relative_to(DATA).as_posix())
        unique = {}
        for source in candidates:
            key = (source.get('source_id') or '', source.get('doi_or_stable_id') or '')
            unique[key] = source
        source_ids = sorted({s.get('source_id', '') for s in unique.values() if s.get('source_id')})
        dois = sorted({doi for s in unique.values()
                       for doi in extract_dois(s.get('doi_or_stable_id') or '')})
        urls = sorted({s.get('url', '') for s in unique.values() if s.get('url')})
        embedded_urls, embedded_dois = embedded_sources(path)
        urls = sorted(set(urls) | set(embedded_urls))
        if local_record.get('source_url'):
            urls = sorted(set(urls) | {str(local_record['source_url'])})
        record_dois = {doi for field in ('dataset_id', 'persistent_identifier')
                       for doi in extract_dois(str(local_record.get(field) or ''))}
        dois = sorted(set(dois) | set(embedded_dois) | record_dois)
        man = manifest_by_path.get(rel.lower(), {})
        media_type = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        if path.suffix.lower() == '.csv':
            media_type = 'text/csv'
        elif path.suffix.lower() == '.xlsx':
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
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
            'readiness': man.get('detected_readiness', ''),
            'source_ids': ';'.join(source_ids),
            'source_dois': ';'.join(dois),
            'doi_urls': ';'.join(f'https://doi.org/{doi}' for doi in dois),
            'source_urls': ';'.join(urls),
            'source_register_paths': ';'.join(source_file_names),
            'source_metadata_linkage': linkage if candidates else 'not_found',
            'source_metadata_status': ('linked_to_source_register' if candidates else 'linked_to_local_source_record' if local_record_pair else 'inline_source_metadata_only' if embedded_urls or embedded_dois else 'file_metadata_only_source_link_not_found'),
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
        'generated_from': 'Greenhub/data/** source assets; source joins from global_audit_package registers',
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

    workbook_path = DATA / 'greenhub_feed_inputs.xlsx'
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
        sheet.freeze_panes = 'A7'
        sheet.auto_filter.ref = f'A6:{get_column_letter(len(keys))}{6 + len(rows)}'
    workbook.save(workbook_path)


def build_input_records() -> list[dict]:
    records: list[dict] = []

    def add(record_id, source_dataset, name, value, unit='', basis='', quality_class='', status='',
            source_title='', stable_identifier='', source_url='', source_location='', geography='',
            reference_year='', uncertainty='', applicability='', runtime_usage='', override_route='', metadata=None):
        records.append({
            'record_id': str(record_id), 'source_dataset': source_dataset, 'name': name,
            'value': '' if value is None else value, 'unit': unit, 'basis': basis,
            'quality_class': quality_class, 'status': status, 'source_title': source_title,
            'stable_identifier': stable_identifier, 'source_url': source_url,
            'source_location': source_location, 'geography': geography,
            'reference_year': reference_year, 'uncertainty': uncertainty,
            'applicability': applicability, 'runtime_usage': runtime_usage,
            'override_route': override_route,
            'additional_metadata_json': json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True),
        })

    for row in read_rows(DATA / 'advanced_model' / 'canonical_parameter_registry.csv'):
        pid = row.get('parameter_id', '')
        add(pid, row.get('source_dataset') or 'Greenhub/data/advanced_model/canonical_parameter_registry.csv',
            row.get('display_name') or pid, row.get('normalized_value') or row.get('value'),
            row.get('normalized_unit') or row.get('unit'), row.get('basis'), row.get('quality_class'),
            f"{row.get('activation_state','')}; {row.get('readiness_state','')}", row.get('source_title'),
            row.get('stable_identifier'), '', row.get('exact_source_location'), '', '', row.get('uncertainty'),
            row.get('applicability_conditions'), 'Canonical registry; resolved by parameter service when applicable.',
            'SimulationRequest overrides and existing registry selectors; see runtime flow documentation.',
            {k: row.get(k) for k in ('process_area','unit_operation','unit_id','scenario_ids','component','material_type','evidence_class','transferability_class','physical_lower_bound','physical_upper_bound','recommended_range','editability_category','editable_mode','rebuild_required','dependency_parameter_ids','warnings','model_parameter_name')})

    # Row-level wet raw-press evidence is indexed for traceability, not injected
    # as a new runtime layer. Only the existing policy's selected IDs are marked
    # calculation-connected; unresolved markers stay explicitly valueless.
    press_path = DATA / 'Pre-treatment' / 'Mechanical' / 'greenhub_direct_raw_press_component_partitioning.csv'
    source_meta = {
        'S01_PEDERSEN_2025': {'identifier': '10.3390/proteomes13010008', 'url': 'https://doi.org/10.3390/proteomes13010008', 'year': '2025', 'geography': 'Denmark', 'quality': 'B', 'status': 'verified_primary_literature'},
        'S02_SANTAMARIA_PATENT_RED_CLOVER': {'identifier': 'WO2015197078A1', 'url': 'https://patents.google.com/patent/WO2015197078A1/en', 'year': '2015', 'geography': 'Not established from the record', 'quality': 'C', 'status': 'patent_source; values remain staged'},
        'S03_SANTAMARIA_FERNANDEZ_2019': {'identifier': '10.1002/bbb.1957', 'url': 'https://doi.org/10.1002/bbb.1957', 'year': '2019', 'geography': 'Denmark', 'quality': 'B', 'status': 'verified_primary_literature'},
        'S04_DCA_2017': {'identifier': 'ISBN 978-87-93398-66-5', 'url': 'https://dcapub.au.dk/djfpdf/DCArapport093.pdf', 'year': '2017', 'geography': 'Denmark', 'quality': 'B', 'status': 'verified_institutional_report'},
        'S05_GUNDERSEN_2022_CASSAVA': {'identifier': '', 'url': '', 'year': '', 'geography': '', 'quality': '', 'status': 'source_identity_mismatch_unresolved'},
    }
    active_press_ids = {'RAW_0001','RAW_0002','RAW_0003','RAW_0010','RAW_0011','RAW_0012','RAW_0013','RAW_0014','RAW_0015','RAW_0016'}
    for row in read_rows(press_path):
        source = source_meta.get(row.get('source_id', ''), {})
        normalized_value = row.get('normalized_value', '')
        quality = source.get('quality', '') if source.get('status', '').startswith('verified_') and normalized_value else ''
        if row.get('source_id') == 'S01_PEDERSEN_2025' and normalized_value:
            quality = 'B'
        if row.get('source_id') == 'S05_GUNDERSEN_2022_CASSAVA':
            quality = ''
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
            {'profile_id': profile.get('profile_id'), 'model_baseline_percent': row.get('model_baseline_percent'), **source})

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
        # A literature citation does not make an assumed or transferred rate a
        # literature measurement. All current reaction constants remain E.
        add(f"storage.reaction.{row.get('reaction_id')}", storage_path.relative_to(ROOT).as_posix(),
            f"{row.get('reaction_id')} {row.get('substrate')} ({row.get('environment')})",
            row.get('k_ref_d_inv'), '1/day',
            'First-order rate on substrate molar pool at reference temperature; rate evidence and limitations are recorded in metadata.',
            'E', f"opt-in package; enabled_default={row.get('enabled_default')}; {rate_evidence}",
            source_title, doi, source_url, row.get('source_locator'),
            'Source experiment; transfer to roadside grass is unvalidated', reference_year,
            f"scenario bounds {row.get('k_low_d_inv')}–{row.get('k_high_d_inv')} 1/day ({row.get('range_type')}); not a confidence interval",
            row.get('transfer_warning'),
            'Used only by Greenhub.storage_reactions when the storage reaction package is explicitly selected and assumptions are allowed.',
            'No UI/default override is implied; canonical seasonal storage parameter and existing request precedence remain unchanged.',
            {**row, 'rate_is_direct_measurement': rate_evidence.startswith('measured'),
             'rate_quality_note': 'E: assumed or indirectly transferred kinetics; citation supports context/mechanism only, not a validated roadside-grass rate.',
             'source_relevance_note': ('This paper supports the anaerobic lactate-to-acetate/1,2-propanediol pathway; it does not supply the package rate constant.' if row.get('reaction_id') == 'R20' else 'This paper does not support the aerobic reoxidation route or its rate.' if row.get('reaction_id') in {'R17', 'R18', 'R19'} else 'Source is contextual; it does not validate this reaction rate for roadside grass.' if doi else 'Source locator not fully resolved to a persistent identifier; rate remains E.'),
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
    return records


if __name__ == '__main__':
    main()
