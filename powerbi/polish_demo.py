"""Apply screenshot-review fixes to the independent demo only."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
BI=ROOT/'powerbi'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def lit(v):return {'expr':{'Literal':{'Value':v}}}
def color(v):return {'solid':{'color':lit("'"+v+"'")}}
def polish():
    model=BI/'LogisticsCostDemo/LogisticsCostDemo.SemanticModel/model.bim'
    m=load(model);ms=next(t for t in m['model']['tables'] if t['name']=='charges')['measures']
    expr="VAR Prior = [Previous Month Cost CNY] RETURN IF(NOT ISINSCOPE('Date'[Month]) || ISBLANK([Total Cost CNY]), BLANK(), DIVIDE([Total Cost CNY] - Prior, Prior))"
    next(x for x in ms if x['name']=='Cost MoM')['expression']=expr
    save(model,m)
    dax=BI/'measures.dax';s=dax.read_text(encoding='utf-8')
    s='\n'.join('Cost MoM = '+expr if l.startswith('Cost MoM = ') else l for l in s.splitlines())+'\n'
    dax.write_text(s,encoding='utf-8')
    pages=BI/'LogisticsCostDemo/LogisticsCostDemo.Report/definition/pages'
    for pp in pages.glob('*/page.json'):
        page=pp.parent.name
        for f in pp.parent.glob('visuals/*/visual.json'):
            d=load(f);v=d['visual'];vid=d['name'];pos=d['position']
            title=v.get('visualContainerObjects',{}).get('title',[{}])[0].get('properties',{})
            title.update({'fontColor':color('#334155'),'fontSize':lit('11D')})
            objs=v.setdefault('objects',{})
            if vid=='header':
                title['show']=lit('false')
            if v['visualType']=='slicer':
                pos.update({'y':64,'height':100})
                if vid!='date_filter':
                    objs['data']=[{'properties':{'mode':lit("'Dropdown'")}}]
                objs['header']=[{'properties':{'show':lit('false')}}]
            if v['visualType']=='card':
                pos.update({'y':180,'height':100})
                measure=v['query']['queryState']['Values']['projections'][0]['field']['Measure']['Property']
                precision='0L' if measure in ['Parcels','Items','Charge Lines','Rejected Rows All Data','Review Charge Lines'] else '2L'
                objs['labels']=[{'properties':{'labelDisplayUnits':lit('0D'),'labelPrecision':lit(precision),'fontSize':lit('28D'),'color':color('#172B4D')}}]
                objs['categoryLabels']=[{'properties':{'show':lit('false')}}]
            if page=='overview':
                if vid in ['monthly_cost','monthly_mom']:pos.update({'y':300,'height':270})
            if page=='structure':
                if vid in ['provider_cost','category_cost']:pos.update({'y':180,'height':300})
                if vid=='provider_table':pos.update({'y':500,'height':270})
                if vid=='structure_note':pos.update({'y':790,'height':95})
            if page=='quality':
                if vid=='charge_review':
                    pos.update({'y':300,'height':250})
                    title['text']=lit("'高费用待核查清单（单笔费用 > 400元）'")
                    d['filterConfig']={'filters':[{
                        'name':'review_only','type':'Categorical',
                        'field':{'Column':{'Expression':{'SourceRef':{'Entity':'charges'}},'Property':'is_anomaly'}},
                        'filter':{'Version':2,'From':[{'Name':'c','Entity':'charges','Type':0}],
                         'Where':[{'Condition':{'In':{'Expressions':[{'Column':{'Expression':{'SourceRef':{'Source':'c'}},'Property':'is_anomaly'}}],
                         'Values':[[{'Literal':{'Value':'1L'}}]]}}}]}}]}
                if vid in ['rejected_table','quality_note']:pos['y']=580
                if vid=='quality_note':
                    text='高费用标记仅用于核查，不代表错账或实际节省。上表默认只显示 is_anomaly=1。拒绝记录为全量快照，不随日期/服务商/类别筛选。原ETL另有重复与冲突检查。'
                    objs['general'][0]['properties']['paragraphs'][0]['textRuns'][0]['value']=text
            save(f,d)
    # Keep the manual page configuration synchronized with actual visual definitions.
    cfg=load(BI/'page_configuration.json')
    byid={(p.parent.parent.parent.name,p.parent.name):load(p) for p in pages.glob('*/visuals/*/visual.json')}
    for v in cfg['visuals']:
        d=byid[(v['page'],v['id'])];p=d['position'];v['position']=[p[k] for k in ['x','y','width','height']]
        if v['id']=='charge_review':v['title']='高费用待核查清单（单笔费用 > 400元）';v['filter']='charges[is_anomaly] = 1 (visual only)'
    save(BI/'page_configuration.json',cfg)
    for name in ['README.md','page_layout.md']:
        p=BI/name;s=p.read_text(encoding='utf-8')
        s=s.replace('第三页费用表保留全部有效费用，可将is_anomaly设为1（视觉对象筛选器）聚焦高费用，','第三页费用表已默认使用is_anomaly=1的视觉对象筛选器聚焦高费用，')
        s=s.replace('截图前建议设置该表is_anomaly=1，并在截图说明中记下日期/服务商/类别范围。','截图时确认该表仅显示500元的合成费用，并记录筛选范围。')
        s=s.replace('可对费用表施加is_anomaly=1的视觉对象筛选。','费用表默认施加is_anomaly=1视觉对象筛选。')
        p.write_text(s,encoding='utf-8')
if __name__=='__main__':polish();print('Applied screenshot review fixes; rendering needs Desktop recheck.')

