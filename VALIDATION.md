# Release validation — 0.1.0

Local validation on 27 October 2026: Linux x86_64, Python 3.12.14, isolated `venv` created without system-site-packages. Dependencies installed from the pinned `requirements.txt`; `pip check` reported no broken requirements. `requirements.lock.txt` captures the complete tested Linux/Python 3.12 environment; the direct dependency list is the recommended portable install route.

18 unit/integration tests passed. Tests cover formula/metric checks, historical/future data separation, risk and exposure constraints, MaxRet cross-check against a numerical optimizer, invalid-data rejection, activity-cost hand calculations, period partitioning and short subperiod behavior, CLI errors/version, and synthetic total/excess convention equivalence. The release demos produced 144 evaluation months after a 36-month warmup on 180 simulated months.

The one-command README example ran in the isolated environment and produced the bundled `examples/sample-report.html`. It contains synthetic results only. The standalone report embeds its figure and does not require external image files.

A GitHub Actions workflow is supplied for Python 3.11/3.12 on Ubuntu. It has NOT been run on the user's future GitHub repository. Windows/macOS commands are documented but those operating systems were not locally tested. AI-host installation compatibility varies; Python report generation is the verified interface.

This establishes basic functionality and computational consistency, not investment-model validity, superiority or live-trading readiness. No downloaded market data, course PDFs or private CV is included.

Independent README walkthrough succeeded from the public export with the isolated interpreter; all 18 tests passed there as well. The public file set was reviewed for private data and developer paths. The bundled sample HTML carries an explicit synthetic-data banner. Export uses an exact filename allowlist and SHA-256 manifest.
