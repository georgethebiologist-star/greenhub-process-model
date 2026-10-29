import csv
from pathlib import Path
src=Path("Greenhub/data/tea/netherlands_industrial_product_price_benchmarks_raw.csv")
out=Path("Greenhub/data/tea/netherlands_industrial_product_price_benchmarks.csv")
with src.open(encoding="utf-8-sig", newline="") as h:
    rows=list(csv.reader(h))
header=rows[0]
cols=["product","industrial_price_low","industrial_price_high","screening_base","unit","price_basis_or_grade","market_status","price_date","geography","source_type","source_url","traceability_and_applicability","uncertainty_or_limitations"]
normalized=[]
for row in rows[1:]:
    if len(row)<11: raise ValueError(row)
    values=row[:11]+[" | ".join(row[11:])]
    normalized.append(values)
with out.open("w",encoding="utf-8",newline="") as h:
    w=csv.writer(h); w.writerow(cols); w.writerows(normalized)
print(len(normalized), out)
