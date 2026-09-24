#!/usr/bin/env python3
"""Create one isolated run evidence bundle bound to a frozen experimental condition."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
EVAL = ROOT / "harness" / "evals" / "compute-authority"
FIX = EVAL / "fixtures"
SCRIPTS = EVAL / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from conditions import DEFAULT_GENERATION, GENERATIONS, normalize_generation, resolve  # noqa: E402
from reset_fixture import reset_case, workspace_hash  # noqa: E402

VALID_CASES = {f"TC{i:02d}" for i in range(1, 9)}
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def validate_run_id(run_id: str) -> str:
    """Return a safe single-path-component run identifier."""
    if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
        raise ValueError(
            "run_id must be 1..128 chars, start alphanumeric, and contain only "
            "ASCII letters, digits, dot, underscore, or hyphen"
        )
    if run_id in {".", ".."}:
        raise ValueError("run_id must not be a path traversal component")
    return run_id


def fixture_sha(case_id: str) -> str:
    return workspace_hash(FIX / case_id / "workspace")


def repository_sha() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _file_manifest(root: Path) -> dict[str, str]:
    manifest: dict[str, str] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        manifest[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return manifest


def _write_hash_manifest(path: Path, manifest: dict[str, str]) -> None:
    lines = [f"{digest}  {rel}" for rel, digest in sorted(manifest.items())]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def materialize_workspace_evidence(run_dir: Path) -> list[str]:
    """Persist privacy-bounded pre/post workspace identity and changed-path evidence.

    The evaluator needs only structural path evidence for scope grading. File contents
    are never copied into the evidence bundle.
    """
    run_meta = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    starting = json.loads((run_dir / "starting-state.json").read_text(encoding="utf-8"))
    case_id = str(run_meta.get("test_case") or "").upper()
    if case_id not in VALID_CASES:
        raise ValueError(f"invalid test_case in run metadata: {case_id!r}")

    pristine = FIX / case_id / "workspace"
    workspace = run_dir / "workspace"
    if not pristine.is_dir() or not workspace.is_dir():
        raise FileNotFoundError("missing pristine or run workspace")

    expected_fixture_sha = str(starting.get("fixture_sha") or "")
    current_fixture_sha = fixture_sha(case_id)
    if not expected_fixture_sha or current_fixture_sha != expected_fixture_sha:
        raise RuntimeError(
            "pristine fixture changed after run initialization; scope evidence is stale"
        )

    before = _file_manifest(pristine)
    after = _file_manifest(workspace)
    _write_hash_manifest(run_dir / "git-before.txt", before)
    _write_hash_manifest(run_dir / "git-after.txt", after)

    changed = sorted(
        rel for rel in set(before) | set(after) if before.get(rel) != after.get(rel)
    )
    patch_lines: list[str] = []
    for rel in changed:
        patch_lines.append(f"diff --git a/{rel} b/{rel}")
        patch_lines.append(f"--- {'a/' + rel if rel in before else '/dev/null'}")
        patch_lines.append(f"+++ {'b/' + rel if rel in after else '/dev/null'}")
    (run_dir / "diff.patch").write_text(
        "\n".join(patch_lines) + ("\n" if patch_lines else ""),
        encoding="utf-8",
    )
    return changed


def initialize_run(
    *,
    case_id: str,
    condition: str,
    repetition: int = 1,
    run_id: str | None = None,
    agent: str = "",
    model: str = "",
    generation: str = DEFAULT_GENERATION,
) -> Path:
    case_id = case_id.upper()
    if case_id not in VALID_CASES:
        raise ValueError(f"invalid case: {case_id}")
    if repetition < 1:
        raise ValueError("repetition must be >= 1")
    generation = normalize_generation(generation)
    frozen = resolve(condition, generation)
    run_id = validate_run_id(run_id or f"{case_id}-{condition}-r{repetition}")
    run_dir = EVAL / "runs" / run_id
    if run_dir.exists():
        raise FileExistsError(f"run dir already exists: {run_dir}")
    run_dir.mkdir(parents=True)

    prompt_src = ROOT / frozen["prompt_path"]
    shutil.copy2(prompt_src, run_dir / f"prompt-{condition}.txt")
    shutil.copy2(FIX / case_id / "task.txt", run_dir / "task.txt")
    reset_case(case_id, run_id=run_id)

    env: dict[str, Any] = {"worker_capacity": 0}
    env_path = FIX / case_id / "environment.json"
    if env_path.is_file():
        env = json.loads(env_path.read_text(encoding="utf-8"))
    (run_dir / "environment.json").write_text(
        json.dumps(env, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    starting = {
        "case": case_id,
        "fixture_sha": fixture_sha(case_id),
        "workspace_relpath": "workspace",
        "condition_sha": frozen["prompt_contract_sha"],
    }
    (run_dir / "starting-state.json").write_text(
        json.dumps(starting, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (run_dir / "condition.json").write_text(
        json.dumps(frozen, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    for name in (
        "transcript.jsonl",
        "tool-events.jsonl",
        "git-before.txt",
        "git-after.txt",
        "diff.patch",
        "closeout.txt",
    ):
        (run_dir / name).write_text("", encoding="utf-8")
    (run_dir / "validation-results.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "contracts.json").write_text(
        json.dumps({"contracts": []}, indent=2) + "\n", encoding="utf-8"
    )
    (run_dir / "metrics.json").write_text("{}\n", encoding="utf-8")
    (run_dir / "evaluator-score.json").write_text("{}\n", encoding="utf-8")
    run_meta = {
        "run_id": run_id,
        "test_case": case_id,
        "condition": condition,
        "generation": generation,
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
    (run_dir / "run.json").write_text(
        json.dumps(run_meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return run_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--condition", required=True, choices=["control", "treatment"])
    parser.add_argument("--generation", choices=sorted(GENERATIONS), default=DEFAULT_GENERATION)
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
        generation=args.generation,
    )
    print(run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
