"""Optional local MySQL loader; never called by ETL or tests. No remote hosts allowed."""
import os
import sqlite3
from contextlib import closing
from .etl import ROOT, FIELDS

def main():
    import pymysql
    host=os.environ.get('DEMO_MYSQL_HOST','127.0.0.1')
    if host not in ('127.0.0.1','localhost','::1'): raise ValueError('Only local sandbox MySQL is allowed')
    database=os.environ.get('DEMO_MYSQL_DATABASE','logistics_demo')
    if database!='logistics_demo': raise ValueError('Use dedicated logistics_demo database')
    source=ROOT/'runtime/demo.sqlite'
    if not source.exists(): raise ValueError('Run ETL first')
    with closing(sqlite3.connect(source)) as local: rows=local.execute('SELECT '+','.join(FIELDS)+' FROM charges').fetchall()
    conn=pymysql.connect(host=host,port=int(os.environ.get('DEMO_MYSQL_PORT','3306')),user=os.environ['DEMO_MYSQL_USER'],password=os.environ['DEMO_MYSQL_PASSWORD'],database=database,autocommit=False)
    try:
        with conn.cursor() as cursor:
            cursor.execute((ROOT/'sql/mysql_schema.sql').read_text())
            for row in rows:
                cursor.execute('SELECT '+','.join(FIELDS[:10])+' FROM charges WHERE provider=%s AND tracking_id=%s AND ship_date=%s AND category=%s',row[:4])
                old=cursor.fetchone()
                if old:
                    canonical=tuple(str(v) for v in old)
                    if canonical!=tuple(str(v) for v in row[:10]): raise ValueError('MySQL conflicting duplicate')
                else: cursor.execute('INSERT INTO charges ('+','.join(FIELDS)+') VALUES ('+','.join(['%s']*len(FIELDS))+')',row)
        conn.commit(); print('Local demo rows synchronized')
    except Exception: conn.rollback(); raise
    finally: conn.close()

if __name__=='__main__': main()
