# Installation contract

Use Python 3.11/3.12 and create a project-specific venv. Install requirements.txt with that venv's Python. Run the synthetic command from README first. No API keys are needed. Report generation runs locally without an AI host; AI invocation requires a host that can execute files and a selected interpreter with dependencies installed.

For a project-local Codex skill, put SKILL.md and its scripts/references/agents/requirements.txt together under .agents/skills/analyze-fx-factors. Do not copy a venv between computers. Other hosts may use different locations or installation tools; consult the host. Resolve bundled scripts relative to this SKILL.md, not relative to the caller's working directory. Input and output paths may be absolute.

The seven-rule model can stop for near-zero signed-weight denominators, singular risk estimates, infeasible MaxRet, insufficient history, or returns <= -100%. Do not silently drop the failing method. Explain it and discuss a separately labeled change in specification.

Public examples must be synthetic. Never bundle the researcher's uploaded PDFs, real workbooks, CV, phone/email, account keys, venv or reports with private inputs.
