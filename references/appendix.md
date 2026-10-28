# Appendix E definitions and implementation

Source: user-supplied article from pasquale.pdf, Currency Speculation, Internet Appendix E, printed pages A-8 to A-12. Supplied PDF includes the appendix; no online inference was used.

Begin monthly rebalancing after 36 historical months, then use expanding data through t-1 only. Estimate covariance with sklearn LedoitWolf centered MLE covariance, annualized by 12. Weighting means are arithmetic annual means; standalone standard deviations use ddof=1, whose common scaling cancels in normalized VOL/SR. Explicitly record these implementation conventions: the appendix does not specify a particular software implementation.

1/N: normalized ones. MEAN: means divided by their signed sum. VOL: inverse standard deviations normalized. SR: Sharpe ratios divided by their signed sum. TOP3: select three highest historical Sharpe ratios, then normalize their Sharpe ratios within the selected set; other weights zero. MinVar: inverse covariance times ones, normalized to sum one. Do not truncate negative means or ratios. Handle near-zero denominators as undefined and stop. Resolve ties stably by supplied column order. Fewer than three factors is a reduced-universe adaptation.

Scale each raw weight vector except MaxRet by target annual volatility / sqrt(w' covariance w). No leverage cap or long-only constraint appears in the appendix. Signed weights are permitted. Exposures after rescaling need not sum one.

MaxRet: maximize mu'w subject to w'covariance w=target² and 1'w=1. Let A=1'C^-1 1, g=C^-1 1/A, d=C^-1 mu-C^-1 1*(1'C^-1 mu/A). The maximum-return solution is g+sqrt((target²-1/A)/(d'Cd))*d. Do not rescale again. Target below minimum fully invested risk is infeasible. A degenerate mean direction is not uniquely optimized; stop explicitly.

MomentumTilt remains the separate coursework extension: inverse volatility weights times 1.5/0.5/1 for positive/negative/zero trailing six-month compounded return, normalized and risk-scaled using the same covariance.

Differences from original eight_methods.r: no clipping of negative means/SR; TOP3 selects by Sharpe and uses Sharpe weights; MaxRet is constrained optimization rather than selecting the highest mean; Ledoit-Wolf replaces plain/ridge covariance; risk scaling uses current weights/covariance rather than historical strategy returns. With three factors TOP3 equals SR, not 1/N.

Scope: default CAR, VAL, M1M universe is the coursework subset; sample ends January 2026. Do not claim paper table replication with its different universe/end date. No extra funding/turnover costs, point-in-time revisions or out-of-sample parameter selection analysis is modeled.

Tests: formula identities, target risk, MaxRet numerical optimizer cross-check and infeasibility rejection, future-data invariance and preservation of signed allocations.
