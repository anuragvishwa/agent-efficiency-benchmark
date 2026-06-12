# Lumni Open-Source Agent Efficiency Benchmark

This repository builds a local, reproducible benchmark over public agent
trajectories, starting with Terminal-Bench and SWE-agent trajectories. It
normalizes runs, detects conservative trajectory-backed signals, exports
JSON/CSV artifacts, and serves a local Streamlit dashboard.

The free workflow uses local files only. It does not require paid model APIs,
cloud services, managed databases, Docker, GPUs, or fresh model execution.

## Quick Start

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

SWE-agent add-on:

```bash
make download-swe
make swe-agent
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

## Public Artifacts

The Lumni-facing artifact is:

```text
reports/public_benchmark.json
```

All public results include sample size, coverage, dataset revision or local
revision status, snapshot cutoff, and methodology version. Waste, RCA, and
early-stop savings are rule-based historical estimates, not ground truth.

Terminal-Bench and SWE-agent are displayed as separate benchmark families. They
are not merged into one universal leaderboard.

## Main Commands

```bash
make inspect
make normalize
make validate
make signals
make benchmarks
make export
make test
make lint
```

The dashboard runs locally with:

```bash
streamlit run dashboard/app.py
```

## Public Streamlit Deployment

This repository is ready for Streamlit Community Cloud. Use these settings:

```text
Repository: anuragvishwa/agent-efficiency-benchmark
Branch: main
Main file path: dashboard/app.py
```

The public app uses the checked-in `reports/public_benchmark.json`,
`reports/swe_agent_public_benchmark.json`, and selected report CSVs. It does not
require downloading the raw datasets or committing local DuckDB/Parquet files.

## AFWB Lite Foundation

AFWB Lite is a deterministic, local benchmark layer for agent root-cause and
waste scenarios. The current implementation covers the Foundation milestone:
schemas, CLI wiring, mock model/tools, a deterministic runner, and the first
four RCA scenarios from `afwb-lite-low-cost-benchmark-spec.md`.

```bash
make afwb-validate
make afwb-generate
```

The same commands are available directly:

```bash
python -m src.afwb.cli validate
python -m src.afwb.cli generate references
python -m src.afwb.cli generate mutations
```

Generated traces are written to `results/afwb/raw/` and are intentionally not
tracked. The Foundation path performs no hosted model calls and does not depend
on git metadata.

Deferred AFWB Lite milestones include the full 24-scenario RCA suite, RCA
scoring, remediation replay, memory variants, temporal hybrid retrieval,
reports, release artifacts, and optional cached LLM judging.
