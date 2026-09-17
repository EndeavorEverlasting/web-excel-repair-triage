#!/usr/bin/env python3
"""Create one isolated run evidence bundle bound to a frozen experimental condition."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVAL = ROOT / "harness" / "evals" / "compute-authority"
FIX = EVAL / "fixtures"
SCRIPTS = EVAL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from conditions import resolve  # noqa: E402
from reset_fixture import reset_case  # noqa: E402

VALID_CASES = {f"TC{i:02d}" for i in range(1, 9)}


def fixture_sha(case_id: str) -> str:
    ws = FIX / case_id / "workspace"
    h = hashlib.sha256()
    for path in sorted(p for p in ws.rglob("*") if p.is_file()):
        h.update(path.relative_to(ws).as_posix().encode())
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def repository_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def initialize_run(
    *,
    case_id: str,
    condition: str,
    repetition: int = 1,
    run_id: str | None = None,
    agent: str = "",
    model: str = "",
) -> Path:
    case_id = case_id.upper()
    if case_id not in VALID_CASES:
        raise ValueError(f"invalid case: {case_id}")
    if repetition < 1:
        raise ValueError("repetition must be >= 1")
    frozen = resolve(condition)
    run_id = run_id or f"{case_id}-{condition}-r{repetition}"
    run_dir = EVAL / "runs" / run_id
    if run_dir.exists():
        raise FileExistsError(f"run dir already exists: {run_dir}")
    run_dir.mkdir(parents=True)

    prompt_src = ROOT / frozen["prompt_path"]
    shutil.copy2(prompt_src, run_dir / f"prompt-{condition}.txt")
    shutil.copy2(FIX / case_id / "task.txt", run_dir / "task.txt")
    reset_case(case_id, run_id=run_id)

    env = {"worker_capacity": 0}
    env_path = FIX / case_id / "environment.json"
    if env_path.is_file():
        env = json.loads(env_path.read_text(encoding="utf-8"))
    (run_dir / "environment.json").write_text(json.dumps(env, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    starting = {
        "case": case_id,
        "fixture_sha": fixture_sha(case_id),
        "workspace_relpath": "workspace",
        "condition_sha": frozen["prompt_contract_sha"],
    }
    (run_dir / "starting-state.json").write_text(json.dumps(starting, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "condition.json").write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    for name in ("transcript.jsonl", "tool-events.jsonl", "git-before.txt", "git-after.txt", "diff.patch", "closeout.txt"):
        (run_dir / name).write_text("", encoding="utf-8")
    (run_dir / "validation-results.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "contracts.json").write_text(json.dumps({"contracts": []}, indent=2) + "\n", encoding="utf-8")
    (run_dir / "metrics.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "evaluator-score.json").write_text("{}\n", encoding="utf-8")
    run_meta = {
        "run_id": run_id,
        "test_case": case_id,
        "condition": condition,
        "repetition": repetition,
        "agent": agent,
        "model": model,
        "condition_source_commit": frozen["source_commit"],
        "prompt_contract_sha": frozen["prompt_contract_sha"],
        "fixture_sha": starting["fixture_sha"],
        "repository_sha": repository_sha(),
        "tool_permissions": [],
        "worker_capacity": int(env.get("worker_capacity") or 0),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": "",
        "termination_reason": "",
        "result": "invalid",
    }
    (run_dir / "run.json").write_text(json.dumps(run_meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--condition", required=True, choices=["control", "treatment"])
    parser.add_argument("--repetition", type=int, default=1)
    parser.add_argument("--run-id")
    parser.add_argument("--agent", default="")
    parser.add_argument("--model", default="")
    args = parser.parse_args(argv)
    run_dir = initialize_run(
        case_id=args.case,
        condition=args.condition,
        repetition=args.repetition,
        run_id=args.run_id,
        agent=args.agent,
        model=args.model,
    )
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
