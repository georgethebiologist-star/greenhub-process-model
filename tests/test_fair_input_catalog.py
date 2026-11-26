import json
import csv
import re
from pathlib import Path

import pytest
from openpyxl import load_workbook

from Greenhub.application.contracts.requests import _default_feed_composition


ROOT = Path(__file__).resolve().parents[1]


def _read_csv(path: Path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def test_doi_extractor_preserves_balanced_parentheses_in_doi_suffix():
    from scripts.build_fair_input_catalog import extract_dois

    doi = "10.1016/S0376-7388(98)00238-5"
    assert extract_dois(doi) == [doi]
    assert extract_dois(f"(https://doi.org/{doi}).") == [doi]


def test_catalog_is_machine_readable_and_covers_authoritative_assets():
    catalog_path = ROOT / 'Greenhub/data/fair_input_catalog/master_input_catalog.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    rows = catalog['assets']
    assert catalog['catalog_id'] == 'urn:greenhub:catalog:master-inputs:v1'
    assert catalog['counts']['assets'] == len(rows)
    assert len({row['relative_path'] for row in rows}) == len(rows)
    assert all(row['dataset_id'].startswith('urn:greenhub:dataset:sha256:') for row in rows)
    assert all(len(row['sha256']) == 64 for row in rows)
    assert any(row['relative_path'].endswith('greenhub_feed_composition_defaults.json') for row in rows)
    assert any(row['relative_path'].endswith('frontend/preview_parameter_defaults.json') for row in rows)
    assert any(row['relative_path'].endswith('tea/tea_cost_quality_review.json') for row in rows)
    assert not any(row['relative_path'].endswith('greenhub_feed_inputs.xlsx') for row in rows)
    assert any(row['relative_path'].endswith('timothy_silage_fermentation_effluent_and_press_liquid_ayanfe_2025_tables2_4_6_reference.csv') for row in rows)
    jrc = next(row for row in rows if row['relative_path'].endswith('JRC_electricity_emission_factors_2024.xlsx'))
    assert jrc['source_metadata_status'] == 'linked_to_local_source_record'
    assert '10.2905/JRC.4800KC0' in jrc['source_dois']
    assert 'CC BY 4.0' in jrc['license_or_rights']
    assert catalog['override_precedence'].startswith('Existing request/UI overrides')
    records = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8'))
    assert records['record_count'] == len(records['records'])
    assert any(row['source_dataset'] == 'Greenhub/data/greenhub_feed_inputs.xlsx' for row in records['records'])
    assert not [row for row in records['records'] if row.get('quality_class') == 'D']
    record_csv = _read_csv(ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.csv')
    by_csv_id = {row['record_id']: row for row in record_csv}
    assert len(by_csv_id) == records['record_count']
    assert all(by_csv_id[row['record_id']]['quality_class'] == row['quality_class'] for row in records['records'])
    normalized_placeholders = [row for row in records['records'] if row.get('quality_class') == 'E']
    assert normalized_placeholders
    for row in normalized_placeholders:
        metadata = json.loads(row['additional_metadata_json'])
        if metadata.get('quality_class_mapping'):
            assert 'not an evidence upgrade' in metadata['quality_class_mapping'].lower()
            assert 'legacy_quality_class' not in metadata
    unresolved_assumptions = [row for row in records['records'] if row.get('quality_class') == 'E']
    phase_3_to_7 = [row for row in records['records'] if row['record_id'].startswith(tuple(f'phase{i}.' for i in range(3, 8)))]
    assert len(phase_3_to_7) == 538
    assert sum(row['quality_class'] == 'E' for row in phase_3_to_7) == 528
    assert sum(row['quality_class'] == 'B' for row in phase_3_to_7) == 10
    unreferenced_placeholders = unresolved_assumptions
    assert not any(row['record_id'].startswith('feed.') for row in unreferenced_placeholders)
    feed_records = {row['record_id']: row for row in records['records'] if row['record_id'].startswith('feed.')}
    for record_id in ('feed.Peptides', 'feed.AminoAcids', 'feed.Microplastics', 'feed.PathogenIndicators'):
        record = feed_records[record_id]
        metadata = json.loads(record['additional_metadata_json'])
        assert record['quality_class'] == ''
        assert metadata['record_role'] == 'unmeasured_model_fallback'
        assert metadata['input_status'] == 'not_measured_numeric_fallback'
        assert 'compatibility fallback' in metadata['basis']
    residual_metadata = json.loads(feed_records['feed.ParticulateBiodegradableOrganics']['additional_metadata_json'])
    assert feed_records['feed.ParticulateBiodegradableOrganics']['quality_class'] == ''
    assert residual_metadata['record_role'] == 'derived_profile_residual'
    assert residual_metadata['input_status'] == 'calculated_baseline_mass_balance_residual'
    assert not ({'feed.PersistentOrganics', 'feed.Pesticides', 'feed.HeavyMetals'}
                & {row['record_id'] for row in unreferenced_placeholders})
    assert all(not re.search(r'10\.\d{4,9}/', f"{row.get('stable_identifier', '')} {row.get('source_url', '')}")
               for row in unreferenced_placeholders)
    b_records = [row for row in records['records'] if row.get('quality_class') == 'B']
    assert all(row.get('source_url') and row.get('uncertainty') for row in b_records)
    assert 'feed.Starch' not in [row['record_id'] for row in b_records]
    starch_record = next(row for row in records['records'] if row['record_id'] == 'feed.Starch')
    assert starch_record['quality_class'] == 'C'
    assert '10.3390/agronomy14010168' in starch_record['stable_identifier']
    record_ids = {row['record_id'] for row in records['records']}
    assert 'feed.Water' in record_ids
    assert 'economics.grassUtilizationBonusEurPerT' in record_ids
    assert 'environment.electricityKgCo2eKwh' in record_ids
    assert any(value.startswith('TEA-') for value in record_ids)
    tea_records = [row for row in records['records'] if row['record_id'].startswith('TEA-')]
    assert len(tea_records) == 55
    tea_by_id = {row['record_id']: row for row in tea_records}
    assert tea_by_id['TEA-002']['quality_class'] == 'B'
    assert tea_by_id['TEA-015']['quality_class'] == 'E'
    assert tea_by_id['TEA-006']['quality_class'] == 'E'
    assert tea_by_id['TEA-051']['quality_class'] == 'E'
    assert all(row['source_url'] for row in tea_by_id.values() if row['quality_class'] == 'B')
    assert all(row['uncertainty'] for row in tea_records)
    assert all(json.loads(row['additional_metadata_json'])['review_date'] == '2026-11-05' for row in tea_records)
    tea_psa_energy = next(row for row in records['records'] if row['record_id'] == 'TEA-041')
    assert tea_psa_energy['stable_identifier'] == '10.1007/s12155-020-10205-9'
    assert tea_psa_energy['source_url'].endswith(tea_psa_energy['stable_identifier'])
    assert any(value.startswith('benchmark.') for value in record_ids)
    preview_records = [row for row in records['records'] if row['record_id'] in {
        'AD_organic_loading_rate', 'PR1_precipitation_recovery', 'S701_solid_capture_efficiency',
        'R711_struvite_conversion_P', 'A721_ammonia_stripping_efficiency', 'M401_membrane_ch4_recovery',
        'feed_moisture_content', 'digester_operating_temp', 'ADM1_k_dis_disintegration_rate',
        'REC001_isoelectric_ph_setpoint', 'STRUV_k_sp_solubility_product',
        'A721_stripping_air_liquid_ratio', 'MEMB_polyimide_co2_ch4_selectivity',
        'E741_evaporator_steam_economy',
    }]
    assert len(preview_records) == 14
    assert all(row['status'] == 'preview_only_not_backend_authority' for row in preview_records)
    assert all('not submitted as a backend parameter override' in row['runtime_usage'] for row in preview_records)
    preview_ksp = next(row for row in preview_records if row['record_id'] == 'STRUV_k_sp_solubility_product')
    assert preview_ksp['quality_class'] == 'B'
    assert preview_ksp['stable_identifier'] == '10.1016/j.watres.2006.11.046'
    assert preview_ksp['uncertainty']
    storage_records = [row for row in records['records'] if row['record_id'].startswith('storage.reaction.')]
    assert len(storage_records) == 23
    assert all(row['quality_class'] == 'C' for row in storage_records)
    assert all('opt-in' in row['status'] for row in storage_records)
    r20 = next(row for row in storage_records if row['record_id'] == 'storage.reaction.R20')
    assert r20['stable_identifier'] == '10.1128/AEM.67.1.125-132.2001'
    r01 = next(row for row in storage_records if row['record_id'] == 'storage.reaction.R01')
    assert r01['stable_identifier'] == '10.1042/bj0291116'
    assert 'rice-straw' in r01['source_title']
    assert 'not a confidence interval' in r01['uncertainty']
    r01_metadata = json.loads(r01['additional_metadata_json'])
    assert 'not a validated roadside-grass rate' in r01_metadata['rate_quality_note']
    assert r01_metadata['rate_quality_note'].startswith('C:')
    assert 'legacy_quality_class' not in r01_metadata
    r06 = next(row for row in storage_records if row['record_id'] == 'storage.reaction.R06')
    assert r06['stable_identifier'] == '10.3389/fmicb.2022.1072140'
    assert r06['source_title'].startswith('Characteristics of lactic acid bacteria')
    reaction_asset = next(row for row in json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_catalog.json').read_text(encoding='utf-8'))['assets'] if row['relative_path'].endswith('grass_degradation_reactions.csv'))
    assert '10.3389/fmicb.2022.1072140/full' not in reaction_asset['source_dois']
    assert '10.3389/fmicb.2022.1072140' in reaction_asset['source_dois']
    r05 = next(row for row in storage_records if row['record_id'] == 'storage.reaction.R05')
    assert r05['stable_identifier'] == '10.3168/jds.2012-5672'
    r17 = next(row for row in storage_records if row['record_id'] == 'storage.reaction.R17')
    assert 'does not support the aerobic reoxidation' in json.loads(r17['additional_metadata_json'])['source_relevance_note']
    recovery = next(row for row in records['records'] if row['record_id'] == 'protein_recovery.REC-001')
    assert recovery['quality_class'] == 'B'
    assert recovery['stable_identifier'] == '10.3389/fsufs.2019.00112'
    assert 'total N' in recovery['applicability']


def test_knmi_weather_observations_are_source_linked_and_not_mislabelled_as_site_measurements():
    catalog = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_catalog.json').read_text(encoding='utf-8'))
    asset = next(row for row in catalog['assets'] if row['relative_path'].endswith('weather/knmi_rotterdam_344_2021_2025.json'))
    assert asset['role'] == 'weather_input_observations'
    assert asset['source_metadata_status'] == 'linked_to_source_register'
    assert 'SRC-KNMI-ROTTERDAM-344-MONTHLY-2021-2025' in asset['source_ids']
    assert 'mndgeg_344_tg.txt' in asset['source_urls']
    assert 'proxy' in asset['runtime_usage_and_precedence'].lower()
    weather_data = json.loads((ROOT / 'Greenhub/data/weather/knmi_rotterdam_344_2021_2025.json').read_text(encoding='utf-8'))
    assert weather_data['evidence_class'].startswith('A: directly observed')
    assert 'exact plant coordinates are not specified' in weather_data['application_status']


def test_active_grass_profile_distinguishes_literature_partition_from_unreferenced_placeholders():
    profile = json.loads((ROOT / 'Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json').read_text(encoding='utf-8'))
    compounds = profile['compounds']
    for component in ('SolubleProtein', 'SuspendedProtein'):
        row = compounds[component]
        assert row['data_class'] == 'C'
        assert row['source']['doi'] == '10.1021/acssuschemeng.2c00838'
        assert 'partition' in row['source']['basis'].lower()
        assert row['source']['uncertainty']
    for component in ('PersistentOrganics', 'Pesticides', 'HeavyMetals'):
        assert compounds[component]['data_class'] == 'C'
        assert compounds[component]['source']['data_class'] == 'C'
        assert compounds[component]['source'].get('source_quality_class') == 'B'
        assert compounds[component]['source'].get('doi')
        assert compounds[component]['source'].get('uncertainty')
        applicability = compounds[component]['source']['applicability'].lower()
        assert 'not ' in applicability
    for component in ('Microplastics', 'PathogenIndicators'):
        assert compounds[component]['data_class'] is None
        assert compounds[component]['source']['data_class'] is None
        assert compounds[component]['record_role'] == 'unmeasured_model_fallback'
        assert compounds[component]['input_status'] == 'not_measured_numeric_fallback'
        assert 'doi' not in compounds[component]['source']
        assert 'not a measured' in compounds[component]['source']['basis'].lower()
    assert {row['data_class'] for row in compounds.values()} <= {'A', 'B', 'C', None}
    for component in ('PrecipitatedProtein', 'HeatCoagulatedProtein'):
        row = compounds[component]
        assert row['record_role'] == 'structural_initial_state'
        assert row['data_class'] is None
        assert row['source']['data_class'] is None
        assert row['wet_mass_fraction'] == 0.0
    assert not [row for row in compounds.values() if row.get('data_class') == 'D']
    for row in compounds.values():
        if row.get('record_role') == 'unmeasured_model_fallback' and row['wet_mass_fraction'] == 0.0:
            assert row['data_class'] is None
            assert row['input_status'] == 'not_measured_zero_fallback'
        elif row.get('record_role') == 'unmeasured_model_fallback':
            assert row['data_class'] is None
            assert row['input_status'] == 'not_measured_numeric_fallback'
            assert row['wet_mass_fraction'] > 0.0
    residual = compounds['ParticulateBiodegradableOrganics']
    assert residual['record_role'] == 'derived_profile_residual'
    assert residual['data_class'] is None
    assert residual['input_status'] == 'calculated_baseline_mass_balance_residual'
    assert all(row['source'].get('doi') or row['source'].get('source_url')
               for row in compounds.values() if row['data_class'] == 'C')


def test_literature_proxy_starch_uses_traceable_ryegrass_comparator_as_class_c():
    profile = json.loads((ROOT / 'Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json').read_text(encoding='utf-8'))
    starch = profile['compounds']['Starch']
    source = starch['source']
    assert starch['data_class'] == 'C'
    assert source['data_class'] == source['source_quality_class'] == 'B'
    assert source['reported_mean_g_per_kg_dry_matter'] == 34
    assert source['reported_range_min_g_per_kg_dry_matter'] == 1
    assert source['reported_range_max_g_per_kg_dry_matter'] == 169
    assert source['sample_count'] == 100
    assert source['nirs_r_squared'] == pytest.approx(0.77)
    assert source['standard_error_calibration_g_per_kg_dry_matter'] == pytest.approx(1.45)
    assert source['standard_error_validation_g_per_kg_dry_matter'] == pytest.approx(2.23)
    assert starch['wet_mass_fraction'] == pytest.approx(34 / 1000 * profile['dry_matter_fraction'])
    assert source['source_type'].startswith('peer-reviewed primary study')
    assert source['doi'] == '10.3390/agronomy14010168'
    assert 'Table 2' in source['source_location']
    assert 'not a GreenHub or roadside-grass measurement' in source['basis']
    assert source['applicability'].startswith('Low-transferability class-C proxy')
    assert source['uncertainty']
    assert _default_feed_composition()['Starch'] == pytest.approx(starch['wet_mass_fraction'])
    assert sum(row['wet_mass_fraction'] for row in profile['compounds'].values()) == pytest.approx(1.0)
    source_data_path = ROOT / 'Greenhub/data/Pre-treatment/Feedstock/perennial_ryegrass_starch_gierus_2024_reference.csv'
    with source_data_path.open(encoding='utf-8-sig', newline='') as source_data_file:
        source_row = next(csv.DictReader(source_data_file))
    assert source_row['observation_id'] == 'GIERUS24-STARCH-SUMMARY'
    assert source_row['value'] == '34'
    assert source_row['activation_state'] == 'reference_only'
    source_sidecar = json.loads(source_data_path.with_suffix('.csv.source.json').read_text(encoding='utf-8'))
    assert source_sidecar['persistent_identifier'] == 'https://doi.org/10.3390/agronomy14010168'
    manifest_rows = _read_csv(ROOT / 'Greenhub/data/Pre-treatment/Feedstock/dataset_manifest.csv')
    assert any(row['file_name'] == source_data_path.name and row['row_count'] == '1' for row in manifest_rows)
    source_rows = _read_csv(ROOT / 'Greenhub/data/Pre-treatment/Feedstock/source_register.csv')
    assert any(row['source_id'] == source['source_id'] and row['doi_or_stable_identifier'] == source['doi'] for row in source_rows)
    catalog = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8'))
    record = next(row for row in catalog['records'] if row['record_id'] == 'feed.Starch')
    assert record['source_title'] == source['source_title']
    assert record['source_url'] == (source.get('source_url') or source['url'])
    assert record['source_location'] == source['source_location']
    assert record['geography'] == source['geography']
    assert str(record['reference_year']) == str(source['reference_year'])
    assert record['quality_class'] == 'C'
    assert 'SRC-GIERUS-2024-RYEGRASS-STARCH' in record['additional_metadata_json']


def test_active_parameter_registry_has_no_quality_d_and_jrc_factor_is_traceable_b():
    registry_path = ROOT / 'Greenhub/data/advanced_model/canonical_parameter_registry.csv'
    with registry_path.open(encoding='utf-8-sig', newline='') as handle:
        registry = list(csv.DictReader(handle))
    assert not [row for row in registry if row.get('activation_state') == 'active' and row.get('quality_class') == 'D']
    defaults = json.loads((ROOT / 'Greenhub/data/greenhub_economic_defaults.json').read_text(encoding='utf-8'))
    electricity_price = defaults['input_evidence']['electricityCostEurMWh']
    assert defaults['economics']['electricityCostEurMWh'] == 203.0
    assert electricity_price['quality_class'] == 'B'
    assert electricity_price['stable_identifier'] == 'CBS-85666NED'
    assert '2026 first half' in electricity_price['source_location']
    assert 'multiplying by 1,000' in electricity_price['basis']
    factor = defaults['environment']['electricityKgCo2eKwh']
    assert factor['value'] == 0.406463
    assert factor['evidence_class'] == 'B'
    assert factor['reference_year'] == 2021
    assert factor['source_table_page'] == 'Table3_EU_LC, Netherlands row, 2021 column'
    assert Path(ROOT / factor['source_file']).is_file()
    heat = defaults['environment']['heatKgCo2eKwh']
    assert heat['value'] == 0.111456
    assert heat['evidence_class'] == 'B'
    assert heat['reference_year'] == 2022

    records = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8'))['records']
    by_id = {row['record_id']: row for row in records}
    assert by_id['economics.electricityCostEurMWh']['quality_class'] == 'B'
    assert by_id['economics.electricityCostEurMWh']['stable_identifier'] == 'CBS-85666NED'
    assert by_id['heat']['quality_class'] == 'B'
    assert by_id['heat']['stable_identifier'] == 'SRC-CEDELFT-2022-HEAT'
    assert '30.96 kg CO2e/GJ' in by_id['heat']['basis']
    assert by_id['TEA-051']['quality_class'] == 'E'
    assert 'user-provided' in by_id['TEA-051']['status']
    for missing_id in ('seasonal.storage_capacity_kg', 'seasonal.storage_degradation_rate_per_day'):
        assert by_id[missing_id]['quality_class'] == ''
        assert by_id[missing_id]['value'] == ''


def test_roadside_feed_and_ipcc_factor_metadata_are_linked_and_values_traceable():
    profile = json.loads((ROOT / 'Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json').read_text(encoding='utf-8'))
    compounds = profile['compounds']
    assert compounds['EntrappedSugars']['wet_mass_fraction'] == pytest.approx(0.004784)
    assert compounds['EntrappedSugars']['data_class'] == 'C'
    assert compounds['EntrappedSugars']['source']['doi'] == '10.1021/acssuschemeng.2c00838'
    assert compounds['EntrappedSugars']['source']['source_id'] == 'SRC-SMIT-2022'
    assert compounds['EntrappedSugars']['source']['secondary_source_doi'] == '10.2508/chikusan.47.205'
    assert compounds['EntrappedSugars']['source']['uncertainty']
    for name, table in [('Cellulose', 'Table 4'), ('Hemicellulose', 'Table 5'), ('Lignin', 'Table 6')]:
        assert compounds[name]['data_class'] == 'C'
        assert compounds[name]['value_status'] == 'literature_derived_assumption'
        source = compounds[name]['source']
        assert source['data_class'] == source['source_quality_class'] == 'B'
        assert source['doi'] == '10.12911/22998993/66249'
        assert source['source_id'] == 'SRC-TRUBA-2017'
        assert table in source['source_location']
        assert source['geography'] == 'Siedlce, Poland'
        assert source['uncertainty']
    assert compounds['Cellulose']['wet_mass_fraction'] == pytest.approx(0.0344344)
    assert compounds['Hemicellulose']['wet_mass_fraction'] == pytest.approx(0.0214071)
    assert compounds['Lignin']['wet_mass_fraction'] == pytest.approx(0.0058916)
    ash = compounds['Ash']['source']
    expected_residual_ash = (
        0.179 * profile['dry_matter_fraction']
        - compounds['ChlorideIon']['wet_mass_fraction']
        - compounds['HeavyMetals']['wet_mass_fraction']
    )
    assert compounds['Ash']['wet_mass_fraction'] == pytest.approx(expected_residual_ash)
    assert ash['source_id'] == 'SRC-BROWN-2020'
    assert '17.9 ± 2.0%' in ash['uncertainty']

    factors = json.loads((ROOT / 'Greenhub/data/lca/climate_factors.json').read_text(encoding='utf-8'))['factors']
    by_id = {row['factor_id']: row for row in factors}
    assert (by_id['fossil_co2']['value'], by_id['biogenic_methane']['value'], by_id['nitrous_oxide']['value']) == (1, 27, 273)
    for name in ('fossil_co2', 'biogenic_methane', 'nitrous_oxide'):
        row = by_id[name]
        assert row['source_doi'] == '10.1017/9781009157896.009'
        assert row['source_id'] == 'SRC-IPCC-AR6-WGI-CH07'
        assert row['source_title'].startswith('Climate Change 2021')
    assert '27.0 +/- 11' in by_id['biogenic_methane']['uncertainty']
    assert '273 +/- 130' in by_id['nitrous_oxide']['uncertainty']


def test_storage_literature_sources_are_indexed_without_promoting_transferred_rates():
    catalog = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_catalog.json').read_text(encoding='utf-8'))
    assets = {row['relative_path']: row for row in catalog['assets']}
    assert not any(Path(path).name.startswith('~$') for path in assets)
    backup = assets['Greenhub/data/greenhub_feed_inputs_phase6_backup.xlsx']
    assert backup['role'] == 'archived_workbook_backup'
    assert 'not an active input' in backup['runtime_usage_and_precedence']
    asset = assets['Greenhub/data/storage/grass_degradation_reactions.csv']
    assert asset['source_metadata_status'] == 'linked_to_source_register'
    assert 'storage/source_register.csv' in asset['source_register_paths']

    records = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8'))['records']
    reaction = next(row for row in records if row['record_id'] == 'storage.reaction.R01')
    assert reaction['quality_class'] == 'C'
    assert reaction['stable_identifier'] == '10.1042/bj0291116'
    assert 'does not validate' in reaction['additional_metadata_json']


def test_fair_catalog_never_attributes_every_folder_source_to_an_unidentified_asset():
    catalog = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_catalog.json').read_text(encoding='utf-8'))
    assets = {row['relative_path']: row for row in catalog['assets']}
    package_note = assets['Greenhub/data/Bigas production + upgrade/AD kinetics/validation_report.json']
    assert package_note['source_ids'] == ''
    assert package_note['source_metadata_status'] != 'linked_to_source_register'
    assert package_note['source_metadata_linkage'] == 'not_found'

    reaction = assets['Greenhub/data/storage/grass_degradation_reactions.csv']
    assert reaction['source_metadata_linkage'] == 'embedded_doi_local_register'
    assert 'SRC-RICE-DECOMPOSITION-1935' in reaction['source_ids'].split(';')
    assert 'SRC-HOMEKY-ROADSIDE-ENSILING-DURATION-2016' not in reaction['source_ids'].split(';')

    for filename in ('varta_2026_grass_fiber_measurements.csv', 'varta_2026_grass_juice_measurements.csv'):
        row = assets[f'Greenhub/data/Pre-treatment/Feedstock/{filename}']
        assert row['source_ids'] == 'SRC-VARTA-2026-10-27'
        assert row['source_metadata_status'] == 'linked_to_source_register'

    cross_stage = assets['Greenhub/data/Bigas production + upgrade/Feed BMP/ad_roadside_seasonal_biogas_reference_2024.csv']
    assert cross_stage['source_ids'] == 'SRC-CZUBASZEK-2024'
    assert cross_stage['source_metadata_linkage'] == 'direct_dataset_path'
    assert cross_stage['source_metadata_status'] == 'linked_to_source_register'
    assert cross_stage['source_dois'] == '10.3390/en17071751'
    unresolved = assets['Greenhub/data/Centrifuge/greenhub_second_centrifuge_protein_capture.csv']
    assert unresolved['source_metadata_status'] != 'linked_to_source_register'


def test_site_productivity_records_are_traceable_and_not_used_as_annual_supply():
    records = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8'))['records']
    site_rows = [row for row in records if row['record_id'].startswith('availability.RV-PROD-2023-')]
    assert len(site_rows) == 10
    assert all(row['quality_class'] == 'B' for row in site_rows)
    assert all('10.5281/zenodo.15349657' in row['stable_identifier'] for row in site_rows)
    assert all('not annual harvest yield' in row['uncertainty'].lower() for row in site_rows)

    with (ROOT / 'Greenhub/data/storage/source_register.csv').open(encoding='utf-8-sig', newline='') as handle:
        sources = list(csv.DictReader(handle))
    by_id = {row['source_id']: row for row in sources}
    grass_silage = by_id['SRC-GRASS-SILAGE-BUNKER-1997']
    assert grass_silage['doi_or_stable_identifier'] == '10.1111/j.1365-2494.1997.tb02348.x'
    assert '0.3% and 0.9%' in grass_silage['quality_notes']


def test_methane_reference_density_is_fair_indexed_and_condition_specific():
    records = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8'))['records']
    row = next(item for item in records if item['record_id'] == 'physical_constants.biomethane_density_kg_per_nm3')
    metadata = json.loads(row['additional_metadata_json'])
    assert row['value'] == pytest.approx(0.71751)
    assert row['unit'] == 'kg/Nm3'
    assert row['quality_class'] == 'B'
    assert '273.15 K' in row['basis']
    assert row['source_url'] == 'https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nbsir85-3028.pdf'
    assert '±0.00006' in row['uncertainty']
    assert 'actual biomethane composition' in metadata['applicability']


def test_acer_biomethane_market_reference_is_separate_from_user_price_assumption():
    records = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8'))['records']
    by_id = {row['record_id']: row for row in records}
    acer = by_id['benchmark.Biomethane']
    user_price = by_id['benchmark.Biomethane (user all-in direct basis)']
    assert acer['value'] == '60.51'
    assert acer['unit'] == 'EUR/MWh'
    assert acer['quality_class'] == 'B'
    assert acer['stable_identifier'] == 'ACER-DATAITEM-1226'
    assert 'Slide 27' in acer['source_location']
    assert user_price['value'] == '0.88'
    assert user_price['unit'] == 'EUR/m3'
    assert user_price['quality_class'] == 'E'
    assert user_price['stable_identifier'] == 'USER-GAS-GO-SCREEN-2026'
    assert 'not the ACER' in user_price['additional_metadata_json']


def test_national_roadside_availability_sources_are_traceable_and_staged():
    evidence_path = ROOT / 'Greenhub/data/Pre-treatment/Feedstock/roadside_grass_availability_evidence.csv'
    source_path = ROOT / 'Greenhub/data/Pre-treatment/Feedstock/source_register.csv'
    with evidence_path.open(encoding='utf-8-sig', newline='') as stream:
        rows = {row['record_id']: row for row in csv.DictReader(stream)}
    with source_path.open(encoding='utf-8-sig', newline='') as stream:
        sources = {row['source_id']: row for row in csv.DictReader(stream)}
    expected = {
        'AV-RWS-HIGHWAY-VERGE-AREA',
        'AV-WUR-RWS-HERBACEOUS-115K',
        'AV-WUR-ROAD-VERGE-DRY-YIELD',
        'AV-WUR-ROAD-VERGE-FRESH-YIELD',
    }
    selected = [rows[key] for key in expected]
    assert {row['quality_class'] for row in selected} == {'B'}
    assert {row['activation_state'] for row in selected} == {'staged_evidence'}
    assert all(row['source_id'] in sources for row in selected)
    assert sources['SRC-WUR-REGIONAL-HERBACEOUS-2023']['doi_or_stable_identifier'] == '10.18174/630159'
    assert rows['AV-WUR-RWS-HERBACEOUS-115K']['value'] == '115000'
    assert rows['AV-WUR-ROAD-VERGE-DRY-YIELD']['value_min'] == '3'
    assert rows['AV-WUR-ROAD-VERGE-DRY-YIELD']['value_max'] == '5'


def test_bakker_harvest_regimes_link_to_the_biomass_mowing_study():
    evidence_path = ROOT / 'Greenhub/data/Pre-treatment/Feedstock/roadside_grass_availability_evidence.csv'
    source_path = ROOT / 'Greenhub/data/Pre-treatment/Feedstock/source_register.csv'
    with evidence_path.open(encoding='utf-8-sig', newline='') as stream:
        rows = {row['record_id']: row for row in csv.DictReader(stream)}
    with source_path.open(encoding='utf-8-sig', newline='') as stream:
        sources = {row['source_id']: row for row in csv.DictReader(stream)}

    regimes = [row for record_id, row in rows.items() if record_id.startswith('AV-BAKKER-2026-REGIME-')]
    assert len(regimes) == 6
    assert all(row['source_id'] == 'SRC-BAKKER-AVSC-2026' for row in regimes)
    assert all(row['doi'] == '10.1111/avsc.70085' for row in regimes)
    assert all(row['quality_class'] == 'B' and row['activation_state'] == 'staged_evidence' for row in regimes)
    assert sources['SRC-BAKKER-AVSC-2026']['doi_or_stable_identifier'] == '10.1111/avsc.70085'
    dataset = sources['SRC-BAKKER-AVSC-DATA-2025']
    assert dataset['doi_or_stable_identifier'] == '10.5281/zenodo.15349657'
    assert dataset['stable_url'] == 'https://doi.org/10.5281/zenodo.15349657'
    assert 'CC BY 4.0' in dataset['quality_notes']
    assert 'exact zenodo biomass.csv and analysis.r are now vendored' in dataset['quality_notes'].lower()
    assert all(
        'schedule' in row['limitations'].lower()
        and ('harvested yield' in row['limitations'].lower() or 'contract' in row['limitations'].lower())
        for row in regimes
    )


def test_bakker_biomass_source_data_is_preserved_and_not_mistaken_for_supply():
    source_path = ROOT / 'Greenhub/data/Pre-treatment/Feedstock/Biomass.csv'
    with source_path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream, delimiter=';'))
    assert len(rows) == 120
    assert {row['Month'] for row in rows} == {'Jun', 'Aug'}
    assert {row['Mow'] for row in rows} == {'Aug', 'Nov', 'JunhAug', 'JunhNov', 'JunAug', 'JunNov'}
    assert sum(not row['Biomass'].strip() for row in rows) == 1
    assert all(row['Biomass'] == '' or float(row['Biomass']) > 0 for row in rows)
    assert all(row['Productivity'] and float(row['Productivity']) > 0 for row in rows)
    catalog = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_catalog.json').read_text(encoding='utf-8'))
    asset = next(item for item in catalog['assets'] if item['relative_path'].endswith('/Feedstock/Biomass.csv'))
    assert asset['source_metadata_status'] == 'linked_to_source_register'
    assert 'global_audit_package/global_source_register.csv' in asset['source_register_paths']
    assert 'Pre-treatment/Feedstock/Biomass.csv.source.json' in asset['source_register_paths']


def test_bakker_biomass_summaries_recompute_from_preserved_source_rows():
    root = ROOT / 'Greenhub/data/Pre-treatment/Feedstock'
    with (root / 'Biomass.csv').open(encoding='utf-8-sig', newline='') as stream:
        source = list(csv.DictReader(stream, delimiter=';'))
    grouped = {}
    for row in source:
        if row['Biomass'].strip():
            grouped.setdefault((row['Mow'], row['Month']), []).append(float(row['Biomass']) * 10 / 1000)
    with (root / 'mowing_regime_biomass_summary.csv').open(encoding='utf-8-sig', newline='') as stream:
        summaries = list(csv.DictReader(stream))
    assert len(summaries) == 12
    for row in summaries:
        values = grouped[(row['mowing_treatment'], row['sampling_month'])]
        assert int(row['n']) == len(values)
        assert float(row['mean_standing_biomass_t_dm_per_ha']) == pytest.approx(sum(values) / len(values), abs=0.00005)
        assert row['quality_class'] == 'A'
        assert row['activation_state'] == 'staged_evidence'
        assert 'not' in row['limitations'].lower()
    records = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8'))['records']
    normalized = {row['record_id']: row for row in records}
    record = normalized['availability.BM-2023-AUG-AUG']
    assert record['value'] == '3.8902'
    assert record['unit'] == 't DM/ha'
    assert record['quality_class'] == 'A'
    assert record['stable_identifier'] == '10.5281/zenodo.15349657'


def test_zeeland_supply_scenarios_keep_current_and_future_supply_distinct():
    path = ROOT / 'Greenhub/data/Pre-treatment/Feedstock/zeeland_availability_scenarios.csv'
    with path.open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    by_id = {row['record_id']: row for row in rows}
    assert len(rows) == 8
    assert by_id['ZL-CURRENT-COLLECTED-2018']['quantity'] == '250'
    assert by_id['ZL-ONE-CUT-POTENTIAL']['quantity'] == '25300'
    assert by_id['ZL-TWO-CUT-TOTAL']['quantity'] == '42300'
    assert float(by_id['ZL-TWO-CUT-SUMMER']['quantity']) + float(by_id['ZL-TWO-CUT-AUTUMN']['quantity']) == 42300
    assert by_id['ZL-TWO-CUT-DRY-TOTAL']['quantity'] == '14000'
    assert all(row['quality_class'] == 'B' and row['activation_state'] == 'staged_evidence' for row in rows)
    assert all(row['source_id'] == 'SRC-MOOV-VITO-2021' for row in rows)
    assert all(row['limitations'].strip() for row in rows)
    with (ROOT / 'Greenhub/data/Pre-treatment/Feedstock/source_register.csv').open(encoding='utf-8-sig', newline='') as stream:
        sources = {row['source_id']: row for row in csv.DictReader(stream)}
    assert sources['SRC-MOOV-VITO-2021']['year'] == '2021'
    assert sources['SRC-MOOV-VITO-2021']['stable_url'].startswith('https://moov.vito.be/')
    assert not sources['SRC-MOOV-VITO-2021']['doi_or_stable_identifier']
    catalog = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_catalog.json').read_text(encoding='utf-8'))
    asset = next(item for item in catalog['assets'] if item['relative_path'].endswith('/zeeland_availability_scenarios.csv'))
    assert asset['source_metadata_status'] == 'linked_to_source_register'
    records = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8'))['records']
    normalized = {row['record_id']: row for row in records}
    current = normalized['availability.ZL-CURRENT-COLLECTED-2018']
    future = normalized['availability.ZL-TWO-CUT-TOTAL']
    assert current['value'] == '250' and current['quality_class'] == 'B'
    assert future['value'] == '42300' and future['quality_class'] == 'B'
    assert 'regional estimate' in current['uncertainty'].lower()
    assert 'not current' in future['uncertainty'].lower()


def test_zeeland_monthly_allocation_record_keeps_usage_and_maturity_metadata():
    records = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8'))['records']
    record = next(row for row in records if row['record_id'] == 'availability.ZL-TWO-CUT-MONTHLY-ALLOCATION')
    metadata = json.loads(record['additional_metadata_json'])
    assert record['quality_class'] == 'C'
    assert record['status'] == 'calculation_connected_tested_reporting_pending'
    assert record['geography'] == 'Zeeland, Netherlands'
    assert 'not contracted' in record['applicability']
    assert 'monthly SimulationRequest profile' in record['runtime_usage']
    assert record['override_route'].startswith('Pareto-only')
    assert metadata['maturity_class'] == 'D3'
    assert 'saved Pareto reporting is pending' in metadata['maturity_note']
    assert metadata['source_data_doi'] == '10.5281/zenodo.15349657'


def test_master_workbook_fair_snapshots_match_generated_catalogs():
    with (ROOT / 'Greenhub/data/fair_input_catalog/master_input_catalog.csv').open(encoding='utf-8-sig', newline='') as handle:
        catalog = list(csv.reader(handle))
    with (ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.csv').open(encoding='utf-8-sig', newline='') as handle:
        records = list(csv.reader(handle))
    quality_column = records[0].index('quality_class')
    assert all(row[quality_column].strip().upper() != 'D' for row in records[1:])
    workbook = load_workbook(ROOT / 'Greenhub/data/greenhub_feed_inputs.xlsx', read_only=False, data_only=False)
    assert workbook.sheetnames[-2:] == ['FAIR_Catalog', 'Master_Inputs']
    catalog_sheet = workbook['FAIR_Catalog']
    master_sheet = workbook['Master_Inputs']
    assert catalog_sheet['A2'].value.endswith(f'{len(catalog) - 1} indexed source assets')
    assert master_sheet['A2'].value.endswith(f'{len(records) - 1} normalized records')
    assert [catalog_sheet.cell(6, column).value for column in range(1, len(catalog[0]) + 1)] == catalog[0]
    assert [master_sheet.cell(6, column).value for column in range(1, len(records[0]) + 1)] == records[0]
    catalog_last_row = 6 + len(catalog) - 1
    assert max(row for row in range(1, catalog_sheet.max_row + 1)
               if any(cell.value is not None for cell in catalog_sheet[row])) == catalog_last_row
    assert all(cell.value is None for cell in catalog_sheet[catalog_last_row + 1])
    assert master_sheet.max_row == 6 + len(records) - 1
    ipcc = next(row for row in records if row[0] == 'biogenic_methane')
    workbook_row = next(row for row in master_sheet.iter_rows(min_row=7, values_only=True) if row[0] == 'biogenic_methane')
    assert workbook_row[9] == ipcc[9] == '10.1017/9781009157896.009'
    assert workbook_row[14] == ipcc[14]


def test_raw_press_evidence_is_traceable_without_changing_runtime_precedence():
    records = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8'))['records']
    rows = {row['record_id']: row for row in records if row['record_id'].startswith('mechanical.raw_press.')}
    assert len(rows) == 75
    selected = {'RAW_0001','RAW_0002','RAW_0003','RAW_0010','RAW_0011','RAW_0012','RAW_0013','RAW_0014','RAW_0015','RAW_0016'}
    assert {key.rsplit('.', 1)[-1] for key, row in rows.items() if row['status'] == 'calculation_connected_existing_dynamic_policy'} == selected
    ryegrass = rows['mechanical.raw_press.RAW_0001']
    assert ryegrass['quality_class'] == 'B'
    assert ryegrass['stable_identifier'] == '10.3390/proteomes13010008'
    assert ryegrass['source_location'] == 'Table 1'
    metadata = json.loads(ryegrass['additional_metadata_json'])
    assert metadata['transferability_class'] == 'A_direct_grass_or_green_forage'
    assert metadata['runtime_selected'] is True
    unresolved = rows['mechanical.raw_press.RAW_0064']
    assert unresolved['value'] == ''
    assert unresolved['quality_class'] == ''
    assert unresolved['status'] == 'missing_source_or_value'
    assert json.loads(unresolved['additional_metadata_json'])['unresolved_value_is_not_zero'] is True
    cassava = rows['mechanical.raw_press.RAW_0057']
    assert cassava['quality_class'] == 'B'
    cassava_metadata = json.loads(cassava['additional_metadata_json'])
    assert cassava_metadata['transferability_class'] == 'low_transferability_reference_only'
    assert cassava_metadata['source_resolution_status'] == 'verified_primary_literature_reference_only'
    assert cassava['stable_identifier'] == '10.1016/j.jclepro.2022.134730'
    assert cassava['source_url'] == 'https://doi.org/10.1016/j.jclepro.2022.134730'
    assert cassava_metadata['runtime_selected'] is False
    assert 'No override introduced' in ryegrass['override_route']


def test_seasonal_roadside_grass_lignocellulose_reference_is_traceable_and_not_activated():
    path = ROOT / 'Greenhub/data/Pre-treatment/Feedstock/czubaszek_2023_lignocellulose_reference.csv'
    with path.open(encoding='utf-8-sig', errors='replace', newline='') as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 12
    assert {row['component'] for row in rows} == {'Crude fiber', 'Lignin', 'Hemicellulose', 'Cellulose'}
    assert {row['harvest_season'] for row in rows} == {'spring', 'summer', 'autumn'}
    assert all(row['evidence_class'] == 'B' for row in rows)
    assert all(row['activation_state'] == 'reference_only' for row in rows)
    assert all(row['doi'] == '10.3390/en16114488' for row in rows)
    assert all(row['analytical_replicates'] == '3' for row in rows)
    assert all(row['field_replicates'] == 'Not reported' for row in rows)
    assert all('not be added to cellulose, hemicellulose, or lignin' in row['limitations'] for row in rows if row['component'] == 'Crude fiber')


def test_scientific_data_csvs_have_no_active_legacy_d_quality_or_transferability_labels():
    data_root = ROOT / 'Greenhub/data'
    quality_columns = {
        'quality_class', 'data_class', 'evidence_class', 'confidence_class',
        'source_quality_class', 'source_quality', 'evidence_grade',
    }
    offenders = []
    legacy_transferability = []
    for path in data_root.rglob('*.csv'):
        with path.open(encoding='utf-8-sig', errors='replace', newline='') as source:
            for row_number, row in enumerate(csv.DictReader(source), start=2):
                for column in quality_columns.intersection(row):
                    if str(row.get(column, '')).strip().upper() == 'D':
                        offenders.append(f'{path.relative_to(data_root)}:{row_number}:{column}')
                transferability = str(row.get('transferability_class', '')).strip()
                if transferability.startswith('D_'):
                    legacy_transferability.append(f'{path.relative_to(data_root)}:{row_number}:transferability_class')
    json_offenders = []
    json_roots = (data_root, ROOT / 'biorefinery_platform')
    for json_root in json_roots:
        for path in json_root.rglob('*.json'):
            if 'results' in path.parts:
                continue
            payload = json.loads(path.read_text(encoding='utf-8'))

            def inspect(value, location=''):
                if isinstance(value, dict):
                    for key, nested in value.items():
                        nested_location = f'{location}.{key}' if location else key
                        if key in quality_columns and str(nested).strip().upper() == 'D':
                            json_offenders.append(f'{path.relative_to(ROOT)}:{nested_location}')
                        inspect(nested, nested_location)
                elif isinstance(value, list):
                    for index, nested in enumerate(value):
                        inspect(nested, f'{location}[{index}]')

            inspect(payload)
    assert offenders == []
    assert legacy_transferability == []
    assert json_offenders == []


def test_water_scrubber_recycle_input_has_direct_report_basis_and_runtime_traceability():
    path = ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json'
    records = json.loads(path.read_text(encoding='utf-8'))['records']
    record = next(row for row in records if row['record_id'] == 'phase6.water_scrubber_flash_gas_recycle_fraction')
    metadata = json.loads(record['additional_metadata_json'])
    assert record['value'] == '0.2'
    assert record['unit'] == 'fraction'
    assert record['quality_class'] == 'B'
    assert record['stable_identifier'] == 'SGC Rapport 2013:270'
    assert record['source_url'] == 'https://vav.griffel.net/filer/C_SGC2013-270.pdf'
    assert record['source_location'] == 'Section 2.4, p.39'
    assert 'reported lower endpoint' in record['basis']
    assert '0.20–0.30' in metadata['evidence_class']
    assert 'actual recycle is capped' in metadata['parameter_basis']
    assert 'WS_REC_001–002' in metadata['source_dataset']
    assert metadata['maturity_class'] == 'D4'
    assert metadata['source_record_ids'] == ['WS_REC_001', 'WS_REC_002']
    assert 'regression tests' in metadata['maturity_basis']

    registry_path = ROOT / 'Greenhub/data/advanced_model/canonical_parameter_registry.csv'
    with registry_path.open(encoding='utf-8-sig', newline='') as handle:
        parameter = next(row for row in csv.DictReader(handle)
                         if row['parameter_id'] == 'phase6.water_scrubber_flash_gas_recycle_fraction')
    assert parameter['normalized_value'] == '0.2'
    assert parameter['quality_class'] == 'B'
    assert parameter['source_row_id'] == 'Phase6Parameters:78'


def test_fair_input_records_preserve_scenario_specific_candidate_provenance():
    records = json.loads(
        (ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8')
    )['records']
    by_id = {row['record_id']: row for row in records}
    candidate_id = 'candidate:workbook:phase4:precipitation_temperature_C:PR3:All:90'
    candidate = by_id[candidate_id]
    metadata = json.loads(candidate['additional_metadata_json'])

    assert candidate['value'] == 60.0
    assert candidate['unit'] == 'degC'
    assert candidate['quality_class'] == 'C'
    assert candidate['stable_identifier'] == '10.1016/j.fufo.2022.100173'
    assert candidate['source_url'] == 'https://doi.org/10.1016/j.fufo.2022.100173'
    assert candidate['source_location'] == 'Sheet Phase4Parameters, row 90'
    assert metadata['scenario_ids'] == ['PR3']
    assert metadata['readiness_state'] == 'D4'
    assert 'residence time and heat duty are not reported' in metadata['warnings'][0]

    pH_candidate = by_id['candidate:workbook:phase4:target_pH:PR3:All:91']
    pH_metadata = json.loads(pH_candidate['additional_metadata_json'])
    assert pH_candidate['value'] == 5.0
    assert pH_candidate['unit'] == 'pH'
    assert pH_candidate['quality_class'] == 'C'
    assert pH_candidate['stable_identifier'] == '10.1016/j.fufo.2022.100173'
    assert pH_metadata['scenario_ids'] == ['PR3']
    assert pH_metadata['readiness_state'] == 'D4'
    assert 'acid demand' in pH_metadata['warnings'][0]

    ad1_rows = {
        'phase5.digester_temperature_c': (
            'candidate:workbook:phase5:digester_temperature_c:AD1:All:88',
            'B',
            '10.1016/j.biortech.2011.07.020',
        ),
        'phase5.digester_pH': (
            'candidate:workbook:phase5:digester_pH:AD1:All:89',
            'C',
            '10.1016/j.rser.2022.112092',
        ),
        'phase5.target_vs_olr_kg_m3_day': (
            'candidate:workbook:phase5:target_vs_olr_kg_m3_day:AD1:All:90',
            'B',
            '10.1016/j.rser.2022.112092',
        ),
    }
    for parameter_id, (record_id, quality, doi) in ad1_rows.items():
        record = by_id[record_id]
        metadata = json.loads(record['additional_metadata_json'])
        assert record['quality_class'] == quality
        assert record['stable_identifier'] == doi
        assert record['source_url'] == f'https://doi.org/{doi}'
        assert metadata['scenario_ids'] == ['AD1']
        assert metadata['readiness_state'] == 'D4'

    pH_ad1_metadata = json.loads(
        by_id[ad1_rows['phase5.digester_pH'][0]]['additional_metadata_json']
    )
    assert 'upper endpoint 7.2 is a proxy assumption' in ' '.join(
        pH_ad1_metadata['warnings']
    )

    # The shared all-route row remains a flagged structural fallback; it is
    # not overwritten or misrepresented as evidence for every technology.
    default = by_id['phase4.precipitation_temperature_C']
    pH_default = by_id['phase4.target_pH']
    assert default['quality_class'] == 'E'
    assert default['stable_identifier'] == ''
    assert pH_default['quality_class'] == 'E'
    assert pH_default['stable_identifier'] == ''


def test_workbook_candidate_hash_is_sheet_scoped_not_container_scoped(monkeypatch, tmp_path):
    import pandas as pd
    from Greenhub.parameters import loaders

    calls = []

    def read_sheet(path, *, sheet_name):
        calls.append(sheet_name)
        if sheet_name == 'Phase4Parameters':
            return pd.DataFrame([{'python_name': 'precipitation_temperature_C', 'value': 60.0}])
        if sheet_name in {'FAIR_Catalog', 'Master_Inputs'}:
            return pd.DataFrame([{'generated_snapshot': 'changed'}])
        raise AssertionError(f'Unexpected workbook sheet read for hash: {sheet_name}')

    monkeypatch.setattr(loaders.pd, 'read_excel', read_sheet)
    checksum = loaders._sha256_workbook_sheet(tmp_path / 'master.xlsx', 'Phase4Parameters')

    assert len(checksum) == 64
    assert calls == ['Phase4Parameters']
