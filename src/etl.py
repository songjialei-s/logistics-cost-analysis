"""Independent demo ETL: local files -> transactional SQLite -> BI CSV.
Changed inputs are rejected; use --rebuild to replace the local demo database.
"""
import argparse
import hashlib
import json
import sqlite3
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
FIELDS=['provider','tracking_id','ship_date','category','currency','amount_minor','fx_rate','amount_cny_minor','weight_kg','item_count','source_file','source_row','is_anomaly']
DDL="""CREATE TABLE IF NOT EXISTS charges (
provider TEXT NOT NULL, tracking_id TEXT NOT NULL, ship_date TEXT NOT NULL,
category TEXT NOT NULL, currency TEXT NOT NULL, amount_minor INTEGER NOT NULL,
fx_rate TEXT NOT NULL, amount_cny_minor INTEGER NOT NULL, weight_kg REAL NOT NULL,
item_count INTEGER NOT NULL, source_file TEXT NOT NULL, source_row INTEGER NOT NULL,
is_anomaly INTEGER NOT NULL, PRIMARY KEY(provider,tracking_id,ship_date,category));
CREATE TABLE IF NOT EXISTS processed_files (name TEXT PRIMARY KEY, fingerprint TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS rejected (source_file TEXT, source_row INTEGER, reason TEXT);"""

def number(value):
    result=Decimal(str(value).strip().replace(',',''))
    if not result.is_finite(): raise ValueError('non-finite number')
    return result

def normalize(raw,cfg,fx,source_row):
    def get(key): return raw[cfg['mapping'][key]]
    tracking=str(get('tracking_id')).strip()
    if not tracking or tracking.lower() in ('nan','none'): raise ValueError('missing tracking ID')
    day=pd.to_datetime(str(get('ship_date')).strip(),format=cfg['date_format'],errors='raise').strftime('%Y-%m-%d')
    if not fx['valid_from']<=day<=fx['valid_to']: raise ValueError('FX coverage missing')
    category=cfg['categories'].get(str(get('category')).strip())
    if not category: raise ValueError('unknown category')
    amount=number(get('amount')); weight=number(get('weight'))*Decimal(str(cfg['weight_factor']))
    units=number(get('item_count'))
    if amount<0 or weight<=0 or units<1 or units!=units.to_integral_value(): raise ValueError('invalid amount, weight or item count')
    rate=Decimal(fx['rates'][cfg['currency']])
    minor=int((amount*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    cny=int((Decimal(minor)*rate).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
    return (cfg['provider'],tracking,day,category,cfg['currency'],minor,str(rate),cny,round(float(weight),6),int(units),cfg['file'],source_row,int(cny>40000))

def run(root=ROOT,rebuild=False):
    configs=json.loads((root/'config/providers.json').read_text())
    fx=json.loads((root/'config/fx_rates.json').read_text())
    folder=root/'runtime'; folder.mkdir(exist_ok=True)
    database=folder/'demo.sqlite'
    con=sqlite3.connect(database)
    try:
        con.executescript(DDL)
        plans=[]
        for cfg in configs:
            file=root/'data/sample'/cfg['file']
            fingerprint=hashlib.sha256(file.read_bytes()+json.dumps([cfg,fx],sort_keys=True).encode()).hexdigest()
            old=con.execute('SELECT fingerprint FROM processed_files WHERE name=?',(cfg['file'],)).fetchone()
            if old and old[0]!=fingerprint and not rebuild: raise ValueError('Input/config changed: rerun with --rebuild for local demo only')
            if rebuild or not old: plans.append((cfg,file,fingerprint))
        stats=dict(files_processed=0,files_skipped=len(configs)-len(plans),inserted=0,duplicates=0,rejected=0)
        with con:
            if rebuild:
                for table in ('charges','processed_files','rejected'): con.execute(f'DELETE FROM {table}')
            for cfg,file,fingerprint in plans:
                frame=pd.read_excel(file,sheet_name=cfg['sheet'],header=cfg['header_row'],dtype=str)
                required=set(cfg['mapping'].values())
                if not required.issubset(frame.columns): raise ValueError('Required header missing')
                for index,row in frame.iterrows():
                    source_row=index+cfg['header_row']+2
                    try: record=normalize(row,cfg,fx,source_row)
                    except (ValueError,TypeError,KeyError,InvalidOperation):
                        con.execute('INSERT INTO rejected VALUES (?,?,?)',(cfg['file'],source_row,'invalid required field, category or FX coverage'))
                        stats['rejected']+=1; continue
                    key=record[:4]
                    old=con.execute('SELECT '+','.join(FIELDS)+' FROM charges WHERE provider=? AND tracking_id=? AND ship_date=? AND category=?',key).fetchone()
                    if old:
                        if old[:10]!=record[:10]: raise ValueError('Conflicting duplicate; no records committed')
                        stats['duplicates']+=1; continue
                    # Same parcel must have reliable, consistent units/weight across charge lines.
                    parcel=con.execute('SELECT item_count,weight_kg FROM charges WHERE provider=? AND tracking_id=? AND ship_date=?',record[:3]).fetchone()
                    if parcel and parcel!=(record[9],record[8]): raise ValueError('Inconsistent parcel attributes')
                    con.execute('INSERT INTO charges VALUES ('+','.join('?' for _ in FIELDS)+')',record)
                    stats['inserted']+=1
                con.execute('INSERT INTO processed_files VALUES (?,?)',(cfg['file'],fingerprint)); stats['files_processed']+=1
        output=root/'data/output'; output.mkdir(parents=True,exist_ok=True)
        frame=pd.read_sql_query('SELECT * FROM charges ORDER BY provider,ship_date,tracking_id,category',con)
        frame['amount']=frame['amount_minor']/100; frame['amount_cny']=frame['amount_cny_minor']/100
        frame.to_csv(output/'charges.csv',index=False,encoding='utf-8-sig')
        parcels=frame.groupby(['provider','tracking_id','ship_date'],as_index=False).agg(item_count=('item_count','first'),weight_kg=('weight_kg','first'))
        parcels.to_csv(output/'parcels.csv',index=False,encoding='utf-8-sig')
        pd.read_sql_query('SELECT * FROM rejected ORDER BY source_file,source_row',con).to_csv(output/'rejected.csv',index=False)
        stats.update(total_charges=len(frame),total_parcels=len(parcels),anomaly_lines=int(frame['is_anomaly'].sum()),persisted_rejected=con.execute('SELECT COUNT(*) FROM rejected').fetchone()[0])
        (output/'quality_report.json').write_text(json.dumps(stats,indent=2))
        return stats
    finally: con.close()

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--rebuild',action='store_true')
    print(json.dumps(run(rebuild=parser.parse_args().rebuild),indent=2))
