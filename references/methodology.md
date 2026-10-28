# Methodology and scope

## Provenance
Research extension of Yanxi Liu's Empirical Finance Coursework 2, Exercise 1. Existing R scripts informed the portfolio choices; the Python implementation is AI-assisted. The supplied Internet Appendix E has now been checked; use appendix.py and appendix.md for its seven rules. The capped analyze.py workflow below remains a separate prototype. Exercise 2 is implemented separately in scripts/pricing.py; see pricing.md.

## Data contract
Use a CSV or Excel sheet with date and explicitly selected factor columns. Dates may be YYYYMMDD or ISO. Require one observation per consecutive calendar month, finite numeric simple excess returns and explicit units. CAR means carry, not cumulative abnormal return. M1M is the supplied one-month momentum factor return, not a raw spot price. Do not deduct the risk-free rate twice. The supplied workbook is described by the user/report as net of source-level transaction costs; this does not cover additional combination-level trading costs.

## Portfolios
For month t, use only factor observations through t-1. Begin all methods after a common warmup (default 36 months).
- Equal: each selected factor receives 1/N.
- Inverse volatility: normalize 1 / sample historical volatility; this is not full equal-risk-contribution optimization.
- Momentum tilt: multiply inverse-volatility weights by 1.5, 0.5, or 1 for positive, negative, or zero trailing six-month compounded factor return, then normalize.
Estimate annual risk using the sample standard deviation of historical factor returns projected onto the current weights, multiplied by sqrt(12). Scale exposures by min(target / estimated risk, leverage cap). This differs intentionally from eight_methods.r, which estimates risk using the prior path of strategy returns. Log changes before comparing historical report figures. No full-sample risk scaling is allowed.

## Metrics
Annual arithmetic mean = 12 times mean monthly excess return. Annual volatility = sqrt(12) times sample monthly standard deviation. Sharpe = annual arithmetic mean / annual volatility. Sortino = annual arithmetic mean / (sqrt(12) times root mean square of negative monthly excess returns, using all months and zero threshold). Undefined ratios are null. Do not equate these with package defaults without checking conventions.
Compound 1 + monthly excess returns into a hypothetical excess-return index with initial capital 1 included in the drawdown calculation. Maximum drawdown is reported as a positive loss fraction. This is not an actual funded total-return wealth process.

## Limitations
No financing, incremental turnover costs, slippage, capacity model or parameter-selection correction. Input factors can already be long-short; nonnegative factor allocation does not mean underlying positions are long-only. Expanding estimates assume historical covariance is informative. Volatility targets are estimates, not guarantees. Dates alone do not establish data availability at the time; no point-in-time vintage verification has been performed.

## Checks and next extensions
Use scripts/test_analysis.py for future-data invariance, closed-form metric checks, exposure limits and bad-data rejection. Appendix definitions are implemented in appendix.py. TOP3 over three factors duplicates SR, not equal weighting. Keep Fama-MacBeth inference separate from predictive backtesting.
