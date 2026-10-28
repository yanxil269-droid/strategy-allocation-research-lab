# Strategy Allocation Research Lab

[中文说明](README.zh-CN.md) · [Synthetic sample report](examples/sample-report.html)

A Python research tool and reusable AI skill for evaluating monthly strategy-return datasets and producing a self-contained investment research report.

**Version 0.1.0 — research release.** Built by Yanxi Liu with AI-assisted implementation, extending Empirical Finance coursework. It implements seven allocation rules described in Appendix E of Della Corte and Riddiough (2025), *Currency Speculation*, plus a momentum-tilted extension. It is not affiliated with the authors and does not reproduce their published tables.

## What you get

- Compare equal, mean, inverse-volatility, Sharpe, Top-3 Sharpe, maximum-return and minimum-variance allocations, plus momentum tilt.
- Expanding historical estimates, a configurable risk target, Ledoit–Wolf covariance and common evaluation dates.
- Performance and drawdown statistics; five-year calendar subperiods; concentration and gross/net exposure.
- Incremental cost **scenarios**, based on changes in target exposures.
- A standalone HTML report with embedded chart, evidence summaries, assumptions and machine-readable CSVs.
- An optional separate FX two-pass pricing module for 30 test portfolios.

The report is generated deterministically from computed results. Running Python needs **no AI account, API key, paid data service or network access after dependency installation**. An AI host may help run the tool and add an evidence-grounded narrative; it is not needed to produce the report.

## Quick start: no programming required beyond commands

Download this project from GitHub using **Code → Download ZIP**, extract it, and open a terminal inside the extracted folder. Alternatively clone your chosen repository URL. Python 3.11 or 3.12 is recommended; the clean-environment release check uses Python 3.12 on Linux.

`requirements.lock.txt` records the fully resolved Linux/Python 3.12 validation environment; `requirements.txt` pins the tested direct dependencies and is the recommended starting point.

Create an isolated environment:

```sh
python -m venv .venv
```

Activate it on macOS/Linux:

