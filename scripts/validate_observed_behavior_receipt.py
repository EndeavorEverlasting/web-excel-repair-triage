#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_RANK = {
    "source": 0,
    "build": 1,
    "synthetic": 1,
    "browser_runtime_observed": 2,
    "target_runtime_observed": 3,
    "production_observed": 4,
}


def validate(receipt: dict, expected_sha: str | None = None) -> list[str]:
    errors: list[str] = []
    if receipt.get("schema_version") != "observed-behavior-proof/v1":
        errors.append("unsupported schema_version")
    subject = receipt.get("subject") or {}
    sha = str(subject.get("commit_sha") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        errors.append("subject.commit_sha must be an exact 40-character SHA")
    if expected_sha and sha != expected_sha:
        errors.append(f"receipt SHA {sha} does not match expected {expected_sha}")
    artifact = subject.get("artifact") or {}
    rel = artifact.get("path")
    digest = str(artifact.get("sha256") or "")
    if not rel or not re.fullmatch(r"[0-9a-f]{64}", digest):
        errors.append("subject.artifact path and sha256 are required")
    else:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"artifact does not exist: {rel}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append("artifact hash does not match current file")
    evidence_class = receipt.get("evidence_class")
    if evidence_class not in EVIDENCE_RANK:
        errors.append("unknown evidence_class")
    observations = {
        item.get("id"): item
        for item in receipt.get("observations", [])
        if isinstance(item, dict) and item.get("id")
    }
    claims = receipt.get("claims", [])
    if not claims:
        errors.append("receipt must contain claims")
    for claim in claims:
        cid = claim.get("id", "<missing>")
        status = claim.get("status")
        required = claim.get("required_evidence_class")
        refs = claim.get("observation_ids") or []
        if status == "PASS":
            if required not in EVIDENCE_RANK:
                errors.append(f"{cid}: unknown required_evidence_class {required}")
            elif evidence_class in EVIDENCE_RANK and EVIDENCE_RANK[evidence_class] < EVIDENCE_RANK[required]:
                errors.append(f"{cid}: PASS requires {required}, got weaker {evidence_class}")
            if not refs:
                errors.append(f"{cid}: PASS has no observation_ids")
            for ref in refs:
                observation = observations.get(ref)
                if not observation:
                    errors.append(f"{cid}: missing observation {ref}")
                    continue
                if observation.get("occurred") is not True:
                    errors.append(f"{cid}: observation {ref} did not occur")
                if observation.get("passed") is not True:
                    errors.append(f"{cid}: observation {ref} did not pass")
        elif status not in {"UNKNOWN", "UNPROVEN", "FAIL"}:
            errors.append(f"{cid}: invalid status {status}")
    verdict = receipt.get("verdict")
    if verdict != "PASS":
        errors.append(f"receipt verdict is {verdict}, not PASS")
    elif any(c.get("status") != "PASS" for c in claims):
        errors.append("overall PASS requires every claim to PASS")
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt")
    parser.add_argument("--expected-sha")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    errors = validate(receipt, args.expected_sha)
    if errors:
        print("Observed behavior proof: FAIL", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Observed behavior proof: PASS" if args.summary else json.dumps({"verdict": "PASS", "receipt": args.receipt}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
