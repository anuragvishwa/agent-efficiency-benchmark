PYTHON ?= .venv/bin/python
STREAMLIT ?= .venv/bin/streamlit
RUFF ?= .venv/bin/ruff
PIP ?= .venv/bin/pip

.PHONY: install download check-update inspect normalize validate signals benchmarks download-swe inspect-swe normalize-swe validate-swe signals-swe benchmarks-swe swe-agent all-datasets label-sample evaluate-labels export dashboard afwb-validate afwb-generate afwb-smoke test lint format all clean-derived

install:
	$(PIP) install -r requirements.txt

download:
	$(PYTHON) -m src.ingestion.download_terminalbench

check-update:
	$(PYTHON) -m src.ingestion.check_dataset_update

inspect:
	$(PYTHON) -m src.ingestion.inspect_dataset

normalize:
	$(PYTHON) -m src.normalization.normalize_terminalbench

validate:
	$(PYTHON) -m src.normalization.validate_normalized

signals:
	$(PYTHON) -m src.signals.detect
	$(PYTHON) -m src.signals.aggregate
	$(PYTHON) -m src.signals.rca

benchmarks:
	$(PYTHON) -m src.benchmarks.build
	$(PYTHON) -m src.benchmarks.early_stopping

download-swe:
	$(PYTHON) -m src.ingestion.download_swe_agent

inspect-swe:
	$(PYTHON) -m src.ingestion.inspect_swe_agent

normalize-swe:
	$(PYTHON) -m src.normalization.normalize_swe_agent

validate-swe:
	$(PYTHON) -m src.normalization.validate_normalized --dataset swe_agent

signals-swe:
	$(PYTHON) -m src.signals.detect --dataset swe_agent
	$(PYTHON) -m src.signals.aggregate --dataset swe_agent
	$(PYTHON) -m src.signals.rca --dataset swe_agent

benchmarks-swe:
	$(PYTHON) -m src.benchmarks.build --dataset swe_agent
	$(PYTHON) -m src.benchmarks.early_stopping --dataset swe_agent

swe-agent: normalize-swe validate-swe signals-swe benchmarks-swe export

all-datasets: all swe-agent

label-sample:
	$(PYTHON) -m src.labeling.sample --size 50 --seed 42

evaluate-labels:
	$(PYTHON) -m src.labeling.evaluate

export:
	$(PYTHON) -m src.reports.export
	$(PYTHON) -m src.benchmarks.validate_reports

dashboard:
	$(STREAMLIT) run dashboard/app.py

afwb-validate:
	$(PYTHON) -m src.afwb.cli validate

afwb-generate:
	$(PYTHON) -m src.afwb.cli generate references
	$(PYTHON) -m src.afwb.cli generate mutations

afwb-smoke: afwb-validate afwb-generate

test:
	$(PYTHON) -m pytest -q

lint:
	$(RUFF) check .

format:
	$(RUFF) format .

all: normalize validate signals benchmarks export test lint

clean-derived:
	rm -f data/processed/step_signals.parquet
	rm -f data/processed/run_signals.parquet
	rm -f data/processed/runs_with_rca.parquet
	rm -f data/processed/benchmark.duckdb
	rm -f data/processed/early_stop_simulation.parquet
	rm -f data/processed/swe_agent_step_signals.parquet
	rm -f data/processed/swe_agent_run_signals.parquet
	rm -f data/processed/swe_agent_runs_with_rca.parquet
	rm -f data/processed/swe_agent_benchmark.duckdb
	rm -f data/processed/swe_agent_early_stop_simulation.parquet
	rm -rf reports/*
	touch reports/.gitkeep
