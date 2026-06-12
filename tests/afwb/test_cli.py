from __future__ import annotations

from typer.testing import CliRunner

from src.afwb.cli import app
from src.afwb.trace import read_jsonl


runner = CliRunner()


def test_validate_cli_passes() -> None:
    result = runner.invoke(app, ["validate"])

    assert result.exit_code == 0
    assert '"ok": true' in result.output
    assert '"scenario_count": 4' in result.output


def test_generate_reference_cli_writes_deterministic_jsonl(tmp_path) -> None:
    output = tmp_path / "reference_runs.jsonl"

    first = runner.invoke(app, ["generate", "references", "--output", str(output)])
    first_payload = output.read_text()
    second = runner.invoke(app, ["generate", "references", "--output", str(output)])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert output.read_text() == first_payload
    traces = read_jsonl(output)
    assert len(traces) == 4
    assert {trace.status.value for trace in traces} == {"passed"}


def test_generate_mutation_cli_writes_failed_jsonl(tmp_path) -> None:
    output = tmp_path / "mutated_runs.jsonl"

    result = runner.invoke(app, ["generate", "mutations", "--output", str(output)])

    assert result.exit_code == 0
    traces = read_jsonl(output)
    assert len(traces) == 4
    assert {trace.status.value for trace in traces} == {"failed"}
