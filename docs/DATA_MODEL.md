# Data Model

## Runs

`data/processed/runs.parquet` stores one row per historical run with source
dataset metadata, deterministic run IDs, raw and canonical model names, outcome,
cost, duration, token, timestamp, and trajectory coverage fields.

`data/processed/swe_agent_runs.parquet` uses the same core run schema and adds
SWE-agent-specific audit fields such as `exit_status`, generated patch hash, and
eval log hash. Full patches and logs are not duplicated into step rows.

## Steps

`data/processed/steps.parquet` stores one row per normalized trajectory event.
Non-tool messages and unexpected public-data structures are preserved as text.

`data/processed/swe_agent_steps.parquet` pairs SWE-agent assistant action turns
with the following environment/user observation.

## Signals

`step_signals.parquet`, `run_signals.parquet`, and `runs_with_rca.parquet`
contain rule-based operational signals. Public-facing labels use terms such as
`suspected_waste`, `rule_based_rca`, and `historical_early_stop_simulation`.
