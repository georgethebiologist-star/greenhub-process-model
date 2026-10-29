import pandas as pd
p='Greenhub/data/greenhub_feed_inputs.xlsx'
for s in ['ModelControl','GrassAvailability','GrassMeasurements']:
    d=pd.read_excel(p,sheet_name=s)
    print('###',s)
    print(d.to_string(index=False))
