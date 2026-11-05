import json
import csv
from pathlib import Path

import pytest
from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]


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
    assert any(row['relative_path'].endswith('greenhub_feed_inputs.xlsx') for row in rows)
    jrc = next(row for row in rows if row['relative_path'].endswith('JRC_electricity_emission_factors_2024.xlsx'))
    assert jrc['source_metadata_status'] == 'linked_to_local_source_record'
    assert '10.2905/JRC.4800KC0' in jrc['source_dois']
    assert 'CC BY 4.0' in jrc['license_or_rights']
    assert catalog['override_precedence'].startswith('Existing request/UI overrides')
    records = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8'))
    assert records['record_count'] == len(records['records'])
    assert not [row for row in records['records'] if row.get('quality_class') == 'D']
    b_records = [row for row in records['records'] if row.get('quality_class') == 'B']
    assert all(row.get('source_url') and row.get('uncertainty') for row in b_records)
    assert 'feed.Starch' in [row['record_id'] for row in b_records if not row.get('stable_identifier')]
    record_ids = {row['record_id'] for row in records['records']}
    assert 'feed.Water' in record_ids
    assert 'economics.grassUtilizationBonusEurPerT' in record_ids
    assert 'environment.electricityKgCo2eKwh' in record_ids
    assert any(value.startswith('TEA-') for value in record_ids)
    tea_records = [row for row in records['records'] if row['record_id'].startswith('TEA-')]
    assert len(tea_records) == 55
    tea_by_id = {row['record_id']: row for row in tea_records}
    assert tea_by_id['TEA-002']['quality_class'] == 'B'
    assert tea_by_id['TEA-015']['quality_class'] == 'C'
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
    assert all(row['quality_class'] == 'E' for row in storage_records)
    assert all('opt-in' in row['status'] for row in storage_records)
    r20 = next(row for row in storage_records if row['record_id'] == 'storage.reaction.R20')
    assert r20['stable_identifier'] == '10.1128/AEM.67.1.125-132.2001'
    r01 = next(row for row in storage_records if row['record_id'] == 'storage.reaction.R01')
    assert r01['stable_identifier'] == '10.1042/bj0291116'
    assert 'rice-straw' in r01['source_title']
    assert 'not a confidence interval' in r01['uncertainty']
    assert 'not a validated roadside-grass rate' in json.loads(r01['additional_metadata_json'])['rate_quality_note']
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


def test_active_grass_profile_has_no_class_d_and_flags_unmeasured_partition_as_e():
    profile = json.loads((ROOT / 'Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json').read_text(encoding='utf-8'))
    compounds = profile['compounds']
    assert all(row['data_class'] != 'D' for row in compounds.values())
    for component in ('SolubleProtein', 'SuspendedProtein'):
        row = compounds[component]
        assert row['data_class'] == 'E'
        assert row['source']['doi'] == '10.1021/acssuschemeng.2c00838'
        assert 'partition' in row['source']['basis'].lower()
        assert row['source']['uncertainty']
    for component in ('PersistentOrganics', 'Pesticides', 'HeavyMetals', 'Microplastics', 'PathogenIndicators'):
        assert compounds[component]['data_class'] == 'E'
        assert 'not a measured' in compounds[component]['source']['basis'].lower()


