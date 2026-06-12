# Codex Implementation Instructions: Lumni Open-Source Agent Efficiency Benchmark

## 0. Execution directive for Codex

You are operating inside the existing `agent-efficiency-benchmark` repository.

Do not return only a plan. Inspect the repository, create or modify the required files, run the commands, fix failures, and leave the repository in a working state.

Work incrementally and preserve existing working behavior. The current Terminal-Bench dataset has already been downloaded and normalized successfully. Do not delete raw data. Rebuild derived files only when their schema changes.

After every phase:

1. Run the relevant command.
2. Validate its output.
3. Run tests.
4. Fix errors before continuing.
5. Update documentation if implementation differs from this specification.

The final result must work locally without paid APIs, cloud services, model inference, managed databases, Docker, or GPUs.

---

# 1. Product goal

Build an open-source, reproducible agent-efficiency benchmark that analyzes existing public AI-agent trajectories and produces:

- Outcome benchmarks
- Cost and duration benchmarks
- Agent/model comparisons
- Tool-use statistics
- Failed-action detection
- Repeated-action detection
- Conservative suspected-waste detection
- Rule-based RCA summaries
- Historical early-stop simulations
- Manual-label evaluation
- A local public dashboard
- Stable JSON/CSV artifacts that Lumni can display in its production dashboard

The project is a public evidence and research layer for Lumni.

The open-source project should answer:

> Across public agent trajectories, where do agents fail, repeat work, waste time, and incur avoidable cost?

Lumni Cloud will later answer:

> Why is your private production agent failing, and how can the failure be prevented continuously?

---

# 2. Current repository state

Assume the repository currently contains or has generated:

```text
data/raw/terminalbench.parquet
data/processed/runs.parquet
data/processed/steps.parquet
src/ingestion/download_terminalbench.py
src/ingestion/inspect_dataset.py
src/normalization/normalize_terminalbench.py
```

Current observed Terminal-Bench snapshot:

```text
Raw runs:                    52,104
Runs with usable steps:      34,462
Runs without usable steps:   17,642
Normalized step events:      1,981,314
Raw model identifiers:       49
Latest completed run:        2026-03-05T22:54:39Z
```

Current normalized schemas:

## Runs

```text
run_id
task_name
agent
model
success
reward
duration_seconds
input_tokens
output_tokens
cache_tokens
cost_usd
trial_name
started_at
ended_at
step_count
tool_call_count
has_steps
has_cost
has_duration
```

## Steps

```text
run_id
task_name
step_index
tool_index
source
message
tool_name
command
observation
```

Known data-quality findings:

```text
29,506 source rows have blank trial_id values.
The current fallback IDs are unique but based on row position.
31,527 runs have positive cost.
20,340 runs have zero cost.
Approximately 237 cost values are non-finite/NaN.
Token coverage is approximately 66.1%.
Trajectory coverage is approximately 66.1%.
```

Do not hard-code these counts as permanent upstream facts. Record them in generated profiles and allow future dataset revisions to change them.

---

# 3. Hard constraints

## 3.1 Cost

The free version must have zero mandatory inference cost.

Allowed:

- Python
- Polars
- DuckDB
- Parquet
- Streamlit
- Plotly
- PyArrow
- Hugging Face Datasets
- Hugging Face Hub metadata API
- Pytest
- Ruff
- Standard local filesystem

Not allowed in this version:

- OpenAI API
- Anthropic API
- Google model API
- Bedrock inference
- Paid embeddings
- Vector databases
- Managed analytics databases
- Fresh Terminal-Bench model execution
- Fresh SWE-agent execution
- LLM-based labeling
- LLM-generated RCA
- Paid cloud deployment as a requirement

## 3.2 Truthfulness

Never describe heuristics as ground truth.

Use labels such as:

- `suspected_waste`
- `possible_missing_verification`
- `estimated_wasted_cost`
- `rule_based_rca`
- `historical_early_stop_simulation`
- `trajectory_backed`

Do not use labels such as:

- `confirmed_waste`
- `actual_avoidable_cost`
- `proven_root_cause`

unless a human label explicitly confirms them.

## 3.3 Comparisons

