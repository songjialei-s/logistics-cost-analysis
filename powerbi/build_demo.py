"""Build a wholly synthetic Power BI project. No company files or services are used."""
import csv, json, hashlib, shutil, sys
from pathlib import Path
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
ROOT=Path(__file__).resolve().parents[1]
BI=ROOT/'powerbi'
DEMO=ROOT/'data/demo'
PROJECT=BI/'LogisticsCostDemo'
def write(p,text):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(text,encoding='utf-8')
def dump(p,obj): write(p,json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def rows(p):
    with p.open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def build():
    charges=rows(ROOT/'data/output/charges.csv')
    parcels=rows(ROOT/'data/output/parcels.csv')
    rejected=rows(ROOT/'data/output/rejected.csv')
    cfg=json.loads((ROOT/'config/providers.json').read_text())
    fx=json.loads((ROOT/'config/fx_rates.json').read_text())
    expected={}
    for idx,c in enumerate(cfg):
        for month in (1,2,3):
            for n in range(1,5):
                tid=f'DEMO-{idx+1}-{month}-{n}'
                for cat,amt in [('freight',10+idx+month+n),('handling',2)]:
                    if idx==0 and month==3 and n==4 and cat=='freight': amt=500
                    minor=int((Decimal(amt)*100*Decimal(str(fx['rates'][c['currency']]))).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
                    expected[(c['provider'],tid,f'2026-{month:02}-{n:02}',cat)]=(minor,1+n%3)
    actual={}
    for r in charges:
        k=tuple(r[x] for x in ['provider','tracking_id','ship_date','category'])
        assert k not in actual,'Duplicate charge key'
        assert k in expected,'Not a deterministic synthetic fixture row'
        actual[k]=(int(r['amount_cny_minor']),int(r['item_count']))
        assert r['source_file'] in {c['file'] for c in cfg}
        assert int(r['is_anomaly'])==int(int(r['amount_cny_minor'])>40000)
        assert r['currency'] in fx['rates']
    assert actual==expected,'CSV differs from independent synthetic fixture calculation'
    keys=[tuple(r[x] for x in ['provider','tracking_id','ship_date']) for r in parcels]
    assert len(keys)==len(set(keys))==72
    assert {k[:3] for k in actual}==set(keys)
    for r in parcels:
        k=tuple(r[x] for x in ['provider','tracking_id','ship_date'])
        assert int(r['item_count'])==expected[k+('freight',)][1]
        assert all('|' not in r[x] for x in ['provider','tracking_id','ship_date'])
        assert float(r['weight_kg'])>0
    assert len(charges)==144 and len(rejected)==18
    assert sum(int(r['item_count']) for r in parcels)==144
    assert sum(v[0] for v in actual.values())==794700
    monthly=Counter()
    for k,v in actual.items(): monthly[k[2][:7]]+=v[0]
    assert dict(monthly)=={'2026-01':236000,'2026-02':248800,'2026-03':309900}
    DEMO.mkdir(parents=True,exist_ok=True)
    hashes={}
    for name in ['charges.csv','parcels.csv','rejected.csv']:
        src=ROOT/'data/output'/name
        shutil.copyfile(src,DEMO/name)
        hashes[name]=hashlib.sha256(src.read_bytes()).hexdigest()
    dump(DEMO/'manifest.json',{'synthetic_only':True,'source':'Independent deterministic project generator and existing ETL output','period':'2026-01 to 2026-03','sha256':hashes,'rows':{'charges':144,'parcels':72,'rejected':18},'expected':{'total_cost_cny':7947,'freight_cny':7179,'items':144,'anomaly_lines':1}})
    write(DEMO/'README.md',"""# Fixed synthetic snapshot
All rows originate from this repository's fictional generator. This is not masked business data.
charges: one charge category per provider / tracking_id / ship_date.
parcels: one row per provider / tracking_id / ship_date.
rejected: one rejected input row, with synthetic source filename and row number only.
Amounts used in BI are integer CNY cents; units come from parcels only.
manifest.json records hashes and fixture expectations.
Run the normal ETL separately; use powerbi/build_demo.py only when intentionally updating this fixed snapshot.
""")
    metrics=[
      ('Total Cost CNY','DIVIDE(SUM(charges[amount_cny_minor]), 100)','#,0.00','Selected charge cost, in fictional CNY.'),
      ('Freight CNY','CALCULATE([Total Cost CNY], KEEPFILTERS(charges[category] = "freight"))','#,0.00','Freight in current scope; handling-only selection gives blank.'),
      ('Parcels','COUNTROWS(parcels)','#,0','Date/provider filtered parcels; category does not reduce this denominator.'),
      ('Items','SUM(parcels[item_count])','#,0','Each parcel counted once. Not summed on charges.'),
      ('Cost per Parcel CNY','DIVIDE([Total Cost CNY], [Parcels])','#,0.00','Selected category cost per all date/provider selected parcels.'),
      ('Cost per Item CNY','DIVIDE([Total Cost CNY], [Items])','#,0.00','Selected category cost per all date/provider selected items.'),
      ('Freight per Parcel CNY','DIVIDE([Freight CNY], [Parcels])','#,0.00','Every fixture parcel has freight, matching SQL freight-bearing denominator.'),
      ('Freight per Item CNY','DIVIDE([Freight CNY], [Items])','#,0.00','Matches SQL for this fixture; see coverage check.'),
      ('Previous Month Cost CNY',"CALCULATE([Total Cost CNY], DATEADD('Date'[Date], -1, MONTH))",'#,0.00','Previous calendar month in current provider/category context.'),
      ('Cost MoM',"VAR Prior = [Previous Month Cost CNY] RETURN IF(ISBLANK([Total Cost CNY]), BLANK(), DIVIDE([Total Cost CNY] - Prior, Prior))",'0.0%','Blank for missing previous month or zero denominator.'),
      ('Category Share','DIVIDE([Total Cost CNY], CALCULATE([Total Cost CNY], REMOVEFILTERS(charges[category])))','0.0%','Share of all categories, retaining date/provider filters.'),
      ('Charge Lines','COUNTROWS(charges)','#,0','Accepted fee lines in selected scope.'),
      ('Review Charge Lines','COALESCE(CALCULATE(COUNTROWS(charges), KEEPFILTERS(charges[is_anomaly] = 1)), 0)','#,0','Charge >400 fictional CNY; not a proven billing error.'),
      ('Review Cost CNY','CALCULATE([Total Cost CNY], KEEPFILTERS(charges[is_anomaly] = 1))','#,0.00','Flagged charge amount, not demonstrated savings.'),
      ('Rejected Rows All Data','COUNTROWS(rejected)','#,0','Global rejected snapshot. No date/provider/category filtering.'),
      ('Freight Coverage Parcels','CALCULATE(DISTINCTCOUNT(charges[parcel_key]), REMOVEFILTERS(charges[category]), charges[category] = "freight")','#,0','Should equal Parcels under date/provider filters for this fixture.')
    ]
    write(BI/'measures.dax','// Create one measure at a time in the charges table. Already included in PBIP.\n\n'+'\n\n'.join(n+' = '+e for n,e,_,_ in metrics)+'\n')
    sm=PROJECT/'LogisticsCostDemo.SemanticModel'
    rp=PROJECT/'LogisticsCostDemo.Report'
    folder=str(DEMO).replace('\\','/')
    expr={'name':'DataFolder','kind':'m','expression':'"'+folder+'" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]','annotations':[{'name':'PBI_ResultType','value':'Text'}]}
    specs={
      'charges':[('provider','string'),('tracking_id','string'),('ship_date','dateTime'),('category','string'),('currency','string'),('amount_minor','int64'),('fx_rate','double'),('amount_cny_minor','int64'),('weight_kg','double'),('item_count','int64'),('source_file','string'),('source_row','int64'),('is_anomaly','int64'),('amount','double'),('amount_cny','double')],
      'parcels':[('provider','string'),('tracking_id','string'),('ship_date','dateTime'),('item_count','int64'),('weight_kg','double')],
      'rejected':[('source_file','string'),('source_row','int64'),('reason','string')]}
    model={'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','expressions':[expr],'tables':[],'relationships':[],'annotations':[{'name':'PBI_QueryOrder','value':json.dumps(['DataFolder','charges','parcels','rejected'])},{'name':'DemoStatus','value':'Synthetic only; pending Power BI Desktop validation'}]}
    queries={}
    for table,fields in specs.items():
        types={'string':'type text','dateTime':'type date','int64':'Int64.Type','double':'type number'}
        cast=', '.join('{"'+n+'", '+types[t]+'}' for n,t in fields)
        steps=['let',f'    Source = Csv.Document(File.Contents(DataFolder & "/{table}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),','    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),','    Typed = Table.TransformColumnTypes(Headers, {'+cast+'}, "en-US")']
        result='Typed'
        if table in ['charges','parcels']:
            steps[-1]+=','
            steps+=['    Keyed = Table.AddColumn(Typed, "parcel_key", each Text.Combine({[provider], [tracking_id], Date.ToText([ship_date], "yyyy-MM-dd")}, "|"), type text)']
            result='Keyed'
        steps+=['in','    '+result]
        query='\n'.join(steps);queries[table]=query
        cols=[]
        for n,t in fields:
            col={'name':n,'dataType':t,'sourceColumn':n,'summarizeBy':'none'}
            if n=='ship_date':col['formatString']='yyyy-MM-dd'
            if table=='charges' and n in ['item_count','weight_kg','amount','amount_cny','amount_minor','fx_rate']:col['isHidden']=True
            cols.append(col)
        if table in ['charges','parcels']:cols.append({'name':'parcel_key','dataType':'string','sourceColumn':'parcel_key','isHidden':True,'summarizeBy':'none'})
        tb={'name':table,'columns':cols,'partitions':[{'name':table,'mode':'import','source':{'type':'m','expression':steps}}]}
        if table=='charges':tb['measures']=[{'name':n,'expression':e,'formatString':f,'description':d} for n,e,f,d in metrics]
        model['tables'].append(tb)
        write(BI/'queries'/f'{table}.pq',query+'\n')
    model['tables'].append({'name':'Date','dataCategory':'Time','columns':[
        {'name':'Date','type':'calculatedTableColumn','isNameInferred':True,'dataType':'dateTime','sourceColumn':'[Date]','isKey':True,'formatString':'yyyy-MM-dd','summarizeBy':'none'},
        {'name':'Year','dataType':'int64','type':'calculated','expression':"YEAR('Date'[Date])",'summarizeBy':'none'},
        {'name':'Month','dataType':'string','type':'calculated','expression':"FORMAT('Date'[Date], \"yyyy-MM\")",'sortByColumn':'MonthIndex','summarizeBy':'none'},
        {'name':'MonthIndex','dataType':'int64','type':'calculated','expression':"YEAR('Date'[Date]) * 100 + MONTH('Date'[Date])",'isHidden':True,'summarizeBy':'none'}],
        'partitions':[{'name':'Date','mode':'import','source':{'type':'calculated','expression':'CALENDAR(DATE(2026,1,1), DATE(2026,12,31))'}}]})
    model['relationships']=[
      {'name':'Date_to_Parcels','fromTable':'parcels','fromColumn':'ship_date','fromCardinality':'many','toTable':'Date','toColumn':'Date','toCardinality':'one','crossFilteringBehavior':'oneDirection','isActive':True},
      {'name':'Parcels_to_Charges','fromTable':'charges','fromColumn':'parcel_key','fromCardinality':'many','toTable':'parcels','toColumn':'parcel_key','toCardinality':'one','crossFilteringBehavior':'oneDirection','isActive':True}]
    dump(sm/'model.bim',{'name':'LogisticsCostDemo','compatibilityLevel':1600,'model':model})
    base='https://developer.microsoft.com/json-schemas/fabric/item/'
    dump(sm/'definition.pbism',{'$schema':base+'semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{}})
    dump(PROJECT/'LogisticsCostDemo.pbip',{'version':'1.0','artifacts':[{'report':{'path':'LogisticsCostDemo.Report'}}],'settings':{'enableAutoRecovery':True}})
    dump(rp/'definition.pbir',{'$schema':base+'report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../LogisticsCostDemo.SemanticModel'}}})
    definition=rp/'definition'
    dump(definition/'version.json',{'$schema':base+'report/definition/versionMetadata/1.0.0/schema.json','version':'2.0.0'})
    dump(definition/'report.json',{'$schema':base+'report/definition/report/3.1.0/schema.json','themeCollection':{}})
    def field(table,name,measure=False):
        return {('Measure' if measure else 'Column'):{'Expression':{'SourceRef':{'Entity':table}},'Property':name}}
    def projection(table,name,measure=False):
        return {'field':field(table,name,measure),'queryRef':table+'.'+name,'nativeQueryRef':name}
    pages=[]
    layout=[]
    def page(pid,title):
        pages.append(pid);dest=definition/'pages'/pid
        dump(dest/'page.json',{'$schema':base+'report/definition/page/2.0.0/schema.json','name':pid,'displayName':title,'displayOption':'FitToPage','width':1280,'height':900})
        return dest
    def visual(dest,vid,kind,title,x,y,w,h,roles=None,text=None,sort=None):
        v={'visualType':kind,'drillFilterOtherVisuals':True}
        if roles:v['query']={'queryState':{role:{'projections':[projection(*f) for f in fs]} for role,fs in roles.items()}}
        if sort:v['query']['sortDefinition']={'sort':[{'field':field(*sort),'direction':'Ascending'}],'isDefaultSort':True}
        v['visualContainerObjects']={'title':[{'properties':{'show':{'expr':{'Literal':{'Value':'true'}}},'text':{'expr':{'Literal':{'Value':"'"+title.replace("'","''")+"'"}}}}}]}
        if text:v['objects']={'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':text,'textStyle':{'fontFamily':'Segoe UI','fontSize':'12pt'}}]}]}}]}
        obj={'$schema':base+'report/definition/visualContainer/2.1.0/schema.json','name':vid,'position':{'x':x,'y':y,'z':len(layout),'width':w,'height':h,'tabOrder':len(layout)},'visual':v}
        dump(dest/'visuals'/vid/'visual.json',obj)
        layout.append({'page':dest.name,'id':vid,'type':kind,'title':title,'roles':roles,'position':[x,y,w,h]})
    def filters(dest):
        visual(dest,'date_filter','slicer','日期 Date',24,62,390,64,{'Values':[('Date','Date',False)]})
        visual(dest,'provider_filter','slicer','服务商 Provider',434,62,390,64,{'Values':[('parcels','provider',False)]})
        visual(dest,'category_filter','slicer','费用类别 Category',844,62,410,64,{'Values':[('charges','category',False)]})
    def header(dest,title):
        visual(dest,'header','textbox',title,24,5,1230,52,text=title+'  |  SYNTHETIC DATA / 合成数据')
    def card(dest,vid,title,measure,x,y,w=230):
        visual(dest,vid,'card',title,x,y,w,100,{'Values':[('charges',measure,True)]})
    p=page('overview','01 成本总览');header(p,'物流成本分析 · 成本总览');filters(p)
    for i,(n,t) in enumerate([('Total Cost CNY','总费用 CNY'),('Parcels','包裹数'),('Items','商品件数'),('Freight per Parcel CNY','单票运费 CNY'),('Freight per Item CNY','单件运费 CNY')]):card(p,'kpi'+str(i),t,n,24+i*248,145)
    visual(p,'monthly_cost','clusteredColumnChart','月度费用 CNY',24,270,760,300,{'Category':[('Date','Month',False)],'Y':[('charges','Total Cost CNY',True)]},sort=('Date','Month',False))
    visual(p,'monthly_mom','lineChart','月度环比（首月空白）',804,270,450,300,{'Category':[('Date','Month',False)],'Y':[('charges','Cost MoM',True)]},sort=('Date','Month',False))
    visual(p,'monthly_table','tableEx','月度核对',24,590,760,215,{'Values':[('Date','Month',False),('charges','Total Cost CNY',True),('charges','Parcels',True),('charges','Items',True),('charges','Cost MoM',True)]})
    visual(p,'scope_note','textbox','口径',804,590,450,215,text='费用按合成汇率换算为人民币。件数只从包裹表统计。类别筛选影响费用，不缩小包裹/件数分母；仅选 handling 时运费卡片为空。没有收入或利润指标。')
    p=page('structure','02 费用结构');header(p,'物流成本分析 · 费用结构');filters(p)
    visual(p,'provider_cost','clusteredBarChart','服务商费用规模（不是服务质量排名）',24,150,710,320,{'Category':[('parcels','provider',False)],'Y':[('charges','Total Cost CNY',True)]})
    visual(p,'category_cost','donutChart','费用类别结构',754,150,500,320,{'Category':[('charges','category',False)],'Y':[('charges','Total Cost CNY',True)]})
    visual(p,'provider_table','tableEx','服务商与费用类别',24,490,1230,290,{'Values':[('parcels','provider',False),('charges','category',False),('charges','Total Cost CNY',True),('charges','Category Share',True)]})
    visual(p,'structure_note','textbox','分析提示',24,800,1230,65,text='金额差异受包裹规模、类别、重量和合成汇率影响。不能据此认定某服务商报价更差；无时效、线路或服务质量数据。类别占比保留日期与服务商范围，分母为所有费用类别。')
    p=page('quality','03 异常与质量核查');header(p,'物流成本分析 · 异常与质量核查');filters(p)
    card(p,'review_count','待核查费用行','Review Charge Lines',24,145,280)
    card(p,'review_amount','待核查金额 CNY','Review Cost CNY',324,145,280)
    card(p,'rejected_count','全量拒绝记录（不随筛选）','Rejected Rows All Data',624,145,330)
    card(p,'accepted_count','当前有效费用行','Charge Lines',975,145,279)
    visual(p,'charge_review','tableEx','费用核查：is_anomaly=1 表示单笔费用>400元',24,265,1230,275,{'Values':[('parcels','provider',False),('charges','tracking_id',False),('charges','ship_date',False),('charges','category',False),('charges','amount_cny',False),('charges','is_anomaly',False),('charges','source_file',False),('charges','source_row',False)]})
    visual(p,'rejected_table','tableEx','全量拒绝记录：仅合成来源及原因',24,560,760,235,{'Values':[('rejected','source_file',False),('rejected','source_row',False),('rejected','reason',False)]})
    visual(p,'quality_note','textbox','质量说明',804,560,450,270,text='高费用标记不代表错账或实际可节省金额。上方费用明细保留全部有效行，可筛 is_anomaly=1。拒绝表没有可靠日期/服务商字段，保持独立，不随筛选变化。ETL拒绝无效必填/日期/类别/汇率记录；另有重复与冲突校验。')
    dump(definition/'pages/pages.json',{'$schema':base+'report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':pages,'activePageName':pages[0]})
    dump(BI/'page_configuration.json',{'desktop_status':'待 Desktop 验证','canvas':[1280,900],'visuals':layout})
    write(BI/'metric_definitions.md','# Independent demo metric definitions\n\nStatus: DAX execution and rendering 待 Desktop 验证.\n\n|Measure|Definition|\n|---|---|\n'+'\n'.join('|'+n+'|'+d+'|' for n,_,_,d in metrics)+"""
\n## Scope and relationships
Date -> parcels -> charges, active single direction. Category only filters charges.
Freight metrics use KEEPFILTERS; selecting handling alone makes them blank.
No category filter changes parcel/item denominators. Every fixture parcel has freight;
check Freight Coverage Parcels = Parcels before applying SQL freight metrics to new data.
Rejected rows are global and disconnected; do not invent ship dates.
Months with no costs/previous month show blank growth, not zero.
There are no revenue, margin, service-quality or demonstrated-savings measures.
""")
    write(BI/'README.md',"""# Power BI 独立物流成本演示
状态：已生成 PBIP、模型、三页图表配置、DAX 和固定合成 CSV；**待 Desktop 验证**。
未生成二进制 PBIX，也没有经过 Desktop 刷新、渲染或截图验证。
所有实现独立编写；只读取本演示项目的数据，不依赖任何公司文件或服务。

## 1. 打开哪个文件
打开 powerbi/LogisticsCostDemo/LogisticsCostDemo.pbip。
必须保留旁边 .Report 和 .SemanticModel 目录。使用支持 PBIP/PBIR 的 Power BI Desktop。
项目自动生成格式依照微软公开 JSON schemas；schema通过不等于Desktop可用性保证。
若版本不支持PBIP，先更新Desktop；若仍打不开，按末尾手工方案重建。

## 2. 修改路径并载入
打开后进入 转换数据 -> 管理参数 -> DataFolder。
本机默认值指向本项目 data/demo。下载者改为自己克隆目录下 data/demo 的绝对路径，
建议用正斜杠，例如 D:/GitHubProjects/logistics-cost-analysis/data/demo。
参数不上传凭据；数据源仅为本地CSV。
关闭并应用，再刷新演示数据。PBIP不含数据缓存，首次打开必须载入。
不要选择本机其他业务文件或连接任何数据库。

## 3. 检查模型
模型视图确认：
Date[Date] 1 -> * parcels[ship_date]；
parcels[parcel_key] 1 -> * charges[parcel_key]；
均活动、单向。rejected独立无关系。
Date是2026完整日历；在表工具“标记为日期表”选择Date[Date]。
日期使用Date表，服务商使用parcels[provider]，费用类别使用charges[category]。
包裹键为 provider|tracking_id|yyyy-MM-dd；构建器已检查本样本没有分隔符冲突。
费用表的item_count隐藏，禁止把费用行的件数相加。

## 4. 核对结果
清除三个页面的所有筛选，查看第一页：
Total Cost CNY = 7,947.00；Parcels = 72；Items = 144。
Freight CNY = 7,179；Freight per Parcel CNY = 99.708333；
Freight per Item CNY = 49.854167。
月度：2026-01=2,360，02=2,488，03=3,099。
环比：1月空白；2月约5.4237%；3月约24.5579%。
质量页：144有效费用行、18全量拒绝记录、1待核查费用行、500元待核查金额。
点选一个服务商时费用与包裹一起变化；类别只影响费用，不改变包裹/件数分母。
仅选handling时Freight卡片空白。拒绝数据始终18，标题明确其不随筛选。
检查首月环比为空、跨月日期筛选、费用总数与Python/SQL一致。
在数据窗格选择度量值查看DAX，全部公式也在 measures.dax。

## 5. 页面与异常筛选
三个页面已配置，不代表已经人工检查布局。请检查是否有空白或报错图表、文本截断。
第三页费用表保留全部有效费用，可将is_anomaly设为1（视觉对象筛选器）聚焦高费用，
再核对source_file/source_row。异常仅是>400元的模拟规则，不代表实际错账。
截图前建议设置该表is_anomaly=1，并在截图说明中记下日期/服务商/类别范围。

## 6. 保存PBIX与截图
验证后 文件 -> 另存为 -> Power BI文件(.pbix)，保存到
powerbi/logistics_cost_demo.pbix。不要仅修改扩展名。
保留载入后的合成数据；关闭再打开，检查无须原机器目录即可查看缓存图表。
需要刷新时仍须设置DataFolder。
截图：各页调到适合页面，收起不必要窗格，使用Windows截图工具Win+Shift+S，
保存到powerbi/screenshots/01-overview.png、02-structure.png、03-quality.png。
这些应是真实Desktop截图；本项目不提供冒充报表的渲染图片。

## 7. GitHub提交
保留：src、sql、config、tests、requirements、data/sample、data/demo、
powerbi/LogisticsCostDemo完整项目、DAX/M/说明、经验证PBIX及实际截图。
不提交：runtime、.venv、.env、__pycache__、任何.pbi目录或本机缓存/凭据。
现有data/output被忽略，固定data/demo可提交。
发布前审查Changes/暂存区，仅在独立项目提交；本次没有init、commit、push或远程发布。
文档及README中的“待Desktop验证”应在实际操作通过后才更新。

## 8. 若PBIP打不开：手工兜底
新建空白PBIX。转换数据中新建文本参数DataFolder，指向data/demo。
建三个空白查询，分别命名charges、parcels、rejected；
把powerbi/queries中同名.pq粘到高级编辑器，关闭并应用。
新建日期表 Date = CALENDAR(DATE(2026,1,1),DATE(2026,12,31))；
增加 Month = FORMAT('Date'[Date], "yyyy-MM")、
MonthIndex = YEAR('Date'[Date])*100+MONTH('Date'[Date])，
Month按MonthIndex排序，标记日期表。
按第3节建立关系；按measures.dax逐个“新建度量值”，不要整段作为一个公式粘贴。
根据page_configuration.json和page_layout.md建立三页，用内置卡片、柱/条形图、
折线图、环形图、表格、文本框、日期/服务商/类别切片器。
核对所有第4节数值后再保存PBIX。
""")
    write(BI/'page_layout.md',"""# 三页配置与手工兜底
画布1280x900；页面顶部标题，第二行日期/服务商/类别切片器。使用内置视觉对象。
完整字段绑定、坐标、尺寸在page_configuration.json。

1. 成本总览：五张卡片（总费用、包裹数、件数、单票运费、单件运费）。
月度费用柱图：Date[Month]轴，Total Cost CNY值；
月度环比折线：Date[Month]轴，Cost MoM值，按月份升序。
下方月度核对表和分母/模拟汇率说明。

2. 费用结构：服务商费用条形图，类别费用环形图，
服务商/类别/金额/类别占比明细；不表述为服务质量排名。

3. 异常与质量：待核查费用行、待核查金额、全量拒绝行、有效费用行卡片；
费用明细含追踪号、标记、合成来源文件与行号。
可对费用表施加is_anomaly=1的视觉对象筛选。
拒绝记录表独立，明确全量且不随切片器变化；不根据异常标记声称真实降本。
所有页面的渲染、字体、布局、交叉筛选及DAX结果待Desktop验证。
""")
    write(BI/'screenshots/README.md','真实 Power BI Desktop 截图待用户完成，当前无截图。不使用伪造截图。\n')
    ign=ROOT/'.gitignore';txt=ign.read_text(encoding="utf-8")
    if '**/.pbi/' not in txt: write(ign,txt.rstrip()+'\n\n# Power BI local cache and settings\n**/.pbi/\n')
    rd=ROOT/'README.md';txt=rd.read_text(encoding="utf-8")
    txt=txt.replace('powerbi/README.md 提供模型与 DAX 建议；**尚未制作或验证 .pbix 报表**。','powerbi/README.md 提供独立 PBIP、模型、三页图表定义及操作步骤；**待 Power BI Desktop 验证，尚无二进制 PBIX 或实际截图**。')
    if '## Power BI 演示项目' not in txt:txt+='\\n'.replace('\\n','\n')+"""## Power BI 演示项目
打开 powerbi/LogisticsCostDemo/LogisticsCostDemo.pbip；
设置DataFolder到data/demo后载入合成CSV。详见powerbi/README.md。
项目文件静态检查与原ETL测试不能替代Desktop实测；当前仍待Desktop验证。
"""
    write(rd,txt)
    summary={'status':'待 Desktop 验证','checks':['synthetic fixture exact amount/item/key match','unique parcel and charge keys','all charge foreign keys matched','integer-cent totals and monthly totals','local CSV-only model','3 pages and 16 measures generated'],
      'expected':{'cost_cny':7947,'parcels':72,'items':144,'freight_cny':7179,'monthly_cny':[2360,2488,3099],'review_lines':1,'rejected_rows':18},
      'not_tested':['Power BI Desktop open','M execution in Desktop','DAX execution','visual rendering','interactive filtering','PBIX save']}
    dump(BI/'validation_report.json',summary)
    from polish_demo import polish
    polish()
    print(json.dumps(summary,ensure_ascii=False))
if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');build()

