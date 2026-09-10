#!/usr/bin/env python3
"""Run one repository-owned promotion validation gate and emit a candidate-bound receipt."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "harness" / "promotion" / "required-checks.v1.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def run_command(command: str, *, base_sha: str, head_sha: str) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{40}", base_sha) or not re.fullmatch(r"[0-9a-f]{40}", head_sha):
        raise RuntimeError("promotion gate requires exact lowercase 40-hex candidate identities")
    resolved = command.format(base_sha=base_sha, head_sha=head_sha)
    result = subprocess.run(resolved, cwd=ROOT, shell=True, text=True)
    return {"command": resolved, "returncode": result.returncode}


def event_candidate(event_path: Path) -> dict[str, Any]:
    payload = load_json(event_path)
    pr = payload.get("pull_request")
    if not isinstance(pr, dict):
        raise RuntimeError("promotion candidate validation requires a pull_request event")
    return {
        "pr_number": int(pr["number"]),
        "head_sha": str(pr["head"]["sha"]),
        "base_sha": str(pr["base"]["sha"]),
        "base_ref": str(pr["base"]["ref"]),
        "head_ref": str(pr["head"]["ref"]),
        "repository": str(payload["repository"]["full_name"]),
    }


def changed_paths(base_sha: str, head_sha: str) -> list[str]:
    output = git("diff", "--name-only", f"{base_sha}...{head_sha}")
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", choices=["harness-e2e", "application-e2e", "candidate"], required=True)
    parser.add_argument("--event-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    policy = load_json(POLICY_PATH)
    main_policy = policy["destinations"]["main"]
    candidate = event_candidate(args.event_path)
    actual_head = git("rev-parse", "HEAD")
    if actual_head != candidate["head_sha"]:
        print(f"Promotion gate blocked: checkout HEAD {actual_head} != event head {candidate['head_sha']}", file=sys.stderr)
        return 1
    paths = changed_paths(candidate["base_sha"], candidate["head_sha"])
    unexpected = sorted(set(paths) - set(main_policy["allowed_change_paths"]))
    receipt: dict[str, Any] = {
        "schema_version": "repository-promotion-validation-receipt/v1",
        "gate": args.gate,
        "status": "UNKNOWN",
        "repository": candidate["repository"],
        "pr_number": candidate["pr_number"],
        "candidate_head_sha": candidate["head_sha"],
        "candidate_base_sha": candidate["base_sha"],
        "base_ref": candidate["base_ref"],
        "head_ref": candidate["head_ref"],
        "policy_version": policy["policy_version"],
        "changed_paths": paths,
        "commands": [],
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proof_ceiling": "",
    }

    if unexpected:
        receipt["status"] = "ENVIRONMENT_BLOCKED"
        receipt["reason"] = "No application-E2E profile is registered for changed paths: " + ", ".join(unexpected)
        receipt["proof_ceiling"] = "No promotion proof; v1 auto-promotion scope is intentionally bounded."
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(receipt["reason"], file=sys.stderr)
        return 1

    if args.gate == "application-e2e":
        receipt["status"] = "INAPPLICABLE"
        receipt["reason"] = main_policy["application_e2e"]["reason"]
        receipt["proof_ceiling"] = "Application E2E is inapplicable only for the bounded sanitized promotion canary path."
    else:
        commands = main_policy["harness_e2e_commands"] if args.gate == "harness-e2e" else main_policy["exact_candidate_commands"]
        for command in commands:
            result = run_command(command, base_sha=candidate["base_sha"], head_sha=candidate["head_sha"])
            receipt["commands"].append(result)
            if result["returncode"] != 0:
                receipt["status"] = "FAIL"
                receipt["reason"] = f"command failed: {result['command']}"
                receipt["proof_ceiling"] = "Promotion blocked at repository validation."
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
                return result["returncode"] or 1
        receipt["status"] = "PASS"
        receipt["proof_ceiling"] = (
            "Harness E2E proves repository promotion contracts and harness integration on the exact candidate."
            if args.gate == "harness-e2e"
            else "Exact-candidate gate proves checkout identity, bounded path scope, policy integrity, and patch hygiene."
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Promotion gate {args.gate}: {receipt['status']} head={candidate['head_sha']} base={candidate['base_sha']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