Do not claim a universal “best model.”

Always retain and display:

- Agent scaffold
- Model
- Provider suffix
- Task count
- Run count
- Trajectory coverage
- Cost coverage
- Dataset revision
- Snapshot cutoff
- Benchmark methodology version

Prefer `agent + model` comparisons. Model-only comparisons must be clearly marked as uncontrolled historical summaries.

## 3.4 Dataset scope

Implement Terminal-Bench first.

SWE-agent support is a later adapter and must not block v0.1. Do not merge Terminal-Bench and SWE-agent into one universal leaderboard.

---

# 4. Repository architecture

Use this structure while preserving any existing equivalent files:

```text
agent-efficiency-benchmark/
├── README.md
├── instructions.md
├── LICENSE
├── DATA_SOURCES.md
├── THIRD_PARTY_NOTICES.md
├── METHODOLOGY.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── Makefile
├── requirements.txt
├── .gitignore
├── pyproject.toml
│
├── data/
│   ├── raw/
│   │   ├── terminalbench.parquet
│   │   └── terminalbench_source.json
│   ├── processed/
│   │   ├── runs.parquet
│   │   ├── steps.parquet
│   │   ├── step_signals.parquet
│   │   ├── run_signals.parquet
│   │   ├── runs_with_rca.parquet
│   │   └── benchmark.duckdb
│   └── labels/
│       ├── rca_labels.csv
│       └── labeling_sample.csv
│
├── reports/
│   ├── manifest.json
│   ├── public_benchmark.json
│   ├── overview.json
│   ├── leaderboard_agent_model.csv
│   ├── leaderboard_agent.csv
│   ├── leaderboard_model_uncontrolled.csv
│   ├── outcome_comparison.csv
│   ├── task_difficulty.csv
│   ├── failure_patterns.csv
│   ├── early_stop_simulation.csv
│   ├── data_quality.json
│   └── examples/
│       └── selected_trajectories.json
│
├── src/
│   ├── __init__.py
│   ├── common/
│   │   ├── __init__.py
│   │   ├── constants.py
│   │   ├── hashing.py
│   │   ├── model_names.py
│   │   ├── numeric.py
│   │   ├── text.py
│   │   └── timestamps.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── download_terminalbench.py
│   │   ├── inspect_dataset.py
│   │   ├── check_dataset_update.py
│   │   └── model_coverage.py
│   ├── normalization/
│   │   ├── __init__.py
│   │   ├── normalize_terminalbench.py
│   │   └── validate_normalized.py
│   ├── signals/
│   │   ├── __init__.py
│   │   ├── patterns.py
│   │   ├── detect.py
│   │   ├── aggregate.py
│   │   └── rca.py
│   ├── benchmarks/
│   │   ├── __init__.py
│   │   ├── build.py
│   │   ├── metrics.py
│   │   ├── early_stopping.py
│   │   └── validate_reports.py
│   ├── labeling/
│   │   ├── __init__.py
│   │   ├── sample.py
│   │   └── evaluate.py
│   └── reports/
│       ├── __init__.py
│       ├── export.py
│       ├── schemas.py
│       └── sanitize.py
│
├── dashboard/
│   ├── app.py
│   ├── data.py
│   ├── formatting.py
│   └── pages/
│       ├── 1_Overview.py
│       ├── 2_Leaderboards.py
│       ├── 3_Failure_and_Waste.py
│       ├── 4_Trajectory_Explorer.py
│       ├── 5_Data_Quality.py
│       └── 6_Methodology.py
│
├── tests/
│   ├── fixtures/
│   │   └── terminalbench_sample.jsonl
│   ├── test_common.py
│   ├── test_normalization.py
│   ├── test_signals.py
│   ├── test_aggregation.py
│   ├── test_benchmarks.py
│   └── test_report_schema.py
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DATA_MODEL.md
│   ├── DATA_PROFILE.md
│   ├── LUMNI_INTEGRATION.md
│   └── LIMITATIONS.md
│
└── .github/
    └── workflows/
        └── ci.yml
```

Do not commit the large raw or processed Parquet files.

---

# 5. Dependencies

