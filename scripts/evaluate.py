"""Reusable monthly strategy screening. No asset-specific risk model is imposed."""
import argparse,base64,hashlib,html,json
from importlib.metadata import version
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze import load,statistics
from appendix import run,METHODS

def activity_costs(returns,weights,bps):
    """Target-to-target activity proxy, not drift-adjusted trade turnover."""
    if bps<0 or not np.isfinite(bps):raise ValueError('Invalid cost')
    adjusted=returns.copy();records=[]
    for method in returns.columns:
        z=weights[weights.method==method].pivot(index='date',columns='factor',values='exposure')
        z.index=pd.PeriodIndex(z.index,freq='M');z=z.reindex(returns.index)
        if z.isna().any().any():raise ValueError('Weights/returns do not align')
        previous=z.shift(1);previous.iloc[0]=0
        activity=(z-previous).abs().sum(axis=1)
        charge=activity*bps/10000
        adjusted[method]=returns[method]-charge
        for date in returns.index:records.append({'date':str(date),'method':method,'activity_proxy':activity.loc[date],'assumed_cost':charge.loc[date],'cost_bps':bps})
    if (adjusted<=-1).any().any():raise ValueError('Cost scenario produces return <= -100%')
    return adjusted,pd.DataFrame(records)

def period_summary(r):
    rows=[]
    # Five-year calendar blocks, anchored at years divisible by five; edge blocks may be partial.
    bins=(r.index.year//5)*5
    for y in np.unique(bins):
        a=r.loc[bins==y]
        if len(a)<12:continue
        for m in a:
            rows.append({'period':f'{y}-{y+4}','observed_start':str(a.index[0]),'observed_end':str(a.index[-1]),'method':m,**statistics(a[m].to_numpy())})
    return pd.DataFrame(rows, columns=["period","observed_start","observed_end","method",*statistics(np.zeros(2)).keys()])

def exposure_summary(w):
    rows=[]
    for m,z in w.groupby('method',sort=False):
        z=z.pivot(index='date',columns='factor',values='exposure')
        gross=z.abs().sum(axis=1);net=z.sum(axis=1)
        concentration=z.abs().div(gross,axis=0).max(axis=1)
        rows.append({'method':m,'mean_gross_exposure':gross.mean(),'max_gross_exposure':gross.max(),'mean_net_exposure':net.mean(),'mean_largest_absolute_share':concentration.mean()})
    return pd.DataFrame(rows).set_index('method')

def main():
    p=argparse.ArgumentParser();p.add_argument('--version', action='version', version='Strategy Allocation Research Lab 0.1.0');p.add_argument('input');p.add_argument('--strategies',nargs='+',required=True)
    p.add_argument('--unit',required=True,choices=['decimal','percent']);p.add_argument('--return-type',required=True,choices=['excess','total'])
    p.add_argument('--rf-column',help='Same-file monthly simple risk-free return, same units as strategies; required for total returns')
    p.add_argument('--fee-status',required=True,choices=['gross','net','unknown'])
    p.add_argument('--sheet',default='All');p.add_argument('--start');p.add_argument('--end')
    p.add_argument('--warmup',type=int,default=36);p.add_argument('--momentum',type=int,default=6);p.add_argument('--target',type=float,default=.10)
    p.add_argument('--cost-bps',type=float,nargs='+',default=[0,5,10]);p.add_argument('--out',required=True)
    a=p.parse_args()
    if len(a.strategies)<3:raise ValueError('At least three strategies required for seven-rule comparison')
    if a.return_type=='total' and not a.rf_column:raise ValueError('Total returns require an aligned monthly risk-free return column')
    if a.rf_column in a.strategies:raise ValueError('Risk-free column cannot be a strategy')
    cols=a.strategies+([a.rf_column] if a.return_type=='total' else [])
    x=load(a.input,a.sheet,cols,a.unit,a.start)
    if a.end:x=x.loc[:pd.Period(a.end,freq='M')]
    if a.return_type=='total':x=x[a.strategies].sub(x[a.rf_column],axis=0)
    if (x<=-1).any().any():raise ValueError('Excess returns <= -100% cannot use compounded-index convention')
    r,w=run(x,a.warmup,a.target,a.momentum)
    baseline=pd.DataFrame({m:statistics(r[m].to_numpy()) for m in r}).T
    baseline['sharpe_difference_vs_equal']=baseline.sharpe_arithmetic-baseline.loc['1/N','sharpe_arithmetic']
    exposures=exposure_summary(w);periods=period_summary(r)
    costs=[];activities=None
    for bps in sorted(set([0.,*a.cost_bps])):
        adjusted,activity=activity_costs(r,w,bps)
        if bps==0:activities=activity
        for m in adjusted:costs.append({'method':m,'cost_bps':bps,**statistics(adjusted[m].to_numpy())})
    costs=pd.DataFrame(costs)
    findings=[]
    equal=baseline.loc['1/N']
    for m in r:
        if m=='1/N':continue
        delta=baseline.loc[m,'sharpe_difference_vs_equal']
        s=periods[periods.method==m].set_index('period').sharpe_arithmetic
        e=periods[periods.method=='1/N'].set_index('period').sharpe_arithmetic
        wins=int((s>e).sum())
        findings.append(f'{m}: historical Sharpe difference versus equal {delta:+.3f}; higher Sharpe in {wins}/{len(s)} observed calendar blocks; maximum gross exposure {exposures.loc[m,"max_gross_exposure"]:.2f}x. These are descriptive comparisons, not significance tests.')
    warnings=['Allocation rules use expanding prior data, Ledoit-Wolf covariance and no leverage cap. Net exposures after scaling need not equal one; negative positions are possible.',
    'Cost scenarios subtract bps times absolute change in target exposures, including opening from zero. This is an activity proxy: no weight drift, underlying turnover, spreads, financing or market-impact model. It is not actual net-of-cost performance.',
    f'Input fee status: {a.fee_status}. Additional costs can overlap costs already embedded in source data; interpret only as incremental sensitivity assumptions.',
    'All reported means, Sharpe and Sortino use excess returns. Wealth is a hypothetical compounded excess-return index, not a funded total-return account. Total inputs are converted by subtracting the supplied monthly risk-free series.',
    'The 10% risk target is estimated from past data; realized volatility can differ. Five-year calendar blocks include partial edge blocks; blocks below 12 observations are omitted. No automatic best-method selection or significance claim is made.',
    'No risk-factor attribution is performed in this version. Missing factor data is not replaced by a currency model. Parameter sensitivity and inference on performance differences are future extensions.']
    if len(a.strategies)==3:warnings.append('Exactly three strategies: TOP3 equals SR by construction.')
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    for name,d in [('summary',baseline),('exposures',exposures)]:d.to_csv(out/(name+'.csv'),index_label='method')
    periods.to_csv(out/'periods.csv',index=False);costs.to_csv(out/'cost_scenarios.csv',index=False)
    r.to_csv(out/'returns.csv',index_label='date');w.to_csv(out/'weights.csv',index=False);activities.to_csv(out/'activity_proxy.csv',index=False)
    meta=vars(a)|{'input_sha256':hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),'data_start':str(x.index[0]),'data_end':str(x.index[-1]),'evaluation_start':str(r.index[0]),'evaluation_end':str(r.index[-1]),'months':len(r),'benchmark':'1/N','warnings':warnings,'tool_version':'0.1.0','software_versions':{name:version(name) for name in ['numpy','pandas','scikit-learn','matplotlib','openpyxl']}}
    (out/'run.json').write_text(json.dumps(meta,indent=2,allow_nan=False))
    wealth=pd.concat([pd.DataFrame([np.ones(len(r.columns))],columns=r.columns,index=[r.index[0]-1]),(1+r).cumprod()]);wealth.index=wealth.index.to_timestamp('M')
    ax=wealth.plot(figsize=(11,6),title='Strategy allocation screening | excess-return index');ax.figure.tight_layout();ax.figure.savefig(out/'wealth.png',dpi=150);plt.close(ax.figure)
    pic=base64.b64encode((out/'wealth.png').read_bytes()).decode()
    doc='<!doctype html><meta charset="utf-8"><title>Strategy Research Report</title><style>body{font:15px/1.65 system-ui;max-width:1200px;margin:40px auto;padding:20px;color:#21384a}table{border-collapse:collapse;font-size:12px;width:100%;margin:20px 0}td,th{padding:7px;border:1px solid #ddd;text-align:right}th{background:#eaf1f5}img{max-width:100%}.scroll{overflow:auto}pre{white-space:pre-wrap}</style><h1>Strategy Allocation Research Report</h1>'
    doc+=f'<p>Evaluation: {r.index[0]}–{r.index[-1]}, {len(r)} months. Benchmark: equal allocation. Research screening; no automatic investment recommendation.</p>'
    doc+='<h2>Evidence for further research</h2><ul>'+''.join('<li>'+html.escape(t)+'</li>' for t in findings)+'</ul>'
    doc+='<h2>Historical performance (decimal returns)</h2>'+baseline.to_html(float_format=lambda z:f'{z:.4f}')+f'<img src="data:image/png;base64,{pic}" alt="Excess-return index">'
    for title,d,index in [('Exposure and concentration',exposures,True),('Calendar-block performance',periods,False),('Incremental activity-cost scenarios',costs,False)]:doc+='<h2>'+title+'</h2><div class="scroll">'+d.to_html(index=index,float_format=lambda z:f'{z:.4f}')+'</div>'
    doc+='<h2>Assumptions and limits</h2><ul>'+''.join('<li>'+html.escape(t)+'</li>' for t in warnings)+'</ul><h2>Audit settings</h2><pre>'+html.escape(json.dumps(meta,indent=2))+'</pre>'
    (out/'report.html').write_text(doc)
    print(baseline.round(4).to_string());print('Report:',out/'report.html')
if __name__=='__main__':main()
