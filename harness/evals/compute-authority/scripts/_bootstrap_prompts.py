#!/usr/bin/env python3
"""Freeze Control/Treatment Prompt Kit contract snapshots for the eval harness.

Each generation pins its treatment commit deterministically so any generation is
reproducible from any checkout. Generation ``v1`` remains the default and its
tracked snapshots are byte-for-byte stable; ``v2`` writes sibling artifacts under
``prompts/gen2/`` and never mutates ``v1`` files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "harness" / "evals" / "compute-authority"
CONTROL_COMMIT = "49951e238bd47e536b40815552ceb32a1aac7815"  # parent of a583b333

DEFAULT_GENERATION = "v1"
GENERATIONS = {
    "v1": {
        "treatment_commit": "741fc565ecc1772d2fcfce43e8c2d071b9d35d81",
        "prompts_subdir": "",
        "freeze_note": (
            "Treatment is the current strengthened actionable-next-step policy. "
            "Control is the same policy immediately before a583b333 "
            "(compute authority + contract horizon expansion). "
            "Exhaustive-compute wording landed later in 2f258b09 and is included in treatment only."
        ),
    },
    "v2": {
        "treatment_commit": "fc9437ff3fa83ce9df82c6ad85a79d09d7e0bd17",
        "prompts_subdir": "gen2",
        "control_from_generation": "v1",
        "freeze_note": (
            "Treatment is the released Operant v0.9.0 shared execution policy at "
            "fc9437ff3fa83ce9df82c6ad85a79d09d7e0bd17. Control is preserved byte-for-byte from "
            "generation v1 (the policy immediately before a583b333) so the longitudinal baseline "
            "comparison stays valid; control is not re-baselined."
        ),
    },
}


def policy_at(commit: str | None) -> dict:
    if commit is None:
        path = ROOT / "registry/prompts/actionable-next-step-policy.v1.json"
        return json.loads(path.read_text(encoding="utf-8"))
    text = subprocess.check_output(
        ["git", "show", f"{commit}:registry/prompts/actionable-next-step-policy.v1.json"],
        cwd=ROOT,
        encoding="utf-8",
    )
    return json.loads(text)


def _prompts_dir(subdir: str) -> Path:
    return OUT / "prompts" / subdir if subdir else OUT / "prompts"


def copy_control(src_generation: str, dest_subdir: str) -> dict:
    """Copy a preserved control snapshot from another generation byte-for-byte.

    The control condition is defined as the same pre-``a583b333`` baseline across
    generations, so a fresh generation reuses the exact frozen control bytes
    (including any historical encoding) rather than re-rendering it. This keeps the
    longitudinal control identical and its contract hash stable.
    """
    src_subdir = GENERATIONS[src_generation]["prompts_subdir"]
    src_ident = json.loads((_prompts_dir(src_subdir) / "identities.json").read_text(encoding="utf-8"))
    src_control = src_ident["control"]
    dest_dir = _prompts_dir(dest_subdir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / "prompt-control.txt"
    shutil.copyfile(_prompts_dir(src_subdir) / "prompt-control.txt", dest_path)
    return {
        "condition": "control",
        "source_commit": src_control["source_commit"],
        "prompt_path": str(dest_path.relative_to(ROOT)).replace("\\", "/"),
        "prompt_contract_sha": src_control["prompt_contract_sha"],
        "markers": src_control["markers"],
    }


def snapshot(policy: dict, label: str, commit: str, subdir: str = "") -> dict:
    body = (
        "# Prompt Kit shared execution contract snapshot\n"
        f"# condition: {label}\n"
        f"# source_commit: {commit}\n"
        f"# policy_id: {policy['policy_id']}\n"
        f"# schema_version: {policy['schema_version']}\n\n"
        "## next_step_suffix\n"
        f"{policy['next_step_suffix']}\n\n"
        "## copy_content_appendix\n"
        f"{policy['copy_content_appendix'].rstrip(chr(10))}\n"
    )
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    path = _prompts_dir(subdir) / f"prompt-{label}.txt"
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


def build_generation(generation: str) -> dict:
    spec = GENERATIONS[generation]
    subdir = spec["prompts_subdir"]
    inherit = spec.get("control_from_generation")
    if inherit:
        control = copy_control(inherit, subdir)
    else:
        control = snapshot(policy_at(CONTROL_COMMIT), "control", CONTROL_COMMIT, subdir)
    treatment = snapshot(policy_at(spec["treatment_commit"]), "treatment", spec["treatment_commit"], subdir)
    if control["markers"]["compute_authority"] or control["markers"]["exhaustive_compute"]:
        raise SystemExit("control snapshot unexpectedly contains compute-authority markers")
    if not (
        treatment["markers"]["compute_authority"]
        and treatment["markers"]["exhaustive_compute"]
        and treatment["markers"]["end_state_horizon"]
    ):
        raise SystemExit("treatment snapshot missing required compute-authority markers")

    ident: dict = {"schema_version": "compute-authority-prompt-identities/v1"}
    if generation != DEFAULT_GENERATION:
        ident["generation"] = generation
    ident["control"] = control
    ident["treatment"] = treatment
    ident["freeze_note"] = spec["freeze_note"]
    (_prompts_dir(subdir) / "identities.json").write_text(
        json.dumps(ident, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    return ident


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation", choices=sorted(GENERATIONS), default=DEFAULT_GENERATION)
    args = parser.parse_args(argv)

    for name in ("prompts", "fixtures", "runs", "aggregate", "templates", "scripts"):
        (OUT / name).mkdir(parents=True, exist_ok=True)

    ident = build_generation(args.generation)
    print(json.dumps(ident, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
