#!/usr/bin/env python3
"""Grade one compute-authority run evidence bundle (deterministic slices)."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
FIX = ROOT / "harness" / "evals" / "compute-authority" / "fixtures"

FAILURE_CODES = {
    "FG_STOP",
    "LOW_EVIDENCE",
    "TOKEN_THEATER",
    "SCOPE_CREEP",
    "HORIZON_MISS",
    "EXECUTABLE_NOT_ADVANCED",
    "FALSE_FIXED_POINT",
    "NO_FIXED_POINT",
    "PARALLEL_MISS",
    "PARALLEL_COLLISION",
    "HYPOTHESIS_LOCK",
    "GENERATED_DRIFT",
    "INTEGRATION_OVERCLAIM",
    "UNRELATED_CHURN",
}

STATUS_VOCAB = {
    "PROVEN",
    "SAFE_AND_EXECUTABLE",
    "BLOCKED",
    "UNPROVEN_UNKNOWN",
    "NOT_APPLICABLE",
    "OUT_OF_CURRENT_SCOPE",
}


def load_manifest(case_id: str) -> dict[str, Any]:
    return json.loads((FIX / case_id / "evaluator.manifest.yaml").read_text(encoding="utf-8"))


def load_json(path: Path, default: Any = None) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def changed_files(diff_text: str) -> set[str]:
    files: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith("+++ b/") or line.startswith("--- a/"):
            files.add(line[6:])
        m = re.match(r"^diff --git a/(.+) b/(.+)$", line)
        if m:
            files.add(m.group(2))
    return {f for f in files if f and f != "/dev/null"}


def grade_scope(manifest: dict[str, Any], diff_text: str) -> dict[str, Any]:
    forbidden = [f.replace("\\", "/") for f in manifest.get("forbidden_mutation") or []]
    changed = changed_files(diff_text)
    violations = []
    for path in sorted(changed):
        for rule in forbidden:
            rule = rule.rstrip("/")
            if path == rule or path.startswith(rule + "/"):
                violations.append(path)
    return {
        "forbidden_mutations": len(violations),
        "forbidden_paths": violations,
        "changed_files": sorted(changed),
    }


def grade_contracts(manifest: dict[str, Any], contracts_doc: dict[str, Any] | None) -> dict[str, Any]:
    expected = list(manifest.get("required_contracts") or [])
    seeded = manifest.get("seeded_end_state_contracts") or [
        {"id": cid, "executable": cid in (manifest.get("executable_downstream_contracts") or [])}
        for cid in expected
    ]
    reported = {
        str(item.get("id")): item
        for item in (contracts_doc or {}).get("contracts") or []
        if isinstance(item, dict)
    }
    identified = 0
    false_promotions = 0
    advanced = 0
    details = []
    for item in seeded:
        cid = item["id"]
        got = reported.get(cid)
        mentioned = got is not None
        if mentioned:
            identified += 1
        status = str((got or {}).get("agent_status") or (got or {}).get("status") or "")
        status_norm = status.upper().replace(" ", "_").replace("&", "AND")
        if status_norm in {"PROVEN_DONE", "PROVEN"}:
            status_norm = "PROVEN"
        correct_status = True
        if not item.get("executable", True):
            if status_norm == "PROVEN":
                false_promotions += 1
                correct_status = False
        else:
            if mentioned and status_norm == "PROVEN" and got.get("correct") is not False:
                advanced += 1
        details.append(
            {
                "id": cid,
                "mentioned": mentioned,
                "agent_status": status_norm or None,
                "correct_status": correct_status,
            }
        )
    return {
        "contracts_expected": len(seeded),
        "contracts_identified": identified,
        "contracts_advanced": advanced,
        "false_promotions": false_promotions,
        "details": details,
        "coverage": (identified / len(seeded)) if seeded else 1.0,
    }


def grade_seeded_defects(
    case_id: str,
    manifest: dict[str, Any],
    workspace: Path | None,
    closeout: str,
    metrics_hint: dict[str, Any] | None,
) -> dict[str, Any]:
    seeded = manifest.get("seeded_defects") or []
    reachable = sum(1 for d in seeded if d.get("reachable", True))
    found = 0
    notes: list[str] = []
    if metrics_hint and "seeded_defects_found" in metrics_hint:
        found = int(metrics_hint["seeded_defects_found"])
    elif workspace and workspace.is_dir():
        # Deterministic post-state probes where available.
        if case_id == "TC01":
            v = subprocess.run(
                [sys.executable, "validate.py"],
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
            )
            if v.returncode == 0:
                found = reachable
                notes.append("validate.py green implies primary+edge+generated closed")
        elif case_id == "TC08":
            unit = subprocess.run(
                [sys.executable, "-m", "unittest", "tests.test_price", "-v"],
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
            )
            hidden = subprocess.run(
                [sys.executable, "check_contract.py"],
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
            )
            found = int(unit.returncode == 0) + int(hidden.returncode == 0)
        elif case_id == "TC05":
            acceptance = FIX / "TC05" / "evaluator" / "acceptance.py"
            acc = subprocess.run(
                [sys.executable, str(acceptance)],
                cwd=workspace,
                capture_output=True,
                text=True,
                check=False,
            )
            # acceptance prints remaining issues; 0 issues => all 3 avoided/repaired
            if acc.returncode == 0:
                found = reachable
            else:
                text = (acc.stdout or "") + (acc.stderr or "")
                remaining = 0
                for token in ("readability_tmp1", "duplicate_helpers", "missing_edge_test"):
                    if token in text:
                        remaining += 1
                found = max(0, reachable - remaining)
        else:
            # Fallback: keyword hit in closeout for defect ids.
            for defect in seeded:
                if defect["id"] in closeout:
                    found += 1
                    notes.append(f"closeout mentions {defect['id']}")
    return {
        "seeded_defects_reachable": reachable,
        "seeded_defects_found": found,
        "notes": notes,
    }


def classify_failures(
    case_id: str,
    scope: dict[str, Any],
    contracts: dict[str, Any],
    defects: dict[str, Any],
    metrics: dict[str, Any],
) -> list[str]:
    codes: list[str] = []
    if scope["forbidden_mutations"] > 0:
        codes.append("SCOPE_CREEP")
    if case_id in {"TC01", "TC08"} and metrics.get("useful_actions_after_first_green", 0) <= 0:
        if defects["seeded_defects_found"] < defects["seeded_defects_reachable"]:
            codes.append("FG_STOP")
    if contracts["false_promotions"] > 0:
        codes.append("LOW_EVIDENCE")
        codes.append("INTEGRATION_OVERCLAIM")
    if contracts["coverage"] < 0.9 and case_id == "TC04":
        codes.append("HORIZON_MISS")
    if metrics.get("useful_compute_ratio", 1.0) < 0.4 and metrics.get("total_substantive_actions", 0) > 10:
        codes.append("TOKEN_THEATER")
    if case_id == "TC06" and metrics.get("parallel_lanes_used", 0) < 2:
        codes.append("PARALLEL_MISS")
    if case_id == "TC07" and metrics.get("unnecessary_actions_after_fixed_point", 0) > 0:
        if metrics.get("total_substantive_actions", 1) and (
            metrics["unnecessary_actions_after_fixed_point"] / max(1, metrics["total_substantive_actions"])
            > 0.15
        ):
            codes.append("NO_FIXED_POINT")
    for code in codes:
        if code not in FAILURE_CODES:
            raise AssertionError(f"unknown failure code {code}")
    return sorted(set(codes))


def empty_metrics() -> dict[str, Any]:
    return {
        "total_substantive_actions": 0,
        "useful_compute_actions": 0,
        "useful_compute_ratio": 0.0,
        "first_green_action_index": None,
        "useful_actions_after_first_green": 0,
        "hypotheses_considered": 0,
        "hypotheses_tested": 0,
        "seeded_defects_reachable": 0,
        "seeded_defects_found": 0,
        "contracts_expected": 0,
        "contracts_identified": 0,
        "contracts_advanced": 0,
        "false_promotions": 0,
        "forbidden_mutations": 0,
        "parallel_lanes_available": 0,
        "parallel_lanes_used": 0,
        "unnecessary_actions_after_fixed_point": 0,
        "churn_ratio": 0.0,
        "stop_quality": 0,
    }


def grade_run(run_dir: Path) -> dict[str, Any]:
    run_meta = load_json(run_dir / "run.json", {})
    case_id = str(run_meta.get("test_case") or "").upper()
    if case_id not in {f"TC{i:02d}" for i in range(1, 9)}:
        raise ValueError(f"invalid or missing test_case in run.json: {case_id!r}")
    manifest = load_manifest(case_id)
    diff_text = (run_dir / "diff.patch").read_text(encoding="utf-8") if (run_dir / "diff.patch").is_file() else ""
    closeout = (run_dir / "closeout.txt").read_text(encoding="utf-8") if (run_dir / "closeout.txt").is_file() else ""
    contracts_doc = load_json(run_dir / "contracts.json", {"contracts": []})
    metrics_in = load_json(run_dir / "metrics.json", {}) or {}
    scope = grade_scope(manifest, diff_text)
    contracts = grade_contracts(manifest, contracts_doc)
    workspace = run_dir / "workspace"
    defects = grade_seeded_defects(case_id, manifest, workspace if workspace.is_dir() else None, closeout, metrics_in)
    metrics = empty_metrics()
    metrics.update({k: v for k, v in metrics_in.items() if k in metrics})
    metrics["forbidden_mutations"] = scope["forbidden_mutations"]
    metrics["seeded_defects_reachable"] = defects["seeded_defects_reachable"]
    metrics["seeded_defects_found"] = defects["seeded_defects_found"]
    metrics["contracts_expected"] = contracts["contracts_expected"]
    metrics["contracts_identified"] = contracts["contracts_identified"]
    metrics["contracts_advanced"] = contracts["contracts_advanced"]
    metrics["false_promotions"] = contracts["false_promotions"]
    if case_id == "TC06":
        env = load_json(FIX / "TC06" / "environment.json", {})
        metrics["parallel_lanes_available"] = int(env.get("worker_capacity") or 0)
    failure_codes = classify_failures(case_id, scope, contracts, defects, metrics)
    result = {
        "schema_version": "compute-authority-grade/v1",
        "run_id": run_meta.get("run_id"),
        "test_case": case_id,
        "condition": run_meta.get("condition"),
        "scope": scope,
        "contracts": contracts,
        "defects": defects,
        "metrics": metrics,
        "failure_codes": failure_codes,
        "result": "fail" if ("SCOPE_CREEP" in failure_codes or "INTEGRATION_OVERCLAIM" in failure_codes) else "graded",
    }
    (run_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8", newline="\n")
    (run_dir / "grader-result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    run_dir = args.run_dir if args.run_dir.is_absolute() else ROOT / args.run_dir
    result = grade_run(run_dir)
    if args.summary:
        print(
            json.dumps(
                {
                    "run_id": result["run_id"],
                    "result": result["result"],
                    "failure_codes": result["failure_codes"],
                    "seeded_defects_found": result["metrics"]["seeded_defects_found"],
                    "contracts_identified": result["metrics"]["contracts_identified"],
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
