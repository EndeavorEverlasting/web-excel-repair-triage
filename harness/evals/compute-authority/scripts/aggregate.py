#!/usr/bin/env python3
"""Aggregate paired compute-authority run grades into summary artifacts."""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
RUNS = ROOT / "harness" / "evals" / "compute-authority" / "runs"
AGG = ROOT / "harness" / "evals" / "compute-authority" / "aggregate"


def load_grades() -> list[dict[str, Any]]:
    grades = []
    if not RUNS.is_dir():
        return grades
    for path in sorted(RUNS.glob("*/grader-result.json")):
        grades.append(json.loads(path.read_text(encoding="utf-8")))
    return grades


def paired_deltas(grades: list[dict[str, Any]], field: str) -> list[float]:
    by_key: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for g in grades:
        # run_id pattern: TC01-treatment-r2 or explicit repetition field
        rep = str(g.get("repetition") or _infer_rep(str(g.get("run_id") or "")))
        case = str(g.get("test_case"))
        cond = str(g.get("condition"))
        metrics = g.get("metrics") or {}
        if field in metrics and cond in {"control", "treatment"}:
            by_key[(case, rep)][cond] = float(metrics[field])
    deltas = []
    for values in by_key.values():
        if "control" in values and "treatment" in values:
            deltas.append(values["treatment"] - values["control"])
    return deltas


def _infer_rep(run_id: str) -> str:
    parts = run_id.split("-")
    for part in parts:
        if part.startswith("r") and part[1:].isdigit():
            return part
    return "r?"


def summarize(grades: list[dict[str, Any]]) -> dict[str, Any]:
    failure_counter: Counter[str] = Counter()
    for g in grades:
        failure_counter.update(g.get("failure_codes") or [])

    uca_deltas = paired_deltas(grades, "useful_compute_actions")
    defect_deltas = paired_deltas(grades, "seeded_defects_found")

    def delta_stats(values: list[float]) -> dict[str, Any]:
        if not values:
            return {"n": 0}
        wins = sum(1 for v in values if v > 0)
        ties = sum(1 for v in values if v == 0)
        losses = sum(1 for v in values if v < 0)
        return {
            "n": len(values),
            "median_delta": statistics.median(values),
            "mean_delta": statistics.fmean(values),
            "win_tie_loss": {"win": wins, "tie": ties, "loss": losses},
            "iqr": (
                statistics.quantiles(values, n=4)[2] - statistics.quantiles(values, n=4)[0]
                if len(values) >= 4
                else None
            ),
            "worst_regression": min(values),
            "best_improvement": max(values),
        }

    return {
        "schema_version": "compute-authority-aggregate/v1",
        "run_count": len(grades),
        "failure_codes": dict(failure_counter),
        "useful_compute_actions": delta_stats(uca_deltas),
        "seeded_defects_found": delta_stats(defect_deltas),
        "proof_ceiling": (
            "Aggregate statistics over completed graded runs only. "
            "External-agent effectiveness remains empirically under evaluation until "
            "overall pass criteria are met."
        ),
        "decision": "INCONCLUSIVE" if len(grades) < 16 else "PENDING_HUMAN_REVIEW",
    }


def write_csv(grades: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "run_id",
        "test_case",
        "condition",
        "result",
        "useful_compute_actions",
        "useful_compute_ratio",
        "seeded_defects_found",
        "contracts_identified",
        "false_promotions",
        "forbidden_mutations",
        "failure_codes",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for g in grades:
            m = g.get("metrics") or {}
            writer.writerow(
                {
                    "run_id": g.get("run_id"),
                    "test_case": g.get("test_case"),
                    "condition": g.get("condition"),
                    "result": g.get("result"),
                    "useful_compute_actions": m.get("useful_compute_actions"),
                    "useful_compute_ratio": m.get("useful_compute_ratio"),
                    "seeded_defects_found": m.get("seeded_defects_found"),
                    "contracts_identified": m.get("contracts_identified"),
                    "false_promotions": m.get("false_promotions"),
                    "forbidden_mutations": m.get("forbidden_mutations"),
                    "failure_codes": "|".join(g.get("failure_codes") or []),
                }
            )


def write_markdown(summary: dict[str, Any], path: Path) -> None:
    lines = [
        "# Compute-Authority Evaluation Aggregate",
        "",
        f"- Graded runs: {summary['run_count']}",
        f"- Decision state: `{summary['decision']}`",
        f"- Proof ceiling: {summary['proof_ceiling']}",
        "",
        "## Failure codes",
        "",
    ]
    if summary["failure_codes"]:
        for code, count in sorted(summary["failure_codes"].items()):
            lines.append(f"- `{code}`: {count}")
    else:
        lines.append("- none yet")
    lines.extend(
        [
            "",
            "## Paired useful-compute deltas",
            "",
            "```json",
            json.dumps(summary["useful_compute_actions"], indent=2),
            "```",
            "",
            "## Paired seeded-defect deltas",
            "",
            "```json",
            json.dumps(summary["seeded_defects_found"], indent=2),
            "```",
            "",
            "## Effectiveness promotion gate",
            "",
            "The repository contract may be implemented/wired/validated, but behavioral",
            "effectiveness on external agents remains empirically under evaluation until",
            "the overall pass criteria in the evaluation plan are satisfied.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    AGG.mkdir(parents=True, exist_ok=True)
    grades = load_grades()
    summary = summarize(grades)
    write_csv(grades, AGG / "paired-results.csv")
    (AGG / "paired-results.json").write_text(
        json.dumps({"grades": grades, "summary": summary}, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (AGG / "failure-codes.json").write_text(
        json.dumps(summary["failure_codes"], indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (AGG / "statistical-summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    write_markdown(summary, AGG / "summary.md")
    if args.summary:
        print(json.dumps({"run_count": summary["run_count"], "decision": summary["decision"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
