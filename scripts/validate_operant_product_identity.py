#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import operant_version

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness/contracts/operant-product-identity.v1.json"


def evaluate() -> list[str]:
    findings: list[str] = []
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    try:
        version = str(operant_version.current_version())
    except operant_version.VersioningError as exc:
        return [str(exc)]

    expected = {
        "schema_version": "operant-product-identity/v1",
        "product_id": "operant",
        "product_name": "Operant",
        "product_version": version,
        "status": "transition",
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            findings.append(f"{key} drifted: {payload.get(key)!r}")

    authority = payload.get("authority", {})
    if authority.get("current_repository") != "EndeavorEverlasting/web-excel-repair-triage":
        findings.append("current repository authority drifted")
    if authority.get("target_repository") != "UnderDeskDev/Operant":
        findings.append("target repository drifted")
    if authority.get("target_repository_state") != "not-created-or-unproven":
        findings.append("target repository state was promoted without proof")

    compatibility = payload.get("compatibility", {})
    if compatibility.get("visible_version") != version:
        findings.append("visible version mirror drifted from OPERANT_VERSION")
    if compatibility.get("internal_path_renames_deferred") is not True:
        findings.append("legacy compatibility-path preservation was disabled")
    for relative in compatibility.get("preserve_paths", []):
        if "*" not in relative and not (ROOT / relative).exists():
            findings.append(f"compatibility path missing: {relative}")

    release_policy = payload.get("release_versioning", {})
    required_release_policy = {
        "schema_version": "operant-release-versioning/v1",
        "authority_file": "OPERANT_VERSION",
        "scheme": "semver",
        "tag_prefix": "operant-v",
        "changelog": "docs/OPERANT_CHANGELOG.md",
    }
    for key, value in required_release_policy.items():
        if release_policy.get(key) != value:
            findings.append(f"release version policy {key} drifted: {release_policy.get(key)!r}")

    bootstrap = release_policy.get("bootstrap", {})
    if bootstrap.get("identity_merge_sha") != "781616a1a42893fb5b521e41b217f5cef04b2701":
        findings.append("Operant 0.1 bootstrap identity drifted")
    if release_policy.get("pre_1_policy", {}).get("promotion_to_1_0") is None:
        findings.append("explicit 1.0 promotion gate is missing")

    governance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for marker in (
        "**Operant** is the operator-approved product identity",
        "`UnderDeskDev/Operant`",
        "must not be silently moved",
        "must not become a competing Operant authority",
    ):
        if marker not in governance:
            findings.append(f"governance marker missing: {marker}")

    html = (ROOT / "web/prompt-kit/index.html").read_text(encoding="utf-8")
    for marker in (
        f"<title>Operant {version}</title>",
        f"Operant <span>{version}</span>",
        f'id="versionBadge">{version}</div>',
        "Capabilities · Skills · Implementations · Evidence",
    ):
        if marker not in html:
            findings.append(f"generated Operant marker missing: {marker}")
    if "<title>AI Harness Prompt Kit v40</title>" in html:
        findings.append("legacy v40 title remains the visible product identity")

    for finding in operant_version.validate():
        if finding not in findings:
            findings.append(finding)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Operant product identity and version authority.")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    findings = evaluate()
    if findings:
        if args.summary:
            print("OPERANT_IDENTITY_FAIL")
            for finding in findings:
                print(f"- {finding}")
        return 1
    if args.summary:
        print(
            f"OPERANT_IDENTITY_PASS product=Operant version={operant_version.current_version()} "
            "target=UnderDeskDev/Operant state=transition"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
