#!/usr/bin/env python3
"""Freeze Control/Treatment Prompt Kit contract snapshots for the eval harness."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "harness" / "evals" / "compute-authority"
CONTROL_COMMIT = "49951e238bd47e536b40815552ceb32a1aac7815"  # parent of a583b333


def policy_at(commit: str | None) -> dict:
    if commit is None:
        path = ROOT / "registry/prompts/actionable-next-step-policy.v1.json"
        return json.loads(path.read_text(encoding="utf-8"))
    text = subprocess.check_output(
        ["git", "show", f"{commit}:registry/prompts/actionable-next-step-policy.v1.json"],
        cwd=ROOT,
        text=True,
    )
    return json.loads(text)


def snapshot(policy: dict, label: str, commit: str) -> dict:
    body = (
        "# Prompt Kit shared execution contract snapshot\n"
        f"# condition: {label}\n"
        f"# source_commit: {commit}\n"
        f"# policy_id: {policy['policy_id']}\n"
        f"# schema_version: {policy['schema_version']}\n\n"
        "## next_step_suffix\n"
        f"{policy['next_step_suffix']}\n\n"
        "## copy_content_appendix\n"
        f"{policy['copy_content_appendix']}\n"
    )
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    path = OUT / "prompts" / f"prompt-{label}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8", newline="\n")
    return {
        "condition": label,
        "source_commit": commit,
        "prompt_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "prompt_contract_sha": digest,
        "markers": {
            "compute_authority": "COMPUTE AUTHORITY / SCOPE-BOUNDARY CONTRACT" in body,
            "exhaustive_compute": "EXHAUSTIVE AVAILABLE COMPUTE RULE" in body,
            "end_state_horizon": "END-STATE CONTRACT HORIZON" in body,
        },
    }


def main() -> int:
    for name in ("prompts", "fixtures", "runs", "aggregate", "templates", "scripts"):
        (OUT / name).mkdir(parents=True, exist_ok=True)

    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    control = snapshot(policy_at(CONTROL_COMMIT), "control", CONTROL_COMMIT)
    treatment = snapshot(policy_at(None), "treatment", head)
    if control["markers"]["compute_authority"] or control["markers"]["exhaustive_compute"]:
        raise SystemExit("control snapshot unexpectedly contains compute-authority markers")
    if not (
        treatment["markers"]["compute_authority"]
        and treatment["markers"]["exhaustive_compute"]
        and treatment["markers"]["end_state_horizon"]
    ):
        raise SystemExit("treatment snapshot missing required compute-authority markers")

    ident = {
        "schema_version": "compute-authority-prompt-identities/v1",
        "control": control,
        "treatment": treatment,
        "freeze_note": (
            "Treatment is the current strengthened actionable-next-step policy. "
            "Control is the same policy immediately before a583b333 "
            "(compute authority + contract horizon expansion). "
            "Exhaustive-compute wording landed later in 2f258b09 and is included in treatment only."
        ),
    }
    (OUT / "prompts" / "identities.json").write_text(
        json.dumps(ident, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(ident, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
