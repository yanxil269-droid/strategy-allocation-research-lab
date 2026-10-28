"""Section E allocation rules; monthly simple excess returns, annual risk units."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analyze import load,statistics

METHODS=('1/N','MEAN','VOL','SR','TOP3','MaxRet','MinVar','MomentumTilt')

def normalize(v):
    s=float(np.sum(v))
    if abs(s)<=1e-12*max(1.,float(np.abs(v).sum())):raise ValueError('Undefined signed weight normalization: near-zero denominator')
    return v/s

def max_return(mu,cov,target):
    n=len(mu);one=np.ones(n)
    ci=np.linalg.solve(cov,one);cm=np.linalg.solve(cov,mu)
    A=one@ci;g=ci/A;v=1/A
    if target**2 < v-1e-12:raise ValueError('MaxRet infeasible: target below fully invested minimum variance')
    if abs(target**2-v)<=1e-12:return g
    d=cm-ci*(one@cm/A);q=float(d@cov@d)
    if q<=1e-18:raise ValueError('MaxRet degenerate: expected returns provide no unique maximizing direction')
    return g+np.sqrt((target**2-v)/q)*d

def allocate(past,target=.10,momentum=6):
    mu=past.mean(axis=0)*12
    vol=past.std(axis=0,ddof=1)*np.sqrt(12)
    if (vol<=1e-12).any():raise ValueError('Zero volatility')
    cov=LedoitWolf().fit(past).covariance_*12
    if np.linalg.eigvalsh(cov).min()<=0:raise ValueError('Nonpositive covariance')
    sr=mu/vol;n=len(mu)
    top=np.argsort(-sr,kind='stable')[:min(3,n)]
    top_w=np.zeros(n);top_w[top]=normalize(sr[top])
    inv=normalize(1/vol)
    signal=np.prod(1+past[-momentum:],axis=0)-1
    tilt=normalize(inv*np.where(signal>0,1.5,np.where(signal<0,.5,1.)))
    gm=np.linalg.solve(cov,np.ones(n));gm=normalize(gm)
    raw={'1/N':np.ones(n)/n,'MEAN':normalize(mu),'VOL':inv,'SR':normalize(sr),
         'TOP3':top_w,'MinVar':gm,'MomentumTilt':tilt}
    exposures={k:w*target/np.sqrt(w@cov@w) for k,w in raw.items()}
    exposures['MaxRet']=max_return(mu,cov,target)
    raw['MaxRet']=exposures['MaxRet'].copy()
    return exposures,raw,cov

def run(x,warmup=36,target=.10,momentum=6):
    if not np.isfinite(target):raise ValueError('Target must be finite')
    if warmup<max(3,momentum) or momentum<1 or len(x)<=warmup+2 or target<=0:raise ValueError('Invalid parameters or insufficient history')
    a=x.to_numpy();rets=[];records=[]
    for t in range(warmup,len(x)):
        try:exposures,raw,cov=allocate(a[:t],target,momentum)
        except ValueError as exc:raise ValueError(f'{x.index[t]}: {exc}') from exc
        r={m:float(exposures[m]@a[t]) for m in METHODS}
        if min(r.values())<=-1:raise ValueError('Return <= -100%; compounded wealth model invalid')
        rets.append(r)
        for m in METHODS:
            w=exposures[m];risk=float(np.sqrt(w@cov@w))
            for i,f in enumerate(x.columns):records.append({'date':str(x.index[t]),'method':m,'factor':f,'raw_weight':raw[m][i],'exposure':w[i],'gross_exposure':np.abs(w).sum(),'net_exposure':w.sum(),'estimated_ann_vol':risk})
    return pd.DataFrame(rets,index=x.index[warmup:]),pd.DataFrame(records)

def main():
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--unit',required=True,choices=['decimal','percent'])
    p.add_argument('--sheet',default='All');p.add_argument('--start',default='1976-02');p.add_argument('--factors',nargs='+',default=['CAR','VAL','M1M'])
    p.add_argument('--warmup',type=int,default=36);p.add_argument('--target',type=float,default=.10);p.add_argument('--momentum',type=int,default=6);p.add_argument('--out',required=True)
    a=p.parse_args();x=load(a.input,a.sheet,a.factors,a.unit,a.start)
    r,w=run(x,a.warmup,a.target,a.momentum);stats={m:statistics(r[m].to_numpy()) for m in METHODS}
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    r.to_csv(out/'returns.csv',index_label='date');w.to_csv(out/'weights.csv',index=False);pd.DataFrame(stats).T.to_csv(out/'summary.csv',index_label='method')
    metadata=vars(a)|{'input_sha256':hashlib.sha256(Path(a.input).read_bytes()).hexdigest(),'evaluation_start':str(r.index[0]),'evaluation_end':str(r.index[-1]),'methods':list(METHODS),'statistics':stats,'covariance':'sklearn LedoitWolf MLE monthly covariance times 12; centered; sample sd for standalone Sharpe weighting','scope':'Section E rule implementation on user-selected factors; not replication of paper tables/universe','caps':'No leverage cap; signed allocations allowed; MomentumTilt is coursework extension'}
    (out/'run.json').write_text(json.dumps(metadata,indent=2,allow_nan=False))
    initial=pd.DataFrame([np.ones(len(METHODS))],columns=METHODS,index=[r.index[0]-1]);wealth=pd.concat([initial,(1+r).cumprod()]);wealth.index=wealth.index.to_timestamp('M')
    ax=wealth.plot(figsize=(11,6),title='Section E rules + coursework extension | excess-return index');ax.set_ylabel('Initial index = 1');ax.figure.tight_layout();ax.figure.savefig(out/'wealth.png',dpi=160);plt.close(ax.figure)
    lines=['# Appendix E allocation comparison',f'{r.index[0]} to {r.index[-1]}, {len(r)} months; '+', '.join(x.columns),
    'Seven Section E rules plus MomentumTilt extension. Expanding history starts with 36 months by default. Weights use only prior returns.',
    'Ledoit-Wolf covariance estimates annualized by 12. Annual target 10% by default, no leverage cap and no clipping of negative means/Sharpe ratios. Estimated risk hits target; realized risk need not.',
    'MaxRet enforces sum(weights)=1 and exact estimated risk target; infeasible targets raise an error rather than switching method.',
    'With only three input strategies TOP3 equals SR, not equal weighting. Paper tables use a different universe and end date; these results are not paper table replication.',
    'Monthly excess-return index is not funded total-return wealth. No incremental trading/financing costs. Check gross exposures before interpreting.',pd.DataFrame(stats).T.to_string()]
    (out/'report.md').write_text('\n\n'.join(lines));print(pd.DataFrame(stats).T.to_string())
if __name__=='__main__':main()
