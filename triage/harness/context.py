"""triage/harness/context.py
---------------------------
Run-context creation, serialization, and persistence.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import secrets
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from triage.path_policy import repo_root


def _generate_run_id() -> str:
    return secrets.token_hex(4)


def _git_branch() -> str:
    try:
        r = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, check=True, cwd=str(repo_root()),
        )
        return r.stdout.strip() or "detached"
    except Exception:
        return "unknown"


def _git_sha() -> str:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, cwd=str(repo_root()),
        )
        return r.stdout.strip()[:40]
    except Exception:
        return "unknown"


def _git_dirty() -> bool:
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, check=True, cwd=str(repo_root()),
        )
        return bool(r.stdout.strip())
    except Exception:
        return False


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_input_hashes(input_paths: List[str]) -> Dict[str, str]:
    root = repo_root()
    hashes: Dict[str, str] = {}
    for p in input_paths:
        full = root / p
        if full.is_file():
            hashes[p] = _hash_file(full)
    return hashes


PROOF_LEVELS = [
    "contract",
    "harness",
    "static_test",
    "build",
    "package",
    "render",
    "launcher",
    "command_ack",
    "behavior_observed",
    "browser",
    "live_runtime",
    "operator_acceptance",
]

PROOF_RANK = {level: i for i, level in enumerate(PROOF_LEVELS)}


def proof_level_gte(a: str, b: str) -> bool:
    """True if proof level a >= proof level b."""
    return PROOF_RANK.get(a, -1) >= PROOF_RANK.get(b, -1)


def allocate_run_dir(run_id: str) -> Path:
    """Create and return the run output directory under Outputs/runs/<run_id>/."""
    out = repo_root() / "Outputs" / "runs" / run_id
    out.mkdir(parents=True, exist_ok=True)
    return out


def create_run_context(
    workflow_id: str,
    input_paths: List[str],
    requested_proof_level: str = "build",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a new run-context dict, create the run directory, and persist it."""
    if requested_proof_level not in PROOF_RANK:
        raise ValueError(f"Unknown proof level: {requested_proof_level!r}")

    run_id = _generate_run_id()
    run_dir = allocate_run_dir(run_id)
    input_hashes = compute_input_hashes(input_paths)

    ctx: Dict[str, Any] = {
        "run_id": run_id,
        "workflow_id": workflow_id,
        "started_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "completed_at": None,
        "branch": _git_branch(),
        "commit_sha": _git_sha(),
        "dirty": _git_dirty(),
        "input_paths": input_paths,
        "input_hashes": input_hashes,
        "output_dir": f"Outputs/runs/{run_id}",
        "requested_proof_level": requested_proof_level,
        "achieved_proof_level": "contract",
        "skipped_gates": [],
        "metadata": metadata or {},
    }

    ctx_path = run_dir / "run-context.json"
    ctx_path.write_text(json.dumps(ctx, indent=2, default=str), encoding="utf-8")
    return ctx


def complete_run_context(ctx: Dict[str, Any], achieved_proof: str) -> Dict[str, Any]:
    """Mark the run as completed and persist updated context."""
    ctx["completed_at"] = _dt.datetime.now(_dt.timezone.utc).isoformat()
    ctx["achieved_proof_level"] = achieved_proof
    out = repo_root() / ctx["output_dir"]
    ctx_path = out / "run-context.json"
    ctx_path.write_text(json.dumps(ctx, indent=2, default=str), encoding="utf-8")
    return ctx


def load_run_context(run_id: str) -> Optional[Dict[str, Any]]:
    ctx_path = repo_root() / "Outputs" / "runs" / run_id / "run-context.json"
    if not ctx_path.exists():
        return None
    return json.loads(ctx_path.read_text(encoding="utf-8"))
