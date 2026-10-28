"""Monthly simple excess-return portfolio research; no network calls."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

METHODS = ('equal', 'inverse_vol', 'momentum_tilt')

def load(path, sheet, factors, unit, start=None):
    df = pd.read_csv(path) if Path(path).suffix.lower() == '.csv' else pd.read_excel(path, sheet_name=sheet)
    if df.columns.duplicated().any() or len(set(factors)) != len(factors):
        raise ValueError('Duplicate column/factor names')
    if not {'date', *factors}.issubset(df.columns):
        raise ValueError('Required columns: date and selected factors')
    s = df['date'].astype(str).str.replace(r'\.0$', '', regex=True)
    dates = pd.to_datetime(s, format='%Y%m%d', errors='coerce')
    missing = dates.isna()
    dates.loc[missing] = pd.to_datetime(s[missing], errors='coerce')
    if dates.isna().any():
        raise ValueError('Invalid date')
    months = dates.dt.to_period('M')
    if months.duplicated().any():
        raise ValueError('Duplicate months')
    x = df[factors].apply(pd.to_numeric, errors='raise').astype(float)
    x.index = pd.PeriodIndex(months)
    x = x.sort_index()
    if start is not None:
        x = x.loc[pd.Period(start, freq='M'):]
    if len(x) == 0 or not x.index.equals(pd.period_range(x.index.min(), x.index.max(), freq='M')):
        raise ValueError('Empty input or missing calendar months')
    if not np.isfinite(x.to_numpy()).all():
        raise ValueError('Missing or infinite returns; no silent imputation')
    if unit == 'percent':
        x /= 100
    if (x <= -1).any().any():
        raise ValueError('Simple returns must exceed -100%')
    return x

def backtest(x, warmup=36, momentum=6, target=.10, cap=2.):
    if warmup < max(2, momentum) or momentum < 1 or len(x) <= warmup + 2 or target <= 0 or cap <= 0:
        raise ValueError('Invalid parameters or insufficient history')
    a = x.to_numpy()
    raw = np.full((len(x), 3), np.nan)
    scaled = raw.copy()
    records = []
    for t in range(warmup, len(x)):
        past = a[:t]
        vol = past.std(axis=0, ddof=1)
        if (vol <= 1e-12).any():
            raise ValueError('Zero historical factor volatility')
        inv = 1 / vol
        inv /= inv.sum()
        signal = np.prod(1 + past[-momentum:], axis=0) - 1
        tilt = inv * np.where(signal > 0, 1.5, np.where(signal < 0, .5, 1.))
        tilt /= tilt.sum()
        for j, w in enumerate((np.ones(a.shape[1]) / a.shape[1], inv, tilt)):
            raw[t, j] = w @ a[t]
            # Estimate today's portfolio risk using today's weights and only prior factor returns.
            est = np.std(past @ w, ddof=1) * np.sqrt(12)
            if est <= 1e-12:
                raise ValueError('Zero estimated portfolio volatility')
            leverage = min(target / est, cap)
            scaled[t, j] = raw[t, j] * leverage
            if scaled[t, j] <= -1:
                raise ValueError('Scaled return reaches -100%; wealth model invalid')
            for k, f in enumerate(x.columns):
                records.append({'date': str(x.index[t]), 'method': METHODS[j], 'factor': f,
                                'base_weight': float(w[k]), 'leverage': float(leverage),
                                'exposure': float(w[k] * leverage), 'estimated_ann_vol': float(est)})
    return pd.DataFrame(scaled[warmup:], index=x.index[warmup:], columns=METHODS), pd.DataFrame(records)

def statistics(r):
    wealth = np.r_[1., np.cumprod(1 + r)]
    dd = wealth / np.maximum.accumulate(wealth) - 1
    mean = float(np.mean(r)) * 12
    vol = float(np.std(r, ddof=1)) * np.sqrt(12)
    downside = float(np.sqrt(np.mean(np.minimum(r, 0) ** 2))) * np.sqrt(12)
    return {'months': len(r), 'ann_arithmetic_mean': mean, 'ann_vol': vol,
            'sharpe_arithmetic': mean / vol if vol > 0 else None,
            'sortino_annualized': mean / downside if downside > 0 else None,
            'max_drawdown': float(-dd.min()), 'terminal_excess_wealth': float(wealth[-1])}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('input')
    p.add_argument('--sheet', default='All')
    p.add_argument('--factors', nargs='+', default=['CAR', 'VAL', 'M1M'])
    p.add_argument('--unit', choices=['decimal','percent'], required=True)
    p.add_argument('--start', help='Explicit first included month, YYYY-MM')
    p.add_argument('--warmup', type=int, default=36)
    p.add_argument('--momentum', type=int, default=6)
    p.add_argument('--target', type=float, default=.10)
    p.add_argument('--cap', type=float, default=2.)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    x = load(args.input, args.sheet, args.factors, args.unit, args.start)
    returns, weights = backtest(x, args.warmup, args.momentum, args.target, args.cap)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)
    returns.to_csv(out / 'returns.csv', index_label='date')
    weights.to_csv(out / 'weights.csv', index=False)
    stats = {m: statistics(returns[m].to_numpy()) for m in METHODS}
    pd.DataFrame(stats).T.to_csv(out / 'summary.csv', index_label='method')
    meta = vars(args) | {'input_sha256': hashlib.sha256(Path(args.input).read_bytes()).hexdigest(),
                       'data_start': str(x.index[0]), 'data_end': str(x.index[-1]),
                       'evaluation_start': str(returns.index[0]), 'evaluation_end': str(returns.index[-1]),
                       'statistics': stats, 'numpy': np.__version__, 'pandas': pd.__version__}
    (out / 'run.json').write_text(json.dumps(meta, indent=2, allow_nan=False))
    wealth = (1 + returns).cumprod()
    # Include initial capital to show first-period losses correctly.
    initial = pd.DataFrame([[1., 1., 1.]], index=[returns.index[0]-1], columns=METHODS)
    wealth = pd.concat([initial, wealth])
    wealth.index = wealth.index.to_timestamp('M')
    ax = wealth.plot(figsize=(10,5), title='Hypothetical compounded excess-return index')
    ax.set_ylabel('Initial value = 1')
    ax.figure.tight_layout()
    ax.figure.savefig(out / 'wealth.png', dpi=160)
    plt.close(ax.figure)
    lines = ['# FX Factor Portfolio Lab: computational report',
             f'Evaluation: {returns.index[0]} to {returns.index[-1]}, {len(returns)} months.',
             'Three methods use the same evaluation dates. All weights and volatility estimates use prior observations only.',
             'Volatility targeting uses current weights applied to historical factor returns; this intentionally differs from the original R historical-strategy-return estimator.',
             f'Target annual volatility: {args.target:.1%}; maximum nonnegative leverage: {args.cap:g}. Realized volatility can differ.',
             'Returns are monthly simple excess returns. The wealth plot is a compounded excess-return index, not a funded total-return account.',
             'No incremental portfolio turnover costs, financing charges, market-impact or live execution model is included.',
             'Research extension of coursework; not verified replication of the Currency Speculation appendix.',
             '']
    for m, s in stats.items():
        lines.append(f"- {m}: annual arithmetic mean {s['ann_arithmetic_mean']:.2%}, volatility {s['ann_vol']:.2%}, maximum drawdown {s['max_drawdown']:.2%}.")
    (out / 'report.md').write_text('\n\n'.join(lines))
    print(json.dumps(stats, indent=2))

if __name__ == '__main__':
    main()