Use Python 3.10 or newer.

Update `requirements.txt` to include:

```text
datasets>=3.0
duckdb>=1.2
huggingface-hub>=0.27
orjson>=3.10
plotly>=5.24
polars>=1.20
pyarrow>=18.0
pydantic>=2.10
rich>=13.9
streamlit>=1.40
typer>=0.15
pytest>=8.3
ruff>=0.9
```

Create `pyproject.toml` with Ruff and pytest configuration. Do not introduce a build system that breaks direct script execution.

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]

[tool.ruff]
line-length = 88
target-version = "py310"
```

---

# 6. Git ignore rules

Ensure `.gitignore` includes:

```gitignore
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.DS_Store

data/raw/*
data/processed/*
!data/raw/.gitkeep
!data/processed/.gitkeep

reports/*
!reports/.gitkeep

.streamlit/secrets.toml
```

Keep `data/labels/*.csv` tracked only if it contains manually created labels safe for publication.

---

# 7. Dataset ingestion

## 7.1 Terminal-Bench downloader

Preserve the existing downloader behavior and add source revision metadata.

Dataset ID:

```text
yoonholee/terminalbench-trajectories
```

The downloader must:

1. Download the `train` split.
2. Save it to `data/raw/terminalbench.parquet`.
3. Query Hugging Face dataset metadata.
4. Save `data/raw/terminalbench_source.json`.
5. Include dataset ID, revision SHA, last modified time, download time, row count, columns, and local file size.
6. Support `--force`.
7. Refuse to overwrite an existing file without `--force`.
8. Print output paths.

## 7.2 Dataset update check

Implement:

```bash
python -m src.ingestion.check_dataset_update
```

It must compare the saved revision with the current remote revision and print:

```text
UP_TO_DATE
UPDATE_AVAILABLE
NO_LOCAL_REVISION
```

Exit codes:

```text
0 = up to date
2 = update available
3 = no local revision
1 = unexpected error
```

Do not download automatically.

## 7.3 Inspection

Implement:

```bash
python -m src.ingestion.inspect_dataset
```

Report:

- Total rows
- Raw schema
- Unique tasks, agents, and models
- Non-empty trajectory coverage
- Cost field coverage
- Positive cost coverage
- Zero cost count
- Missing/non-finite cost count
- Duration coverage
- Token coverage
- Earliest and latest valid timestamps
- Top agent/model combinations
- Duplicate and blank identifier counts

Do not calculate trajectory coverage using only `steps.is_not_null()`. Parse JSON and require a non-empty list.

## 7.4 Model coverage

Implement:

```bash
python -m src.ingestion.model_coverage \
  --model gpt-5.5 \
  --model opus-4-7 \
  --model opus-4-6
```

Show exact matches, run counts, agent combinations, latest run, and snapshot cutoff. This checks the dataset, not provider API availability.

---

# 8. Shared normalization utilities

## 8.1 Text conversion

`to_text(value)` must preserve strings, serialize dictionaries/lists/tuples as deterministic JSON, convert numbers/booleans to strings, and never crash on unexpected public data.

## 8.2 Numeric conversion

`to_float(value)` must convert numeric values while rejecting blank values, NaN, and positive/negative infinity. `to_int(value)` should behave similarly.

## 8.3 Timestamps

Convert blank strings to null before parsing. Retain raw and parsed timestamp columns.

## 8.4 Model names

Retain:

```text
model_raw
model
```

Canonicalization may normalize capitalization and punctuation-only duplicates. Do not merge distinct provider endpoints without explicit evidence. Keep a documented alias map and tests.

## 8.5 Deterministic run IDs

Use non-blank source `trial_id`:

```text
terminalbench:trial:<trial-id>
```

For missing IDs, hash stable identifying fields:

```text
trial_name
task_name
agent
model_raw
started_at_raw
ended_at_raw
reward
steps
```

Format:

```text
terminalbench:derived:<first-24-sha256-characters>
```

Handle exact duplicates with `:duplicate-2`, and add `run_id_source` plus `source_row_number`.

---

# 9. Final normalized schemas

## 9.1 Runs

```text
run_id: String
run_id_source: String
source_dataset: String
source_revision: String
source_row_number: Int64
task_name: String
agent: String
model_raw: String
model: String
success: Boolean
reward: Int64
duration_seconds: Float64
input_tokens: Float64
output_tokens: Float64
cache_tokens: Float64
cost_usd: Float64
cost_status: String
trial_name: String
started_at_raw: String
ended_at_raw: String
started_at: timezone-aware Datetime
ended_at: timezone-aware Datetime
step_count: Int64
tool_call_count: Int64
has_steps: Boolean
has_cost: Boolean
has_positive_cost: Boolean
has_duration: Boolean
has_tokens: Boolean
```

`cost_status` values:

```text
positive
zero
missing
```

Do not silently classify zero as missing.

## 9.2 Steps

```text
run_id: String
task_name: String
step_index: Int64
tool_index: Int64
source: String
message: String
tool_name: String
command: String
observation: String
```

Preserve non-tool messages and unexpected tool structures as text.

## 9.3 Normalizer behavior

Preserve the existing defensive support for mixed values, primitive steps, single tool dictionaries, tool lists, non-dictionary tools, alternate command/name keys, progress logging, explicit schemas, and Zstandard Parquet output.

---

# 10. Normalized-data validation

Implement:

```bash
python -m src.normalization.validate_normalized
```

Fail on broken invariants:

1. `run_id` unique.
2. Every step references an existing run.
3. No NaN/infinite cost or duration.
4. `has_steps == (step_count > 0)`.
5. `has_positive_cost == (cost_usd > 0)`.
6. `cost_status` agrees with cost.
7. `success == (reward == 1)` for non-null rewards.
8. Non-negative indexes/counts.
9. Required columns exist.
10. Allowed `run_id_source` values only.

Generate `docs/DATA_PROFILE.md` and `reports/data_quality.json`. Warn, but do not fail, if upstream counts change.

---

# 11. Step-level signal detection

Run:

```bash
python -m src.signals.detect
```

Output:

```text
data/processed/step_signals.parquet
```

Use Polars lazy scans.

Add:

```text
normalized_tool_name
normalized_command
normalized_action
observation_key
is_error
is_test
is_edit
is_read
is_search
is_shell
is_submission
is_adjacent_repeat
same_result_repeat
repeated_failed_attempt
suspected_waste
```

Normalization should trim and lowercase tool names, collapse command whitespace, replace temp paths and UUIDs, normalize line endings, and create a bounded observation fingerprint without changing source fields.

Initial error patterns:

```text
command not found
no such file or directory
permission denied
ModuleNotFoundError
module not found
SyntaxError
syntax error
traceback
fatal:
timed out
timeout
segmentation fault
AssertionError
tests failed
error:
```

Recognize common test commands and tool names such as Bash, Write, Edit, and Read.

Primary v0.1 waste rule:

```text
same normalized action
+ immediately previous tool event in same run
+ same normalized observation
+ not an edit action
= suspected_waste
```

Then:

```text
suspected_waste + error-like observation = repeated_failed_attempt
```

Do not label every repeated test as waste. A rerun after an edit can be valid.

Optionally calculate `repeat_within_5`, but do not use it in the primary public metric before manual evaluation.

---

# 12. Run-level aggregation

Run:

```bash
python -m src.signals.aggregate
```

Output:

```text
data/processed/run_signals.parquet
```

Add:

```text
observed_tool_events
error_events
test_actions
edit_actions
read_actions
search_actions
shell_actions
submission_actions
adjacent_repeats
same_result_repeats
repeated_failed_attempts
suspected_wasted_actions
suspected_waste_rate
error_event_rate
repeat_rate
read_search_rate
possible_missing_verification
estimated_wasted_cost_usd
estimated_wasted_duration_seconds
```

Definitions:

```text
suspected_waste_rate = suspected_wasted_actions / observed_tool_events
error_event_rate = error_events / observed_tool_events
repeat_rate = adjacent_repeats / observed_tool_events
```

Use zero only for zero-event denominators.

Possible missing verification:

```text
edit_actions > 0 and test_actions == 0
```

Estimated waste:

```text
cost_usd * suspected_waste_rate
duration_seconds * suspected_waste_rate
```

Calculate estimates only when the source metric and usable trajectory are present. Label them as proportional estimates.

---

# 13. Rule-based RCA

Run:

```bash
python -m src.signals.rca
```

Output:

```text
data/processed/runs_with_rca.parquet
```

Add:

```text
rule_based_rca
rca_confidence
rca_explanation
rca_evidence_step_indexes
```

Initial categories:

```text
REPEATED_FAILED_APPROACH
TOOL_EXECUTION_FAILURE
POSSIBLE_MISSING_VERIFICATION
EXCESSIVE_EXPLORATION
LATE_FAILURE
MISSING_TRAJECTORY
UNCLASSIFIED_FAILURE
NO_MAJOR_RULE_BASED_FAILURE
```

Use that priority order. Never force a specific RCA when evidence is insufficient. Serialize evidence indexes as JSON. Confidence is heuristic, not calibrated probability.

---

# 14. Excessive exploration

Calculate successful peer baselines by task:

```text
successful median observed_tool_events
successful p90 read_search_rate
successful p90 step_count
```

Flag only when enough successful peer runs exist and the failed run exceeds peer thresholds. Store baseline fields for auditability.

---

# 15. Benchmark database

Run:

```bash
python -m src.benchmarks.build
```

Create `data/processed/benchmark.duckdb` with:

```text
runs
steps
step_signals
run_signals
runs_with_rca
overview
data_quality
agent_model_leaderboard
agent_leaderboard
model_uncontrolled_leaderboard
task_difficulty
outcome_comparison
failure_patterns
cost_coverage_by_system
trajectory_coverage_by_system
```

Use direct Parquet reads where practical.

---

# 16. Metrics

## Overview

Report run counts, trajectory coverage, pass rate, task/agent/model counts, observed cost coverage, median duration/steps/tool calls, suspected waste, estimated waste, dataset revision, cutoff, and methodology version.

Waste metrics must use only runs with trajectories.

## Agent/model leaderboard

Group by agent and canonical model. Include:

```text
runs
tasks
successful_runs
pass_rate_micro
pass_rate_macro_by_task
Wilson confidence interval
median duration
median steps
median tool calls
trajectory coverage
cost field coverage
positive cost coverage
median positive cost
observed cost per success
mean waste/error/repeat rates
missing-verification rate
```

Default internal threshold: 20 runs. Default public ranked threshold: 100 runs, configurable.

## Cost eligibility

```text
cost_metrics_eligible = positive_cost_coverage >= 0.80 and runs >= 20
```

Only rank eligible systems by cost. Otherwise return null and display `Cost data insufficient`.

Observed cost per success:

```text
sum usable observed cost / successful usable-cost runs
```

Expose coverage. Never imply zero cost means free execution.

## Outcome comparison

Compare success and failure on cost, duration, steps, tool calls, waste, errors, and repeats. Produce both all-run and trajectory-only tables.

## Task difficulty and failure patterns

Generate transparent task and RCA aggregations with counts and sample sizes.

---

# 17. Historical early-stop simulation

Run:

```bash
python -m src.benchmarks.early_stopping
```

Policies:

1. Stop after the third identical failed action/result.
2. Stop after five consecutive error-like tool events.
3. Stop after a configurable same-result no-progress burst.

For each run/policy calculate trigger status, trigger step, events saved, proportional cost/duration saved, historical success, and false-stop status.

Aggregate false-stop rate and estimated savings. Label all values as counterfactual historical estimates.

---

# 18. Human labeling

Create a stratified sample:

```bash
python -m src.labeling.sample --size 50 --seed 42
```

Buckets:

```text
15 failed high-waste
10 failed low-waste
10 successful high-waste
10 successful low-waste
5 outliers
```

Create label columns:

```text
run_id
primary_rca
secondary_rca
waste_types
first_problem_step
evidence_steps
avoidable
severity
confidence
notes
reviewer
reviewed_at
```

Implement evaluation for RCA accuracy, waste precision/recall/F1, evidence precision/recall, false positives, and confusion matrix.

Prioritize precision. Do not publish aggregate waste claims before manually reviewing at least 20 high-waste examples.

---

# 19. Report export

Run:

```bash
python -m src.reports.export
```

Generate:

```text
reports/manifest.json
reports/public_benchmark.json
reports/overview.json
reports/leaderboard_agent_model.csv
reports/leaderboard_agent.csv
reports/leaderboard_model_uncontrolled.csv
reports/outcome_comparison.csv
reports/task_difficulty.csv
reports/failure_patterns.csv
reports/early_stop_simulation.csv
reports/data_quality.json
reports/examples/selected_trajectories.json
```

Manifest must include benchmark/methodology versions, generation time, dataset ID/revision/cutoff/counts, code commit, dirty status, and artifact list.

`public_benchmark.json` top-level shape:

```json
{
  "metadata": {},
  "coverage": {},
  "overview": {},
  "systems": [],
  "agents": [],
  "models_uncontrolled": [],
  "tasks": [],
  "failure_patterns": [],
  "early_stopping": [],
  "examples": []
}
```

Every system result must include sample size, task count, coverage, eligibility, and snapshot cutoff.

Sanitize obvious secrets in selected public trajectory examples. Do not modify source Parquet.

---

# 20. Streamlit dashboard

Run:

```bash
streamlit run dashboard/app.py
```

Read local DuckDB/Parquet/report artifacts only. No authentication or paid services.

Pages:

1. Overview
2. Leaderboards
3. Failure and Waste
4. Trajectory Explorer
5. Data Quality
6. Methodology

Persistent disclaimer:

> Results are historical and trajectory-backed. Waste, RCA, and savings values are rule-based estimates, not ground truth.

The trajectory explorer must query one selected run rather than load all step text into memory.

Always display revision, cutoff, methodology version, sample size, and coverage.

---

# 21. Lumni integration

Keep the OSS repository independent of Lumni’s private backend.

Create `docs/LUMNI_INTEGRATION.md` with:

```text
OSS pipeline
    ↓
reports/public_benchmark.json
    ↓
versioned public object or GitHub release
    ↓
Lumni ingestion job/API
    ↓
Lumni dashboard
```

Recommended Lumni routes:

```text
/benchmarks
/benchmarks/models
/benchmarks/agents
/benchmarks/failures
/benchmarks/waste
/benchmarks/tasks
/benchmarks/trajectories/:runId
/benchmarks/methodology
```

Navigation:

```text
Research
  Public Benchmarks
  Methodology
```

Product switch:

```text
Public Benchmarks | Your Agents
```

Keep private ingestion, advanced RCA, clustering, alerts, replay, routing, workflows, and enterprise controls proprietary.

---

# 22. Licensing and attribution

Use Apache-2.0 for repository code unless an existing license conflicts.

Do not commit upstream datasets.

Document:

```text
Terminal-Bench trajectories
https://huggingface.co/datasets/yoonholee/terminalbench-trajectories
License: Apache-2.0
```

Future SWE-agent support:

```text
https://huggingface.co/datasets/nebius/SWE-agent-trajectories
License: CC BY 4.0
Also respect licenses of represented repositories.
```

Create `DATA_SOURCES.md` and `THIRD_PARTY_NOTICES.md`.

---

# 23. Documentation

Create:

- `METHODOLOGY.md`
- `docs/LIMITATIONS.md`
- `docs/ARCHITECTURE.md`
- `docs/DATA_MODEL.md`
- `docs/DATA_PROFILE.md`
- `docs/LUMNI_INTEGRATION.md`

Limitations must explicitly state historical/confounded runs, incomplete cost accounting, zero-cost ambiguity, trajectory-only analysis limits, heuristic RCA, proportional waste estimation, counterfactual early-stop savings, and missing recent models.

README quick start:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make download
make normalize
make validate
make signals
make benchmarks
make export
make dashboard
```

Existing-data shortcut:

```bash
make normalize
make validate
make signals
make benchmarks
make export
make dashboard
```

---

# 24. Makefile

Implement targets:

```text
install
download
check-update
inspect
normalize
validate
signals
benchmarks
label-sample
evaluate-labels
export
dashboard
test
lint
format
all
clean-derived
```

`clean-derived` must not delete raw data or normalized runs/steps.

---

# 25. Tests and CI

Use synthetic fixtures; CI must not download the full dataset.

Test utilities, normalization edge cases, deterministic IDs, non-finite numbers, model aliases, repeat/error detection, aggregation denominators, missing verification, cost eligibility, micro/macro pass rate, Wilson intervals, and Pydantic report schema.

GitHub Actions should test Python 3.10 and 3.11, run Ruff, pytest, a synthetic fixture pipeline, and report-schema validation.

---

# 26. Performance requirements

- Use Polars lazy scans for signals and aggregation.
- Use DuckDB for benchmark views.
- Do not load 1.98 million steps into pandas.
- Query only selected trajectories in the dashboard.
- Use Zstandard Parquet compression.
- Avoid duplicating large text columns.
- Do not create another 2-million-row Python dictionary list for signal enrichment.
- Existing normalization loop may remain because it completed successfully.
- Write long-running outputs to temporary files and atomically rename where practical.

---

# 27. Public presentation rules

Every public result must include dataset source/revision/cutoff, generated time, methodology version, sample size, and coverage.

Use:

```text
Trajectory-backed
Historical public run
Rule-based RCA
Suspected waste
Historical estimate
```

Do not use:

```text
Latest model leaderboard
Universal best model
Proven waste
Guaranteed savings
```

For absent models, display trajectory unavailable and do not invent data.

---

# 28. Completion criteria

## Reliable data

- Full normalization succeeds.
- IDs are deterministic and unique.
- No non-finite cost/duration remains.
- Raw and canonical models retained.
- Validation passes.
- Data profile generated.

## Signals

- Step signals generated.
- Repeated and failed attempts detected.
- Run aggregation generated.
- At least 20 high-waste runs reviewed.
- False positives documented.

## Benchmarks

- DuckDB created.
- Coverage-aware leaderboards generated.
- Cost eligibility enforced.
- Public JSON validates.
- Early-stop simulation generated.

## Dashboard

- Six pages load.
- Filters work.
- Explorer queries one run at a time.
- Coverage and limitations visible.
- No paid service required.

## OSS readiness

- README commands work.
- Makefile works.
- Tests and Ruff pass.
- CI uses synthetic fixtures.
- License/attribution complete.
- Large data ignored.

---

# 29. Commands Codex must run before completion

```bash
python -m src.ingestion.inspect_dataset
python -m src.normalization.normalize_terminalbench
python -m src.normalization.validate_normalized
python -m src.signals.detect
python -m src.signals.aggregate
python -m src.signals.rca
python -m src.benchmarks.build
python -m src.benchmarks.early_stopping
python -m src.reports.export
python -m src.benchmarks.validate_reports
pytest -q
ruff check .
```

Run a dashboard data-access smoke test and print final counts/artifact paths.

Do not declare completion while required commands fail.

---

# 30. Final Codex response

Report:

1. Files created/changed
2. Commands run
3. Validation results
4. Key generated counts
5. Test results
6. Known limitations
7. Dashboard launch command
8. Lumni artifact path

Mention anything not completed.

---

# 31. Non-goals for v0.1

Do not implement:

- SWE-agent ingestion
- Fresh model runs
- Live interception
- Production OTel ingestion
- Vector search
- LLM-generated RCA
- Fine-tuning
- Automatic fixes
- Authentication/billing
- Alerts
- Cloud hosting
- Private cross-company comparisons
- A universal composite best-model score

The v0.1 product is:

> Download public trajectories, normalize them, detect conservative operational signals, generate transparent benchmarks, show evidence, and export a public artifact for Lumni.

---

# 32. Primary references

- Terminal-Bench trajectories: `https://huggingface.co/datasets/yoonholee/terminalbench-trajectories`
- Harbor ATIF: `https://harborframework.com/docs/agents/trajectory-format`
- DuckDB Parquet: `https://duckdb.org/docs/stable/data/parquet/overview.html`
- Future SWE-agent dataset: `https://huggingface.co/datasets/nebius/SWE-agent-trajectories`
