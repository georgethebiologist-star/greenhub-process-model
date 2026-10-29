import csv
from datetime import datetime
from pathlib import Path
import openpyxl

src = Path(r'C:\Users\katrb\Downloads\261027 Nutriënten Grasmonsters VARTA.xlsx')
out = Path('Greenhub/data/Pre-treatment/Feedstock')
out.mkdir(parents=True, exist_ok=True)
wb = openpyxl.load_workbook(src, data_only=True, read_only=True)

def clean(v):
    return v.date().isoformat() if isinstance(v, datetime) else v

translation = {
    'Reterra bermgras N36': 'Reterra road-verge grass N36', 'Reterra mengselstroom bermgras': 'Reterra mixed-stream road-verge grass',
    'Greenhub gras heel': 'Greenhub whole grass', 'Greenhub gras verkleind': 'Greenhub size-reduced grass',
    'Reterra ruwgras': 'Reterra raw grass', 'Reterra bermgras geperst': 'Reterra pressed road-verge grass',
    'Sample 1 bewerkt gras': 'Sample 1 processed grass', 'Onbewerkt gras sample 1': 'Unprocessed grass sample 1',
    'Sample 1.2 bewerkt gras': 'Sample 1.2 processed grass', 'Onbewerkt gras': 'Unprocessed grass',
    'GREENHUB (grasmonster)': 'Greenhub (grass sample)', 'RETERRA (ruwgras)': 'Reterra (raw grass)', 'RETERRA (bermgras)': 'Reterra (road-verge grass)',
}

fiber_map = {
    'Droge stof (%)':'dry_matter_fraction','Kalium (K) (mmol/kg DS)':'potassium_mmol_kg_dm','Natrium (Na) (mmol/kg DS)':'sodium_mmol_kg_dm','Calcium (Ca) (mmol/kg DS)':'calcium_mmol_kg_dm','Magnesium (Mg) (mmol/kg DS)':'magnesium_mmol_kg_dm','Stikstof (N) (mmol/kg DS)':'nitrogen_mmol_kg_dm','Zwavel (S) (mmol/kg DS)':'sulfur_mmol_kg_dm','Fosfor (P) (mmol/kg DS)':'phosphorus_mmol_kg_dm','IJzer (Fe) (µmol/kg DS)':'iron_umol_kg_dm','Mangaan (Mn) (µmol/kg DS)':'manganese_umol_kg_dm','Zink (Zn) (µmol/kg DS)':'zinc_umol_kg_dm','Borium (B) (µmol/kg DS)':'boron_umol_kg_dm','Koper (Cu) (µmol/kg DS)':'copper_umol_kg_dm','Molybdeen (Mo) (µmol/kg DS)':'molybdenum_umol_kg_dm','Chloride (Cl) (mmol/kg DS)':'chloride_mmol_kg_dm','Stikstof (N) (g/kg DS)':'nitrogen_g_kg_dm','Zwavel (S) (g/kg DS)':'sulfur_g_kg_dm','Fosfor (P) (g/kg DS)':'phosphorus_g_kg_dm','Kalium (K) (g/kg DS)':'potassium_g_kg_dm','Calcium (Ca) (g/kg DS)':'calcium_g_kg_dm','Magnesium (Mg) (g/kg DS)':'magnesium_g_kg_dm','Natrium (Na)(g/kg DS)':'sodium_g_kg_dm','Chloride (Cl) (g/kg DS)':'chloride_g_kg_dm','IJzer (Fe) (mg/kg DS)':'iron_mg_kg_dm','Zink (Zn) (mg/kg DS)':'zinc_mg_kg_dm','Mangaan (Mn) (mg/kg DS)':'manganese_mg_kg_dm','Koper (Cu) (mg/kg DS)':'copper_mg_kg_dm','Borium (B) (mg/kg DS)':'boron_mg_kg_dm','Molybdeen (Mo) (mg/kg DS)':'molybdenum_mg_kg_dm','Droge stof eiwit (g/kg product)':'dry_matter_protein_g_kg_product','Ruw eiwit (g/kg product)':'crude_protein_g_kg_product','Ruw eiwit (g/kg DS)':'crude_protein_g_kg_dm'}
juice_map = {'Ammonium (NH4) (mg/l)':'ammonium_mg_l','Nitriet (NO2) (mg/l)':'nitrite_mg_l','Nitraat (NO3) (mg/l)':'nitrate_mg_l','Kalium (K) (mg/l)':'potassium_mg_l','Fosfaat (PO4) (mg/l)':'phosphate_mg_l','Chloride (Cl) (mg/l)':'chloride_mg_l','Sulfaat (SO4) (mg/l)':'sulfate_mg_l','Calcium (Ca) (mg/l)':'calcium_mg_l','Magnesium (Mg) (mg/l)':'magnesium_mg_l','Siliciumdioxide (SiO2) (mg/l)':'silicon_dioxide_mg_l','IJzer (Fe) (mg/l)':'iron_mg_l'}

def export(sheet, mapping, filename):
    ws = wb[sheet]; rows = list(ws.iter_rows(min_row=4, values_only=True)); headers = list(rows[0])
    fields = ['dataset_id','source_workbook','source_sheet','source_row','sample_number','sample_name_english','sample_name_original','sample_date'] + list(mapping.values())
    with (out/filename).open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for source_row, raw in enumerate(rows[1:], start=5):
            if not raw[0] or not raw[1]: continue
            row = {'dataset_id':'VARTA_2026_10_27','source_workbook':src.name,'source_sheet':sheet,'source_row':source_row,'sample_number':clean(raw[0]),'sample_name_original':clean(raw[1]),'sample_name_english':translation.get(str(raw[1]),str(raw[1])),'sample_date':clean(raw[2]) if sheet == 'Nutriënten Vezel' else ''}
            for original, english in mapping.items(): row[english] = clean(raw[headers.index(original)])
            w.writerow(row)

export('Nutriënten Vezel', fiber_map, 'varta_2026_grass_fiber_measurements.csv')
export('Nutriënten Sap', juice_map, 'varta_2026_grass_juice_measurements.csv')
with (out/'varta_2026_dataset_traceability.csv').open('w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['dataset_id','source_file','source_sheets','translation_policy','default_profile','activation_state','readiness_state','limitations']); w.writeheader(); w.writerow({'dataset_id':'VARTA_2026_10_27','source_file':src.name,'source_sheets':'Nutriënten Vezel; Nutriënten Sap','translation_policy':'English field names and translated sample labels; original Dutch labels retained; censored values retained verbatim.','default_profile':'Greenhub whole grass + Greenhub grass sample juice','activation_state':'active','readiness_state':'D4','limitations':'Measured laboratory profile for specific samples; not a universal seasonal average. No grass mass availability or operating-day data were supplied.'})
