# Two-pass pricing

Read six Portfolios_Net_{CAR,VAL,M1M,M3M,M6M,M1Y}.xlsx workbooks using only P1-P5, prefix names, and align strictly by calendar month with Factors_Net.xlsx DOL/CAR. Default All and explicit start 1976-02. Reject duplicates, internal gaps and nonfinite data; do not silently inner-join/drop. Keep raw uploads outside the skill repository.

Estimate full-sample time-series intercepts and constant betas, then OLS with cross-sectional intercept each month. Average monthly lambdas. Estimate the mean-lambda covariance using Bartlett HAC with lag floor(T**0.25), no prewhitening or finite-sample correction. Do not claim exact R parity: sandwich::NeweyWest defaults differ. This does not incorporate generated-regressor uncertainty or Shanken correction; refrain from definitive significance claims.

If supplied, global realized volatility must be documented positive levels in date/vol columns and cover the complete sample plus prior month. Take first log difference. Both models then use exactly the same dates. Do not substitute VOL factor returns, VIX, or a volatility proxy without explicit scope change. Missing GRVOL means extended model not run.

Export per-asset betas/alphas, monthly lambdas, average prices/SE/t, actual versus fitted mean returns, pricing errors, figure, input hashes and settings. Define R² across average returns of the 30 assets, not time-series variance. Report all prices in monthly decimals or explicitly convert to percentage points. Never interpret full-sample fitting as tradable predictive evidence.

Run scripts/test_pricing.py for known synthetic price recovery, asset-order invariance, rank deficiency and a direct HAC lag-zero calculation. Optional third analysis connecting Q1 exposures is out of scope.

The supplied GRVOL workbook uses Sheet1, unlike the All portfolio universe sheet. Use --grvol-sheet Sheet1 (default) independently of --sheet All. Align by calendar month, not exact trading-day dates. Include January 1976 levels to form February 1976 log changes. On supplied files both models span 600 months through January 2026. Checked against the submitted report: beta summaries, risk-price estimates and R² reproduce its rounding; HAC SE/t differ because current code does not prewhiten. Do not claim full statistical-output parity.
