from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from src.afwb.constants import MUTATION_OUTPUT, REFERENCE_OUTPUT
from src.afwb.runner import DeterministicRunner
from src.afwb.scenarios import load_scenarios
from src.afwb.schemas import TraceVariant
from src.afwb.trace import write_jsonl
from src.afwb.validation import validate_scenarios


app = typer.Typer(no_args_is_help=True, help="AFWB Lite local benchmark CLI.")
generate_app = typer.Typer(no_args_is_help=True, help="Generate deterministic traces.")
memory_app = typer.Typer(no_args_is_help=True, help="Memory commands.")
app.add_typer(generate_app, name="generate")
app.add_typer(memory_app, name="memory")


def _foundation_stub(command: str) -> None:
    typer.echo(f"{command} is deferred beyond the AFWB Lite Foundation milestone.")
    raise typer.Exit(code=2)


@app.command()
def validate() -> None:
    """Validate foundation scenarios, gold labels, and generated trace invariants."""
    report = validate_scenarios()
    typer.echo(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    if not report.ok:
        raise typer.Exit(code=1)


@generate_app.command("references")
def generate_references(
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="JSONL output path for deterministic reference traces.",
        ),
    ] = REFERENCE_OUTPUT,
) -> None:
    """Generate successful reference traces for Foundation scenarios."""
    _generate(TraceVariant.REFERENCE, output)


@generate_app.command("mutations")
def generate_mutations(
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="JSONL output path for deterministic mutated traces.",
        ),
    ] = MUTATION_OUTPUT,
) -> None:
    """Generate failed or wasteful mutated traces for Foundation scenarios."""
    _generate(TraceVariant.MUTATED, output)


@app.command("run-rca")
def run_rca() -> None:
    _foundation_stub("run-rca")


@app.command("run-memory")
def run_memory() -> None:
    _foundation_stub("run-memory")


@app.command()
def score() -> None:
    _foundation_stub("score")


@app.command()
def replay() -> None:
    _foundation_stub("replay")


@app.command()
def report() -> None:
    _foundation_stub("report")


@memory_app.command("index")
def memory_index() -> None:
    _foundation_stub("memory index")


def _generate(variant: TraceVariant, output: Path) -> None:
    runner = DeterministicRunner.create()
    traces = [runner.run(scenario, variant) for scenario in load_scenarios()]
    write_jsonl(output, traces)
    typer.echo(f"Wrote {len(traces)} {variant.value} traces to {output}")


if __name__ == "__main__":
    app()
