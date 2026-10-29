import json, openpyxl
p = r'C:\Users\katrb\Downloads\261027 Nutriënten Grasmonsters VARTA.xlsx'
w = openpyxl.load_workbook(p, data_only=False, read_only=True)
print(json.dumps(w.sheetnames, ensure_ascii=False))
for name in w.sheetnames:
    ws = w[name]
    print('###', name, ws.max_row, ws.max_column)
    for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 15), values_only=True):
        print(json.dumps(row, ensure_ascii=False, default=str))
