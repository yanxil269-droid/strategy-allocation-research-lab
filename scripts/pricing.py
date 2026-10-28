"""Full-sample two-pass FX pricing. Not a predictive backtest."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

GROUPS=('CAR','VAL','M1M','M3M','M6M','M1Y')

def read_months(path, sheet, cols, start, unit):
    d=pd.read_csv(path) if Path(path).suffix.lower()=='.csv' else pd.read_excel(path,sheet_name=sheet)
    if not {'date',*cols}.issubset(d.columns): raise ValueError(f'{Path(path).name}: missing columns {cols}')
    s=d.date.astype(str).str.replace(r'\.0$','',regex=True)
    date=pd.to_datetime(s,format='%Y%m%d',errors='coerce')
    mask=date.isna();date.loc[mask]=pd.to_datetime(s[mask],errors='coerce')
    if date.isna().any():raise ValueError('Invalid dates')
    idx=pd.PeriodIndex(date.dt.to_period('M'))
    if idx.duplicated().any():raise ValueError('Duplicate months')
    x=d[cols].apply(pd.to_numeric,errors='raise').astype(float);x.index=idx;x=x.sort_index()
    before=len(x);x=x.loc[pd.Period(start,freq='M'):]
    if len(x)==0:raise ValueError('Empty data')
    if not x.index.equals(pd.period_range(x.index[0],x.index[-1],freq='M')):raise ValueError('Missing months')
    if not np.isfinite(x.to_numpy()).all():raise ValueError('Nonfinite observations; resolve explicitly')
    if unit=='percent':x=x/100
    return x,{'filename':Path(path).name,'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'rows_before':before,'rows_retained':len(x),'start':str(x.index[0]),'end':str(x.index[-1])}

def hac_mean(lambdas,lag):
    a=np.asarray(lambdas);T=len(a)
    if not 0<=lag<T:raise ValueError('Invalid HAC lag')
    u=a-a.mean(axis=0)
    omega=u.T@u/T
    for j in range(1,lag+1):
        gamma=u[j:].T@u[:-j]/T
        omega+=(1-j/(lag+1))*(gamma+gamma.T)
    # Bartlett HAC, no prewhitening, no finite-sample multiplier.
    return omega/T

def fit_pricing(portfolios,factors,lag):
    if not portfolios.index.equals(factors.index):raise ValueError('Sample mismatch')
    R=portfolios.to_numpy();F=factors.to_numpy();T,N=R.shape;K=F.shape[1]
    X=np.column_stack([np.ones(T),F])
    if T<=K+2 or N<=K+1 or np.linalg.matrix_rank(X)<K+1:raise ValueError('Insufficient observations or rank deficiency')
    coef=np.linalg.lstsq(X,R,rcond=None)[0]
    betas=coef[1:].T
    Z=np.column_stack([np.ones(N),betas])
    if np.linalg.matrix_rank(Z)<K+1:raise ValueError('Cross-sectional design rank deficient')
    lambdas=np.linalg.lstsq(Z,R.T,rcond=None)[0].T
    cov=hac_mean(lambdas,lag);se=np.sqrt(np.maximum(np.diag(cov),0));mu=lambdas.mean(axis=0)
    t=np.divide(mu,se,out=np.full_like(mu,np.nan),where=se>0)
    actual=R.mean(axis=0);predicted=Z@mu;errors=actual-predicted
    denom=np.sum((actual-actual.mean())**2)
    r2=1-np.sum(errors**2)/denom if denom>0 else None
    # Independent mean-return cross-section must give the same point estimates.
    np.testing.assert_allclose(mu,np.linalg.lstsq(Z,actual,rcond=None)[0],rtol=1e-8,atol=1e-12)
    names=['intercept',*factors.columns]
    risk=pd.DataFrame({'term':names,'lambda_monthly_decimal':mu,'hac_se':se,'t_stat':t})
    loadings=pd.DataFrame(betas,index=portfolios.columns,columns=factors.columns)
    loadings.insert(0,'time_series_alpha',coef[0])
    pricing=pd.DataFrame({'actual_mean':actual,'fitted_mean':predicted,'pricing_error':errors},index=portfolios.columns)
    return risk,loadings,pricing,pd.DataFrame(lambdas,index=factors.index,columns=names),{'months':T,'portfolios':N,'cross_section_r2':r2,'pricing_rmse_monthly':float(np.sqrt(np.mean(errors**2))),'condition_number_cross_section':float(np.linalg.cond(Z))}

def main():
    p=argparse.ArgumentParser();p.add_argument('--data-dir',required=True);p.add_argument('--out',required=True)
    p.add_argument('--sheet',default='All');p.add_argument('--start',default='1976-02')
    p.add_argument('--unit',choices=['decimal','percent'],required=True)
    p.add_argument('--grvol',help='Optional file containing date and positive vol LEVELS; never a VOL factor return')
    p.add_argument('--grvol-sheet', default='Sheet1', help='Worksheet for GRVOL levels, independent of portfolio universe')
    p.add_argument('--lag',type=int)
    a=p.parse_args();root=Path(a.data_dir);audit=[]
    f,m=read_months(root/'Factors_Net.xlsx',a.sheet,['DOL','CAR'],a.start,a.unit);audit.append(m)
    blocks=[]
    for group in GROUPS:
        x,m=read_months(root/f'Portfolios_Net_{group}.xlsx',a.sheet,[f'P{i}' for i in range(1,6)],a.start,a.unit)
        audit.append(m)
        if not x.index.equals(f.index):raise ValueError('Portfolio/factor months differ; choose explicit common sample')
        blocks.append(x.add_prefix(group+'_'))
    portfolios=pd.concat(blocks,axis=1)
    models={'DOL_CAR':(portfolios,f)};status='Not run: global realized volatility level series is missing. VOL factor returns are not substituted.'
    if a.grvol:
        # Load the prior month as well to form the first log change; do not scale volatility levels.
        prior=str(pd.Period(a.start,freq='M')-1)
        v,m=read_months(a.grvol,a.grvol_sheet,['vol'],prior,'decimal');audit.append(m)
        if (v.vol<=0).any():raise ValueError('Volatility levels must be positive')
        diff=np.log(v.vol).diff().rename('dlnGRV')
        if not f.index.isin(diff.index).all() or diff.reindex(f.index).isna().any():raise ValueError('GRVOL must cover sample plus one prior month')
        extended=f.join(diff)
        models['DOL_CAR_dlnGRV']=(portfolios,extended);status='Run on identical months to the baseline.'
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    results={};texts=[]
    for name,(r,ff) in models.items():
        lag=a.lag if a.lag is not None else int(len(r)**.25)
        risk,beta,errors,lambdas,meta=fit_pricing(r,ff,lag);meta['hac_lag']=lag
        results[name]=meta
        risk.to_csv(out/f'{name}_risk_prices.csv',index=False)
        beta.to_csv(out/f'{name}_loadings.csv',index_label='portfolio')
        errors.to_csv(out/f'{name}_pricing_errors.csv',index_label='portfolio')
        lambdas.to_csv(out/f'{name}_monthly_lambdas.csv',index_label='date')
        fig,ax=plt.subplots(figsize=(7,6));ax.scatter(errors.fitted_mean*100,errors.actual_mean*100)
        lo=min(errors.actual_mean.min(),errors.fitted_mean.min())*100;hi=max(errors.actual_mean.max(),errors.fitted_mean.max())*100
        ax.plot([lo,hi],[lo,hi],'--',color='gray')
        for label,row in errors.iterrows():ax.annotate(label,(row.fitted_mean*100,row.actual_mean*100),fontsize=5)
        ax.set(xlabel='Fitted mean monthly excess return (%)',ylabel='Actual mean monthly excess return (%)',title=name+' | in-sample pricing')
        fig.tight_layout();fig.savefig(out/f'{name}_fit.png',dpi=170);plt.close(fig)
        texts += [f'## {name}',f"Sample {r.index[0]} to {r.index[-1]}; {len(r)} months; 30 portfolios; cross-sectional R² {meta['cross_section_r2']:.4f}; Bartlett HAC lag {lag}.",risk.to_string(index=False)]
    meta={'inputs':audit,'settings':vars(a),'models':results,'extended_status':status,'numpy':np.__version__,'pandas':pd.__version__}
    (out/'run.json').write_text(json.dumps(meta,indent=2,allow_nan=False))
    caveats=['# FX cross-sectional pricing: coursework extension',
    'Return-unit assumption: '+a.unit+'. Selected workbook universe: '+a.sheet+'. Explicit start '+a.start+' excludes the empty initial month in supplied returns.',
    'Six sorts x five portfolios = 30 test assets. First-pass OLS uses full-sample constant betas and an intercept; each month, second-pass OLS regresses 30 returns on those betas with a cross-sectional intercept.',
    'This is an in-sample pricing exercise, not an ex-ante backtest or a forecast. Risk prices and SEs are monthly decimals; multiply by 100 for percentage points. DOL is dollar; CAR is carry.',
    'HAC SEs use Bartlett weights, no prewhitening, no finite-sample adjustment. They do not correct generated-beta estimation error (no Shanken correction). t statistics are approximate; no joint model-pricing test is implemented. R sandwich::NeweyWest defaults can differ, so R parity is not asserted.',
    'Cross-sectional R² describes mean returns across these 30 assets, not monthly-return variance explained and not a formal test that a model is true.',
    'Extended model: '+status,*texts]
    (out/'report.md').write_text('\n\n'.join(caveats))
    print(json.dumps(results,indent=2));print(status)

if __name__=='__main__':main()