def test_literature_proxy_starch_is_class_b_with_basis_conversion_and_limitations():
    profile = json.loads((ROOT / 'Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json').read_text(encoding='utf-8'))
    starch = profile['compounds']['Starch']
    source = starch['source']
    assert starch['data_class'] == source['data_class'] == 'B'
    assert source['reported_value_percent_dry_matter'] == 1.88
    assert source['converted_value_g_per_kg_dry_matter'] == 18.8
    assert starch['wet_mass_fraction'] == pytest.approx(0.0188 * profile['dry_matter_fraction'])
    assert source['source_type'].startswith('peer-reviewed secondary literature')
    assert source['primary_reference'].startswith('Chornolata, L.P.; Horbachuk, T.V.; Liakhovchenko, I.A. (2018)')
    assert source['primary_reference_doi'] == ''
    assert 'not verified' in source['primary_reference_status']
    assert 'not measure starch' in source['source_location']
    assert source['applicability'].startswith('Low-transferability literature proxy')
    assert source['uncertainty']
    catalog = json.loads((ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.json').read_text(encoding='utf-8'))
    record = next(row for row in catalog['records'] if row['record_id'] == 'feed.Starch')
    assert record['source_title'] == source['source_title']
    assert record['source_url'] == source['url']
    assert record['source_location'] == source['source_location']
    assert record['geography'] == source['geography']
    assert str(record['reference_year']) == str(source['reference_year'])
    assert 'SRC-GUTU-2025' in record['additional_metadata_json']


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


def test_roadside_feed_and_ipcc_factor_metadata_are_linked_and_values_unchanged():
    profile = json.loads((ROOT / 'Greenhub/data/Pre-treatment/Feedstock/greenhub_feed_composition_defaults.json').read_text(encoding='utf-8'))
    compounds = profile['compounds']
    assert compounds['EntrappedSugars']['wet_mass_fraction'] == pytest.approx(0.010295999999999998)
    assert compounds['EntrappedSugars']['source']['doi'] == '10.1021/acssuschemeng.2c00838'
    assert compounds['EntrappedSugars']['source']['source_id'] == 'SRC-SMIT-2022'
    assert compounds['EntrappedSugars']['source']['uncertainty']
    for name, table in [('Cellulose', 'Table 4'), ('Hemicellulose', 'Table 5'), ('Lignin', 'Table 6')]:
        source = compounds[name]['source']
        assert source['doi'] == '10.12911/22998993/66249'
        assert source['source_id'] == 'SRC-TRUBA-2017'
        assert table in source['source_location']
        assert source['geography'] == 'Siedlce, Poland'
        assert source['uncertainty']
    ash = compounds['Ash']['source']
    assert compounds['Ash']['wet_mass_fraction'] == pytest.approx(0.025596999999999995)
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
    assert reaction['quality_class'] == 'E'
    assert reaction['stable_identifier'] == '10.1042/bj0291116'
    assert 'does not validate' in reaction['additional_metadata_json']

    with (ROOT / 'Greenhub/data/storage/source_register.csv').open(encoding='utf-8-sig', newline='') as handle:
        sources = list(csv.DictReader(handle))
    by_id = {row['source_id']: row for row in sources}
    grass_silage = by_id['SRC-GRASS-SILAGE-BUNKER-1997']
    assert grass_silage['doi_or_stable_identifier'] == '10.1111/j.1365-2494.1997.tb02348.x'
    assert '0.3% and 0.9%' in grass_silage['quality_notes']


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


def test_master_workbook_fair_snapshots_match_generated_catalogs():
    with (ROOT / 'Greenhub/data/fair_input_catalog/master_input_catalog.csv').open(encoding='utf-8-sig', newline='') as handle:
        catalog = list(csv.reader(handle))
    with (ROOT / 'Greenhub/data/fair_input_catalog/master_input_records.csv').open(encoding='utf-8-sig', newline='') as handle:
        records = list(csv.reader(handle))
    workbook = load_workbook(ROOT / 'Greenhub/data/greenhub_feed_inputs.xlsx', read_only=False, data_only=False)
    assert workbook.sheetnames[-2:] == ['FAIR_Catalog', 'Master_Inputs']
    catalog_sheet = workbook['FAIR_Catalog']
    master_sheet = workbook['Master_Inputs']
    assert catalog_sheet['A2'].value.endswith(f'{len(catalog) - 1} indexed source assets')
    assert master_sheet['A2'].value.endswith(f'{len(records) - 1} normalized records')
    assert [catalog_sheet.cell(6, column).value for column in range(1, len(catalog[0]) + 1)] == catalog[0]
    assert [master_sheet.cell(6, column).value for column in range(1, len(records[0]) + 1)] == records[0]
    assert catalog_sheet.max_row == 6 + len(catalog) - 1
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
    assert cassava['quality_class'] == ''
    assert json.loads(cassava['additional_metadata_json'])['transferability_class'] == 'D_low_transferability_reference_only'
    assert cassava['stable_identifier'] == ''
    assert 'No override introduced' in ryegrass['override_route']
