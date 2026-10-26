"""Execute the five local SQLite analysis queries without network access."""
import json
import sqlite3
from contextlib import closing
from .etl import ROOT

def main():
    source=ROOT/'runtime/demo.sqlite'
    if not source.exists(): raise SystemExit('Run python -m src.etl first')
    sql='\n'.join(line for line in (ROOT/'sql/analysis.sql').read_text().splitlines() if not line.lstrip().startswith('--'))
    with closing(sqlite3.connect(source)) as con:
        con.row_factory=sqlite3.Row
        for index,query in enumerate(sql.split(';'),1):
            if query.strip():
                print('Analysis',index)
                print(json.dumps([dict(row) for row in con.execute(query)],indent=2))
if __name__=='__main__': main()
