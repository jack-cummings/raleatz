import pandas as pd
from datetime import datetime

df = pd.read_excel('./sample.xlsx').head(50)
print(df.shape)

# Create Fiscal Year Ranges
# june to july for each year from 2002-2022
# FY1 = june to july 2022
FY_dict = {}
for x in range(2002,2023):
    year = str(x)
    start_dt = datetime.strptime(f'07/01/{year}', '%m/%d/%Y')
    end_dt = datetime.strptime(f'06/30/{str(x+1)}', '%m/%d/%Y')
    FY_dict[year] = [start_dt,end_dt]

def assignFiscalYear(date,ref_dict):
    date_ts = datetime.strptime(str(date), '%Y-%m-%d %H:%M:%S')
    for k,v in ref_dict.items():
        if v[0] <= date_ts <= v[1]:
            return k
        else:
            print('here')

df['FY'] = df['Created Date'].apply(lambda x: assignFiscalYear(x, FY_dict))
print('done')