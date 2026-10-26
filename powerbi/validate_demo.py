"""Validate fixed synthetic data, PBIP references and official PBIR JSON schemas."""
from pathlib import Path
import sys, json, csv, sqlite3, subprocess, os, re, urllib.request, urllib.parse, urllib.error, hashlib, warnings
ROOT=Path(__file__).resolve().parents[1]
BI=ROOT/'powerbi'
sys.path.insert(0, str(ROOT))
from src.demo_snapshot import verify_snapshot
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def readcsv(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def main():
    checks=[]
    demo=ROOT/'data/demo'
    charges=readcsv(demo/'charges.csv');parcels=readcsv(demo/'parcels.csv');rejected=readcsv(demo/'rejected.csv')
    cfg=load(ROOT/'config/providers.json');providers={c['provider']:c for c in cfg}
    rates=load(ROOT/'config/fx_rates.json')['rates']
    for r in charges:
        c=providers[r['provider']]
        idx=int(r['tracking_id'].split('-')[1])-1
        month=int(r['tracking_id'].split('-')[2]);n=int(r['tracking_id'].split('-')[3])
        assert cfg[idx]['provider']==r['provider']
        amt=(500 if idx==0 and month==3 and n==4 else 10+idx+month+n) if r['category']=='freight' else 2
        assert r['currency']==c['currency']
        assert int(r['amount_minor'])==amt*100
        assert float(r['fx_rate'])==float(rates[c['currency']])
        assert int(r['amount_cny_minor'])==round(amt*100*float(rates[c['currency']]))
        assert float(r['amount'])==amt and float(r['amount_cny'])==int(r['amount_cny_minor'])/100
        assert abs(float(r['weight_kg'])-(1+n*.2))<0.001
        assert int(r['source_row'])==c['header_row']+2+(month-1)*8+(n-1)*2+(r['category']=='handling')
    charge_by_key = {(r['provider'], r['tracking_id'], r['ship_date']): r for r in charges}
    for r in parcels:
        c = charge_by_key[(r['provider'], r['tracking_id'], r['ship_date'])]
        assert int(r['item_count']) == int(c['item_count'])
        assert abs(float(r['weight_kg']) - float(c['weight_kg'])) < 0.000001
    expected_rejects={(c['file'],c['header_row']+2+i,'invalid required field, category or FX coverage') for c in cfg for i in (25,26,27)}
    assert {(r['source_file'],int(r['source_row']),r['reason']) for r in rejected}==expected_rejects
    assert len(rejected)==18
    checks.append('all CSV values matched independent fictional fixture, including rejection traceability')
    man=verify_snapshot(demo)
    checks.append('snapshot UTF-8/LF bytes and SHA256 match manifest')
    con=sqlite3.connect(':memory:')
    con.execute('CREATE TABLE charges(provider TEXT, tracking_id TEXT, ship_date TEXT,category TEXT,amount_cny_minor INTEGER,item_count INTEGER,is_anomaly INTEGER)')
    con.executemany('INSERT INTO charges VALUES (?,?,?,?,?,?,?)',[(r['provider'],r['tracking_id'],r['ship_date'],r['category'],int(r['amount_cny_minor']),int(r['item_count']),int(r['is_anomaly'])) for r in charges])
    sql='\n'.join(l for l in (ROOT/'sql/analysis.sql').read_text(encoding='utf-8').splitlines() if not l.lstrip().startswith('--'))
    results=[con.execute(q).fetchall() for q in sql.split(';') if q.strip()]
    assert [x[1] for x in results[0]]==[2360,2488,3099]
    assert abs(results[3][0][0]-7179/72)<1e-10
    assert abs(results[3][0][1]-7179/144)<1e-10
    assert len(results[4])==1
    assert len(charges)==144 and len(parcels)==72
    assert sum(int(r['item_count']) for r in parcels)==144
    assert sum(int(r['amount_cny_minor']) for r in charges)==794700
    checks.append('five original SQL queries run against CSV-loaded in-memory SQLite; totals and freight rates match')
    modelpath=BI/'LogisticsCostDemo/LogisticsCostDemo.SemanticModel/model.bim'
    m=load(modelpath)['model'];tables={t['name']:t for t in m['tables']}
    assert set(tables)=={'Date','charges','parcels','rejected'}
    date_columns = tables['Date']['columns']
    returned_date = next(c for c in date_columns if c['name'] == 'Date')
    assert returned_date['type'] == 'calculatedTableColumn'
    assert returned_date['sourceColumn'] == '[Date]'
    for table in tables.values():
        calculated_partition = any(p['source']['type'] == 'calculated' for p in table['partitions'])
        for column in table['columns']:
            if calculated_partition and 'sourceColumn' in column:
                assert column.get('type') == 'calculatedTableColumn', (table['name'], column['name'])
            if column.get('isNameInferred'):
                assert column.get('type') == 'calculatedTableColumn'
    checks.append('calculated-table returned columns explicitly use calculatedTableColumn (Desktop error regression)')
    assert len(m['relationships'])==2
    for r in m['relationships']:
        for side in ['from','to']:
            assert r[side+'Table'] in tables
            assert r[side+'Column'] in {c['name'] for c in tables[r[side+'Table']]['columns']}
        assert r['fromCardinality']=='many' and r['toCardinality']=='one'
        assert r['crossFilteringBehavior']=='oneDirection'
    checks.append('relationship endpoints exist, one-to-many single-direction, rejected disconnected')
    # Validate visual bindings against model objects, including hidden trace fields.
    project=BI/'LogisticsCostDemo'
    report_root=project/'LogisticsCostDemo.Report'
    assert load(report_root/'definition.pbir')['version']=='4.0'
    assert load(report_root/'definition/version.json')['version']=='2.0.0'
    pages=load(report_root/'definition/pages/pages.json')
    assert pages['activePageName'] in pages['pageOrder']
    for page_id in pages['pageOrder']:
        page_path=report_root/'definition/pages'/page_id
        assert load(page_path/'page.json')['name']==page_id
        assert list((page_path/'visuals').glob('*/visual.json'))
    checks.append('PBIR content version 2.0.0 distinct from definition.pbir 4.0; active page resolves')
    visual_count=0
    for p in project.rglob('visual.json'):
        d=load(p);pos=d['position']
        assert pos['x']>=0 and pos['y']>=0 and pos['x']+pos['width']<=1280 and pos['y']+pos['height']<=900
        for role in d['visual'].get('query',{}).get('queryState',{}).values():
            for pr in role['projections']:
                f=pr['field'];kind=next(iter(f));v=f[kind];table=v['Expression']['SourceRef']['Entity']
                assert table in tables
                choices=tables[table].get('measures' if kind=='Measure' else 'columns',[])
                assert v['Property'] in {o['name'] for o in choices},(p,v)
        visual_count+=1
    mom = next(x for x in tables['charges']['measures'] if x['name']=='Cost MoM')
    assert "ISINSCOPE('Date'[Month])" in mom['expression']
    review=load(project/'LogisticsCostDemo.Report/definition/pages/quality/visuals/charge_review/visual.json')
    assert review['filterConfig']['filters'][0]['filter']['Where'][0]['Condition']['In']['Values']==[[{'Literal':{'Value':'1L'}}]]
    checks.append('MoM total suppressed; anomaly table has a visual-only is_anomaly=1 filter')
    checks.append(f'{visual_count} visuals: all fields/measures resolve and positions stay in canvas')
    # No external connectors or company-path values in generated model / Power Query.
    contents=modelpath.read_text(encoding='utf-8')
    for forbidden in ['MySQL.Database','Sql.Database','Web.Contents','192.168.','File.Contents("\\\\']:
        assert forbidden not in contents
    assert all('Csv.Document' in '\n'.join(t['partitions'][0]['source']['expression']) for t in tables.values() if t['name']!='Date')
    checks.append('generated model sources are local demo CSV only')
    schema_count=None
    if '--schemas' in sys.argv:
        sys.path.insert(0,str(ROOT/'runtime/powerbi_validation_deps'))
        import jsonschema
        warnings.filterwarnings('ignore',category=DeprecationWarning)
        cache=ROOT/'runtime/powerbi_schema_cache';cache.mkdir(parents=True,exist_ok=True)
        def retrieve(url):
            u=urllib.parse.urlparse(url)
            if u.netloc!='developer.microsoft.com':raise ValueError('Only official Microsoft schema host is allowed')
            p=cache/(hashlib.sha256(url.encode()).hexdigest()+'.json')
            if p.exists():return load(p)
            try:
                with urllib.request.urlopen(url,timeout=30) as res:d=json.load(res)
            except urllib.error.HTTPError as exc:
                if exc.code!=404 or 'schema.embedded.json' not in url: raise
                # Microsoft embedded schemas advertise a dotted $id; public endpoint uses a hyphen.
                with urllib.request.urlopen(url.replace('schema.embedded.json','schema-embedded.json'),timeout=30) as res:d=json.load(res)
            p.write_text(json.dumps(d),encoding='utf-8');return d
        schema_count=0
        for p in project.rglob('*'):
            if not p.is_file() or p.suffix not in ['.json','.pbir','.pbism']:continue
            d=load(p)
            if '$schema' not in d:continue
            schema=retrieve(d['$schema'])
            resolver=jsonschema.RefResolver(base_uri=d['$schema'],referrer=schema,handlers={'https':retrieve})
            errors=list(jsonschema.Draft7Validator(schema,resolver=resolver).iter_errors(d))
            if errors: raise AssertionError(str(p.relative_to(ROOT))+': '+' | '.join(e.message for e in errors[:3]))
            schema_count+=1
        checks.append(f'{schema_count} PBIR/project JSON documents pass official Microsoft JSON schemas')
    runtime=ROOT/'runtime/powerbi_test_temp';runtime.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env.update({'TEMP':str(runtime),'TMP':str(runtime),'PYTHONDONTWRITEBYTECODE':'1','PYTHONUTF8':'1'})
    result=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
    (BI/'pipeline_test_results.txt').write_text(result.stdout+result.stderr,encoding='utf-8')
    assert result.returncode==0,result.stderr
    checks.append('full automated suite passes in isolated temp directories inside demo runtime')
    report=load(BI/'validation_report.json');report['verified_checks']=checks
    report['official_schema_documents']=schema_count
    shot_status = load(BI/'screenshots/status.json')
    report['desktop_status'] = ('用户已确认完成最终Desktop验证；最终截图文件另行核查'
        if shot_status.get('user_reported_desktop_validation_complete')
        else '历史三页及主要数值已由截图验证；最新布局与交互待 Desktop 验证')
    report['user_reported_desktop_verified'] = bool(shot_status.get('user_reported_desktop_validation_complete'))
    (BI/'validation_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({'checks':checks,'desktop_status':'待 Desktop 验证'},ensure_ascii=False))
if __name__=='__main__':
    sys.dont_write_bytecode=True;sys.stdout.reconfigure(encoding='utf-8');main()
