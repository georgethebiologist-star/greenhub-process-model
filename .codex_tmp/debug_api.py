import sys, importlib.util
sys.path.insert(0,'.')
s=importlib.util.spec_from_file_location('t','tests/test_api_v1.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
from api.app import create_app
from pathlib import Path
app=create_app(Path('.codex_tmp/api_debug3'))
p=m.request_payload(resolution_mode='quasi_dynamic',selected_month='July',start_date='2026-01-01',end_date='2026-12-31',time_step='monthly',annual_biomass_target=30000000,biomass_schedule={'annual_available_biomass_tonnes':30000,'annual_processed_biomass_tonnes':30000,'collection_refinery_fraction':1.0,'feed_basis':'tonnes_per_year','feed_kg_per_hr':10000,'season_start':'2026-04-15','season_end':'2026-11-15','peak_date':'2026-07-31','spread_days':55,'active_months':list(range(1,13))})
print(m.invoke(app,'POST','/api/v1/simulations',p),flush=True)