```sh
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If activation is unavailable, use `.venv/bin/python` (macOS/Linux) or `.venv\Scripts\python.exe` (Windows) in place of `python` below. Some systems use `python3` instead of `python` for initial setup.

```sh
python -m pip install -r requirements.txt
python run_report.py examples/synthetic_excess.csv --strategies Quality Trend Defensive Value --unit decimal --return-type excess --fee-status unknown --out outputs/demo
```

Open **`outputs/demo/report.html`** in your browser. It works offline. Use a new output directory each time, for example `outputs/demo2`; existing output folders are deliberately not overwritten.

The sample is **synthetic**, not historical investment performance. See [examples/DATA.md](examples/DATA.md). Report text is currently English.

## Use your own data

Supply CSV or XLSX with a `date` column and at least three named strategy columns. One unique consecutive observation per calendar month; no missing/nonfinite values. Date formats: `YYYY-MM-DD` or numeric `YYYYMMDD`. All selected strategies must share units, currency basis and return convention. Prices, annualized yields, cumulative indexes and raw volatility levels are not strategy returns.

| date | Strategy_A | Strategy_B | Strategy_C |
|---|---:|---:|---:|
| 2020-01-31 | 0.012 | -0.006 | 0.008 |
| 2020-02-29 | -0.015 | 0.009 | 0.003 |

The table shows a schema only: two rows are not enough to run. Default warmup is 36 months; at least 39 total months are required. Short evaluation periods are possible but weak evidence. Monthly frequency is mandatory.

```sh
python run_report.py private_data/strategies.xlsx --sheet Returns --strategies Strategy_A Strategy_B Strategy_C --unit decimal --return-type excess --fee-status net --start 2000-01 --target 0.10 --warmup 36 --momentum 6 --cost-bps 0 5 10 --out outputs/my-research
```

For percentages use `--unit percent`: `1.2` means 1.2%; for decimals `0.012` means 1.2%. Units are never guessed. `--fee-status gross|net|unknown` records source-fee provenance; it does not calculate or strip source fees.

For **total** returns, provide a same-file monthly simple risk-free return column in the same units:

```sh
python run_report.py examples/synthetic_total.csv --strategies Quality Trend Defensive Value --unit decimal --return-type total --rf-column cash --fee-status unknown --out outputs/total-demo
```

The tool subtracts risk-free returns before allocation and reports excess-return statistics. It does not reconstruct funded total-account performance. Keep private inputs under `private_data/`, which is ignored by version control.

## Parameters and behavior

| Option | Default / meaning |
|---|---|
| `--strategies` | Required selected return-column names, at least three |
| `--unit` | Required `decimal` or `percent` |
| `--return-type` | Required `excess` or `total`; total needs `--rf-column` |
| `--fee-status` | Required `gross`, `net` or `unknown` |
| `--sheet` | Excel worksheet, default `All`; CSV ignores it |
| `--start`, `--end` | Optional inclusive calendar-month bounds |
| `--warmup` | 36 historical months; expanding thereafter |
| `--target` | 0.10 annual estimated volatility |
| `--momentum` | 6 months for the extension |
| `--cost-bps` | 0, 5, 10 bps activity-cost scenarios; zero always included |
| `--out` | Required **new** output folder |

Run `python run_report.py --help` for options. All eight methods run together; an undefined method or infeasible MaxRet stops the run rather than silently changing its definition. For a different research specification, explicitly change settings and document it. No leverage cap is imposed in Appendix E mode; negative weights and leverage are possible. With three inputs, TOP3 duplicates SR by construction.

## Report and outputs

| File | Contents |
|---|---|
| `report.html` | Self-contained chart, descriptive findings, tables and limitations |
| `summary.csv` | Common-period metrics and Sharpe differences versus equal allocation |
| `returns.csv`, `weights.csv` | Monthly excess returns and allocations/exposures |
| `periods.csv` | Five-year calendar blocks; partial edge blocks labeled; <12 months omitted |
| `exposures.csv` | Gross/net exposure and concentration |
| `cost_scenarios.csv` | Hypothetical extra-cost sensitivity |
| `activity_proxy.csv` | Target-exposure changes; `assumed_cost=0` in this zero-cost diagnostic file |
| `wealth.png`, `run.json` | Chart; settings, input hash, software versions and conventions |

Higher historical Sharpe is not automatically an investment recommendation. The tool prints per-method evidence for further research, not a statistically validated winner. Results may be unsuitable for live implementation.

## Use as an AI skill

`SKILL.md`, `scripts/`, `references/` and `agents/` form the skill. A compatible AI host must support local skills and Python/shell execution. Installing a skill does not install Python libraries: use the virtual environment above and tell the host which interpreter to use.

For a Codex project that scans `.agents/skills`, copy the complete skill content into `.agents/skills/analyze-fx-factors/`: include `SKILL.md`, `scripts`, `references`, `agents`, and `requirements.txt`. Avoid copying `.venv` or private inputs. Hosts with other skill directories/import workflows should use their own installation instructions. Simply uploading the text to a chat without file execution will not run the calculations.

Example request after installation:

> Use analyze-fx-factors to evaluate my CSV. The strategies are A, B and C; monthly decimal excess returns, source fees unknown. Use a 10% estimated volatility target and equal allocation as benchmark. Generate a report, explain subperiod stability and cost scenarios, and separate measurements from hypotheses. Use my project virtual-environment Python.

`references/installation.md` provides a platform-neutral checklist. Hosting the files on GitHub does not execute the tool or provide an online web service.

## Optional FX pricing module

The general report does not require FX factor data. `scripts/pricing.py` separately supports six sorts × P1–P5 (30 currency portfolios), DOL/CAR and optional log changes in global realized volatility. Those third-party workbooks are not bundled. See [references/pricing.md](references/pricing.md) for schema and inference limits.

```sh
python scripts/pricing.py --data-dir private_data --unit decimal --sheet All --grvol private_data/GRVOL.xlsx --grvol-sheet Sheet1 --out outputs/fx-pricing
```

`python scripts/appendix.py --help` exposes the allocation-only workflow; `scripts/analyze.py` is an earlier capped three-method prototype, retained for provenance and metric utilities. The release report uses `evaluate.py` and uncapped Appendix E rules.

## Methodology and limitations

- See [references/appendix.md](references/appendix.md) and [references/evaluation.md](references/evaluation.md) for formulas and definitions.
- Covariance and weights use only prior observations. This does not establish point-in-time source vintages or eliminate research selection bias.
- Estimated risk targets are not realized-risk guarantees. No full risk-factor attribution or parameter-sensitivity module is included yet.
- Cost proxy = sum of absolute changes in target exposures, including initial allocation from zero, without halving. It omits weight drift, underlying positions, closing liquidation, funding, execution and market impact. It is **not actual trade turnover or investable net return**. Extra-cost assumptions can overlap embedded source costs.
- Compounding excess returns forms a hypothetical index, not funded account wealth. Annual mean is arithmetic; ratios and drawdown conventions are explicitly defined in methodology references.
- No model superiority significance test, causal claim, or automatic buy/sell decision. Short samples, unstable covariance and normalization can fail; failures are reported.
- Data stays local; calculations contain no data upload or model API calls. Do not commit real data or private report outputs accidentally. Reports contain supplied column names and input paths; review them before sharing.

## Test and reproduce

```sh
python -m unittest discover -s scripts -p "test_*.py"
python examples/generate_demo.py
```

The CI workflow runs unit tests and both demo conventions. See [VALIDATION.md](VALIDATION.md) for what was actually verified locally. CI is provided but is not claimed to have run on your future GitHub repository.

## Attribution and license

MIT license for this project's code, instructions and synthetic examples; see [LICENSE](LICENSE). Third-party software retains its own license. The cited paper, publisher materials, Bloomberg data and course workbooks are **not** included or licensed by this project.

Reference: Della Corte, P. and Riddiough, S. (2025), *Currency Speculation*, Internet Appendix E, pages A-8–A-12 (version supplied during development). AI assisted implementation and testing; human review of assumptions and outputs remains necessary.
