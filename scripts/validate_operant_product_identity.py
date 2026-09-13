#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import operant_version

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "harness/contracts/operant-product-identity.v1.json"
PRODUCT_NAME = "AFK Agent Flow"
PRODUCT_ID = "afk-agent-flow"
PUBLIC_ROUTE = "/afk-agent-flow/"
TARGET_REPOSITORY = "UnderDeskDev/AFK-Agent-Flow"


def evaluate() -> list[str]:
    findings: list[str] = []
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    try:
        version = str(operant_version.current_version())
    except operant_version.VersioningError as exc:
        return [str(exc)]

    expected = {
        "schema_version": "operant-product-identity/v1",
        "product_id": PRODUCT_ID,
        "product_name": PRODUCT_NAME,
        "product_version": version,
        "status": "transition",
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            findings.append(f"{key} drifted: {payload.get(key)!r}")

    public_identity = payload.get("public_identity", {})
    if public_identity.get("slug") != PRODUCT_ID:
        findings.append("public slug drifted")
    if not str(public_identity.get("canonical_url", "")).endswith(PUBLIC_ROUTE):
        findings.append("canonical public URL drifted")
    if "Away From Keyboard" not in str(public_identity.get("public_expansion", "")):
        findings.append("public AFK expansion is missing")
    if "Failure must not silently become accepted state" not in str(
        public_identity.get("reliability_claim", "")
    ):
        findings.append("bounded unattended-execution reliability claim is missing")

    legacy_names = payload.get("legacy_identity", {}).get("names", [])
    for legacy_name in ("Operant", "AI Harness Prompt Kit", "Prompt Kit"):
        if legacy_name not in legacy_names:
            findings.append(f"legacy product alias missing: {legacy_name}")

    authority = payload.get("authority", {})
    if authority.get("current_repository") != "EndeavorEverlasting/web-excel-repair-triage":
        findings.append("current repository authority drifted")
    if authority.get("target_repository") != TARGET_REPOSITORY:
        findings.append("target repository drifted")
    if authority.get("target_repository_state") != "not-created-or-unproven":
        findings.append("target repository state was promoted without proof")

    compatibility = payload.get("compatibility", {})
    if compatibility.get("visible_brand") != PRODUCT_NAME:
        findings.append("visible product brand drifted")
    if compatibility.get("visible_version") != version:
        findings.append("visible version mirror drifted from OPERANT_VERSION")
    if compatibility.get("canonical_public_route") != PUBLIC_ROUTE:
        findings.append("canonical public route drifted")
    if set(compatibility.get("legacy_public_routes", [])) != {"/operant/", "/prompt-kit/"}:
        findings.append("legacy public route set drifted")
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
    for scope in ("afk-agent-flow", "operant", "prompt-kit"):
        if scope not in release_policy.get("shared_scopes", []):
            findings.append(f"release scope compatibility missing: {scope}")

    bootstrap = release_policy.get("bootstrap", {})
    if bootstrap.get("identity_merge_sha") != "781616a1a42893fb5b521e41b217f5cef04b2701":
        findings.append("Operant 0.1 bootstrap identity drifted")
    if release_policy.get("pre_1_policy", {}).get("promotion_to_1_0") is None:
        findings.append("explicit 1.0 promotion gate is missing")

    governance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for marker in (
        "**AFK Agent Flow**",
        "`UnderDeskDev/AFK-Agent-Flow`",
        "Operant",
        "Prompt Kit",
        "must not be silently moved",
    ):
        if marker not in governance:
            findings.append(f"governance marker missing: {marker}")

    html = (ROOT / "web/prompt-kit/index.html").read_text(encoding="utf-8")
    for marker in (
        f"<title>{PRODUCT_NAME} {version}</title>",
        f"{PRODUCT_NAME} <span>{version}</span>",
        f'id="versionBadge">{version}</div>',
        "Capabilities · Skills · Implementations · Evidence",
    ):
        if marker not in html:
            findings.append(f"generated AFK Agent Flow marker missing: {marker}")
    for stale_title in (
        f"<title>Operant {version}</title>",
        "<title>AI Harness Prompt Kit v40</title>",
    ):
        if stale_title in html:
            findings.append(f"legacy title remains the visible product identity: {stale_title}")

    for finding in operant_version.validate():
        if finding not in findings:
            findings.append(finding)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the AFK Agent Flow public identity over legacy Operant release seams."
    )
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    findings = evaluate()
    if findings:
        if args.summary:
            print("AFK_AGENT_FLOW_IDENTITY_FAIL")
            for finding in findings:
                print(f"- {finding}")
        return 1
    if args.summary:
        print(
            f"AFK_AGENT_FLOW_IDENTITY_PASS product={PRODUCT_NAME} "
            f"version={operant_version.current_version()} target={TARGET_REPOSITORY} state=transition"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
