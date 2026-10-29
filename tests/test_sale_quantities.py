from types import SimpleNamespace
from dataclasses import replace
import math
import pytest
import biosteam as bst
from Greenhub.application.sale_quantities import dry_gas_kmol, reference_volume_m3, seasonal_sale_quantities
from Greenhub.product_price_benchmarks import screening_tea_product_prices
from Greenhub.phase5_units import AnaerobicDigester, digestion_parameters_from_mapping


def test_atmospheric_gas_volume_uses_confirmed_reference_not_compressor_pressure():
    moles = dry_gas_kmol({'Methane': 16.04246, 'CarbonDioxide': 44.0095, 'Water': 100})
    assert moles == pytest.approx(2)
    volume = reference_volume_m3(moles)
    assert volume == pytest.approx(2 * 8314.462618 * 293.15 / 101325)
    assert volume > reference_volume_m3(moles, 273.15)
    assert dry_gas_kmol({'UnknownGas': 1}) is None
    assert dry_gas_kmol({'Methane': None}) is None


def test_seasonal_component_and_molar_inventory_integrates_once():
    gas = bst.Stream('sale_test_gas', Methane=1, CarbonDioxide=.1, Water=.2, units='kg/hr')
    salt = bst.Stream('sale_test_salt', AmmoniumSulfate=2, Water=8, units='kg/hr')
    p = bst.Stream('sale_test_p', Struvite=0, Water=3, units='kg/hr')
    model = SimpleNamespace(streams={'biomethane':gas,'ammonium_product':salt,'phosphorus_product':p})
    c, g = seasonal_sale_quantities(model, 10)
    assert c['ammonium_product']['AmmoniumSulfate'] == pytest.approx(20)
    assert c['phosphorus_product']['Struvite'] == 0
    assert g['biomethane'] == pytest.approx((1/16.04246+.1/44.0095)*10,rel=1e-4)
    gas.P *= 10
    assert seasonal_sale_quantities(model,10)[1] == g


def test_price_profile_uses_chemical_mass_and_declared_currency_conversion():
    prices=screening_tea_product_prices()
    assert prices['biomethane']['gas_reference_temperature_k'] == 293.15
    assert prices['biomethane']['gas_reference_pressure_pa'] == 101325
    assert prices['ammonium_product']['quantity_component'] == 'AmmoniumSulfate'
    assert prices['phosphorus_product']['quantity_component'] == 'Struvite'
    assert prices['ammonium_product']['value_eur_per_unit'] == pytest.approx(334.5*.92/1000)
    assert prices['phosphorus_product']['value_eur_per_unit'] == pytest.approx(600*.92/1000)


def test_dissolved_glucose_contributes_methane_without_solid_hydrolysis(phase5_values):
    values=dict(phase5_values,cellulose_hydrolysis_fraction=0,hemicellulose_hydrolysis_fraction=0)
    parameters=digestion_parameters_from_mapping(values,enabled=True)
    feed=bst.Stream('sugar_sale_feed',Water=90,Glucose=10,units='kg/hr')
    digester=AnaerobicDigester('R_sugar_sale',ins=feed,outs='sugar_sale_broth',parameters=parameters)
    digester.simulate()
    assert digester.consumed_kg_hr['Glucose']>0
    assert digester.generated_kg_hr['Methane']>0
    row=next(row for row in digester.hydrolysis_rows if row['component_id']=='Glucose')
    assert row['hydrolysis_fraction']==1
    assert digester.methane_cod_kg_hr<=digester.converted_cod_kg_hr


def test_sales_do_not_price_solution_water_or_empty_struvite_separator():
    from Greenhub.application.tea_service import _product_price_lines, TEAProjectBasis
    from Greenhub.tea_finance import TEAFinancialAssumptions
    profile=screening_tea_product_prices()
    measures={'annual_products_kg':{'ammonium_product':100,'phosphorus_product':50},
              'annual_product_components_kg':{'ammonium_product':{'AmmoniumSulfate':20},'phosphorus_product':{'Struvite':0}}}
    finance=TEAFinancialAssumptions(product_prices=profile,revenue_product_ids=('ammonium_product','phosphorus_product'))
    lines,missing,status,_=_product_price_lines(measures,TEAProjectBasis(),finance,(),model_type='empirical')
    assert not missing and status=='complete'
    by={line['product_id']:line for line in lines}
    assert by['ammonium_product']['quantity']==20
    assert by['ammonium_product']['annual_revenue_eur']==pytest.approx(20*.30774)
    assert by['phosphorus_product']['quantity']==0
    assert by['phosphorus_product']['annual_revenue_eur']==0
