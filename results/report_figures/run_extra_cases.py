"""Additional matched structural GreenHub runs for the PNG figure library."""
from __future__ import annotations
import csv
import json
from copy import deepcopy
from pathlib import Path
from Greenhub.application.decision_support_service import DecisionSupportService, default_configuration
from Greenhub.application.simulation_service import SimulationService

OUT = Path(__file__).resolve().parent
CASES = {
    "no_pef_F1": {"feed_preparation":"F1"},
    "nutrient_order_B": {"process_order":"B"},
    "calcium_phosphate_NR5": {"nutrient_recovery":"NR5"},
    "ion_exchange_NR6": {"nutrient_recovery":"NR6"},
    "potassium_NR7": {"nutrient_recovery":"NR7"},
    "membrane_BG3": {"biogas_upgrading":"BG3"},
    "psa_BG4": {"biogas_upgrading":"BG4"},
}

def main():
    service=DecisionSupportService(SimulationService(run_root=OUT/'source_runs'))
    rows=[]
    for name,overrides in CASES.items():
        config=deepcopy(default_configuration())
        config['simulation']['request_id']=name
        config['simulation']['scenarios'].update(overrides)
        try:
            result=service.evaluate(config)
            (OUT/f'{name}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
            annual=result['annual']
            row={'case_id':name,'run_id':result['run_id'],**config['simulation']['scenarios'],
                 'feed_kg_year':annual['feed_processed']['value'],
                 'electricity_kwh_year':annual['utilities']['electricity']['value'],
                 'heating_kwh_year':annual['utilities']['heating']['value'],
                 'cooling_kwh_year':annual['utilities']['cooling']['value'],
                 'mass_residual_kg_year':annual['balance']['process_mass_residual_kg'],
                 'warning_count':len(result['warnings']),
                 'installed_capex_eur':result['tea']['totals'].get('total_installed_capex_eur'),
                 'npv_eur':result['tea']['financial_kpis'].get('npv_eur'),
                 'climate_kg_co2e_year':result['lca']['totals'].get('climate_kg_co2e_per_year')}
            row.update({k+'_kg_year':v['value'] for k,v in annual['products'].items()})
            rows.append(row)
            print(name,'OK',flush=True)
        except Exception as e:
            rows.append({'case_id':name,'error':str(e)})
            print(name,'FAILED',str(e),flush=True)
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with (OUT/'extra_cases.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)

if __name__=='__main__':main()
