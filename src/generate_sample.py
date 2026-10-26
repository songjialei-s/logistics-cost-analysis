"""Generate entirely fictional Excel bills. No external inputs or network calls."""
import json
from datetime import date
from pathlib import Path
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parents[1]
def generate(root=ROOT):
    configs=json.loads((root/'config/providers.json').read_text())
    folder=root/'data/sample'; folder.mkdir(parents=True,exist_ok=True)
    for index,cfg in enumerate(configs):
        wb=Workbook(); ws=wb.active; ws.title=cfg['sheet']
        for _ in range(cfg['header_row']): ws.append(['SYNTHETIC DATA - NOT REAL BUSINESS RECORDS'])
        ws.append(list(cfg['mapping'].values()))
        records=[]
        for month in (1,2,3):
            for parcel in range(1,5):
                tracking=f'DEMO-{index+1}-{month}-{parcel}'
                day=date(2026,month,parcel).strftime(cfg['date_format'])
                weight=round((1+parcel*.2)/cfg['weight_factor'],4)
                count=1+parcel%3
                for category,amount in [('DELIVERY',10+index+month+parcel),('HANDLING',2)]:
                    if index==0 and month==3 and parcel==4 and category=='DELIVERY': amount=500
                    records.append([tracking,day,str(amount),weight,count,category])
        # Duplicate, then three invalid records: missing ID, invalid date, missing amount.
        records.append(records[0].copy())
        for column,value in [(0,None),(1,'invalid-date'),(2,None)]:
            row=records[1].copy(); row[column]=value; records.append(row)
        for row in records: ws.append(row)
        ws.freeze_panes=f'A{cfg["header_row"]+2}'
        for col in ws.columns: ws.column_dimensions[col[0].column_letter].width=25
        wb.save(folder/cfg['file'])
    return len(configs)
if __name__=='__main__': print(f'Generated {generate()} synthetic bills')
