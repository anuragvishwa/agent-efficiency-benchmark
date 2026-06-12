from __future__ import annotations

import json

import polars as pl

from src.common.constants import LABELS_DIR, REPORTS_DIR, RUNS_WITH_RCA_PATH


def _parse_steps(value: str | None) -> set[int]:
    if not value:
        return set()
    try:
        parsed = json.loads(value)
        if isinstance(parsed, list):
            return {int(item) for item in parsed}
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return {
        int(part.strip())
        for part in value.split(",")
        if part.strip().lstrip("-").isdigit()
    }


def main() -> None:
    labels_path = LABELS_DIR / "rca_labels.csv"
    if not labels_path.exists():
        print(f"No labels found at {labels_path}")
        return
    labels = pl.read_csv(labels_path, infer_schema_length=0)
    labels = labels.filter(pl.col("reviewed_at").fill_null("") != "")
    if labels.is_empty():
        print("No reviewed labels available yet.")
        return

    runs = pl.read_parquet(RUNS_WITH_RCA_PATH).select(
        ["run_id", "rule_based_rca", "rca_evidence_step_indexes", "suspected_waste_rate"]
    )
    joined = labels.join(runs, on="run_id", how="left")
    total = joined.height
    rca_accuracy = (
        joined.filter(pl.col("primary_rca") == pl.col("rule_based_rca")).height / total
        if total
        else 0
    )
    avoidable_positive = joined.filter(
        pl.col("avoidable").str.to_lowercase().is_in(["true", "yes", "1"])
    ).height
    suspected_positive = joined.filter(pl.col("suspected_waste_rate") > 0).height
    true_positive = joined.filter(
        (pl.col("suspected_waste_rate") > 0)
        & pl.col("avoidable").str.to_lowercase().is_in(["true", "yes", "1"])
    ).height
    precision = true_positive / suspected_positive if suspected_positive else 0
    recall = true_positive / avoidable_positive if avoidable_positive else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0

    evidence_overlaps = []
    for row in joined.iter_rows(named=True):
        predicted = _parse_steps(row.get("rca_evidence_step_indexes"))
        labeled = _parse_steps(row.get("evidence_steps"))
        if not predicted and not labeled:
            continue
        overlap = len(predicted & labeled)
        evidence_overlaps.append(
            {
                "precision": overlap / len(predicted) if predicted else 0,
                "recall": overlap / len(labeled) if labeled else 0,
            }
        )
    evidence_precision = (
        sum(item["precision"] for item in evidence_overlaps) / len(evidence_overlaps)
        if evidence_overlaps
        else 0
    )
    evidence_recall = (
        sum(item["recall"] for item in evidence_overlaps) / len(evidence_overlaps)
        if evidence_overlaps
        else 0
    )
    confusion = (
        joined.group_by(["primary_rca", "rule_based_rca"])
        .agg(pl.len().alias("runs"))
        .sort("runs", descending=True)
        .to_dicts()
    )
    report = {
        "reviewed_runs": total,
        "rca_accuracy": rca_accuracy,
        "waste_precision": precision,
        "waste_recall": recall,
        "waste_f1": f1,
        "evidence_precision": evidence_precision,
        "evidence_recall": evidence_recall,
        "false_positives": max(suspected_positive - true_positive, 0),
        "confusion_matrix": confusion,
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / "label_evaluation.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    print(f"Label evaluation saved to {path}")


if __name__ == "__main__":
    main()
